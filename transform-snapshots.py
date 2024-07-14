import argparse
import bz2
import ipaddress
import json
import logging
import os
import pickle
import subprocess as sp
import sys
from datetime import timedelta
from multiprocessing import Pool
from shutil import which
from socket import AF_INET
from typing import Tuple

import radix

from helpers.defines import FOLDER_FORMAT, RIB_FILE_FORMATS, TIMESTAMP_FORMAT_ESCAPED
from helpers.shared_functions import get_candidate_file, parse_timestamp_argument, sanitize_dir

OUTPUT_FILE_SUFFIX = '.pickle.bz2'


def transform_rib(fixture: Tuple[str, str]) -> dict:
    input_file, output_file = fixture
    logging.info(f'Processing {input_file}')
    rtree = radix.Radix()

    stats = {'file': input_file,
             'peers': set(),
             'entries': 0,
             'origin_sets': 0,
             'v4_pfxs': 0,
             'v6_pfxs': 0,
             'ignored_v4_pfxs': 0,
             'ignored_v6_pfxs': 0}

    # Output format:
    #   type|timestamp|peer_ip|peer_asn|prefix|as_path|origin_asns|origin|
    #   next_hop|local_pref|med|communities|atomic|aggr_asn|aggr_ip|only_to_customer
    p = sp.Popen(['bgpkit-parser', input_file], stdout=sp.PIPE, text=True, bufsize=1)

    for line in p.stdout:
        res = line.split('|')
        peer_ip = res[2]
        prefix = res[4]

        if peer_ip not in stats['peers']:
            stats['peers'].add(peer_ip)

        try:
            prefix_parsed = ipaddress.ip_network(prefix)
        except ValueError as e:
            logging.error(f'Invalid prefix ({prefix}): {e}')
            continue

        if not prefix_parsed.is_global:
            logging.debug(f'Ignoring non-global prefix: {prefix}')
            continue

        stats['entries'] += 1

        as_path = res[5]
        origin_asn = as_path.split(' ')[-1]
        if ',' in origin_asn:
            # Do not include "Origin AS Sets"
            stats['origin_sets'] += 1
            continue
        # There are sometimes singleton sets of the form {ASXXX},
        # which we should be able to use, just strip the parenthesis.
        origin_asn = origin_asn.strip('{}')

        node = rtree.add(prefix)
        if 'as' in node.data:
            if origin_asn not in node.data['as']:
                logging.debug(f'{prefix}: {node.data["as"]} += {origin_asn}')
                if peer_ip in node.data['peers']:
                    logging.error(f'Peer {peer_ip} reported different origins for {prefix}: {node.data["as"]} '
                                  f'{origin_asn}')
                node.data['as'].add(origin_asn)
                node.data['peers'].append(peer_ip)
        else:
            node.data['as'] = {origin_asn}
            node.data['peers'] = list(peer_ip)

    # Do not create an output file for an empty RIB.
    if not rtree.nodes():
        logging.warning(f'Did not create empty file: {output_file}')
        return stats

    # Remove AS sets caused by differing information from peers.
    for node in rtree.nodes():
        is_v4 = node.family == AF_INET
        if is_v4:
            stats['v4_pfxs'] += 1
        else:
            stats['v6_pfxs'] += 1
        asn_set = node.data['as']
        if len(asn_set) == 1:
            node.data['as'] = asn_set.pop()
            node.data.pop('peers')
        else:
            if is_v4:
                stats['ignored_v4_pfxs'] += 1
            else:
                stats['ignored_v6_pfxs'] += 1
            rtree.delete(node.prefix)

    stats['peers'] = len(stats['peers'])

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with bz2.open(output_file, 'wb') as f:
        pickle.dump(rtree, f)

    return stats


def print_stats(stats: list) -> None:
    for stat in sorted(stats, key=lambda d: d['file']):
        v4_pfxs = stat['v4_pfxs']
        ignored_v4_pfxs = stat['ignored_v4_pfxs']
        ignored_v4_pfxs_pct = 0
        if v4_pfxs > 0:
            ignored_v4_pfxs_pct = ignored_v4_pfxs / v4_pfxs * 100
        final_v4_pfxs = v4_pfxs - ignored_v4_pfxs
        v6_pfxs = stat['v6_pfxs']
        ignored_v6_pfxs = stat['ignored_v6_pfxs']
        ignored_v6_pfxs_pct = 0
        if v6_pfxs > 0:
            ignored_v6_pfxs_pct = ignored_v6_pfxs / v6_pfxs * 100
        final_v6_pfxs = v6_pfxs - ignored_v6_pfxs
    # autopep8: off
        logging.info(f'{stat["file"]} | peers:{stat["peers"]} entries:{stat["entries"]} origin_sets:{stat["origin_sets"]} v4_pfxs:{v4_pfxs} v4_ignored:{ignored_v4_pfxs} ({ignored_v4_pfxs_pct:.2f}%) v4_final:{final_v4_pfxs} v6_pfxs:{v6_pfxs} v6_ignored:{ignored_v6_pfxs} ({ignored_v6_pfxs_pct:.2f}%) v6_final:{final_v6_pfxs}')
    # autopep8: on


def main() -> None:
    desc = """Transform RIB files into radix trees.

    Transform the files closest to the specified timestamp. If no file matching the
    exact timestamp is found, transform the next-closest file up to a difference of 24
    hours, which can be adjust with the --max-timestamp-difference parameter.

    Ignore prefixes with origin AS sets from the RIB, but also origin AS sets that would be created
    due to peers disagreeing on the origin AS for a prefix.
    """
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('index')
    parser.add_argument('timestamp', help=f'UTC timestamp in {TIMESTAMP_FORMAT_ESCAPED} format')
    parser.add_argument('--max-timestamp-difference',
                        type=int,
                        default=24,
                        help='max allowed difference (in h) from timestamp')
    parser.add_argument('-i', '--input-dir',
                        default='data/',
                        help='change default input directory')
    parser.add_argument('-o', '--output-dir',
                        default='transformed/',
                        help='change default output directory')
    parser.add_argument('-n', '--num-workers',
                        type=int,
                        default=4,
                        help='number of parallel workers')
    parser.add_argument('-f', '--force',
                        action='store_true',
                        help='overwrite existing files')
    args = parser.parse_args()

    FORMAT = '%(asctime)s %(levelname)s %(message)s'
    logging.basicConfig(
        format=FORMAT,
        handlers=[
            logging.FileHandler('transform-snapshots.log'),
            logging.StreamHandler(sys.stdout)
        ],
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logging.info(f'Started {sys.argv}')

    if not which('bgpkit-parser'):
        logging.error('Failed to find bgpkit-parser executable. Is it installed?')
        sys.exit(1)

    timestamp = parse_timestamp_argument(args.timestamp)
    if timestamp is None:
        logging.error('Invalid timestamp specified')
        sys.exit(1)

    index_file = args.index
    with open(index_file, 'r') as f:
        index = json.load(f)

    input_dir = sanitize_dir(args.input_dir)
    output_dir = sanitize_dir(args.output_dir)
    max_timestamp_difference = timedelta(hours=args.max_timestamp_difference)

    fixtures = list()
    skipped_files = 0
    for source, collectors in index['sources'].items():
        for collector in collectors:
            collector_dir = f'{input_dir}{source}/{collector}/'
            candidate_file = get_candidate_file(collector_dir,
                                                timestamp,
                                                max_timestamp_difference,
                                                RIB_FILE_FORMATS)
            if candidate_file is None:
                continue
            output_file = f'{output_dir}{source}/{collector}/{timestamp.strftime(FOLDER_FORMAT)}/{os.path.splitext(candidate_file[0])[0]}{OUTPUT_FILE_SUFFIX}'
            if not args.force and os.path.exists(output_file):
                skipped_files += 1
                continue
            fixtures.append((candidate_file[1], output_file))

    if skipped_files > 0:
        logging.info(f'Skipped {skipped_files} existing files. Use --force to overwrite.')

    num_workers = args.num_workers
    logging.info(f'Processing {len(fixtures)} files with {num_workers} parallel workers')
    with Pool(num_workers) as p:
        stats = p.map(transform_rib, fixtures)
    print_stats(stats)


if __name__ == '__main__':
    main()
    sys.exit(0)
