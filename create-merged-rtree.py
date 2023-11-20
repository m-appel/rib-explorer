import argparse
import bz2
import json
import logging
import pickle
import sys
from collections import defaultdict
from datetime import timedelta

import radix

from helpers.defines import RTREE_FILE_FORMATS, TIMESTAMP_FORMAT_ESCAPED
from helpers.shared_functions import get_candidate_file, parse_timestamp_argument, sanitize_dir

EXPECTED_OUTPUT_FILE_SUFFIX = '.pickle.bz2'


def main() -> None:
    desc = """Create a radix tree merging information from all collectors.

    Prefixes for which the collectors do not agree on the origin are ignored by default.
    In addition, a minimum number or ratio of collectors can be specified. If a prefix
    is seen by fewer collectors, it is ignored as well."""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('index')
    parser.add_argument('timestamp', help=f'UTC timestamp in {TIMESTAMP_FORMAT_ESCAPED} format')
    parser.add_argument('output_file')
    parser.add_argument('--max-timestamp-difference',
                        type=int,
                        default=24,
                        help='max allowed difference (in h) from timestamp')
    parser.add_argument('-i', '--input-dir',
                        default='transformed/',
                        help='change default input directory')
    min_group = parser.add_mutually_exclusive_group()
    min_group.add_argument('--min-collector-ratio',
                           type=float,
                           help='ratio (0-1) of collectors required to include prefix')
    min_group.add_argument('--min-collector-count',
                           type=int,
                           help='number of collectors required to include prefix')
    args = parser.parse_args()

    FORMAT = '%(asctime)s %(levelname)s %(message)s'
    logging.basicConfig(
        format=FORMAT,
        handlers=[
            logging.FileHandler('create-merged-rtree.log'),
            logging.StreamHandler(sys.stdout)
        ],
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logging.info(f'Started {sys.argv}')

    timestamp = parse_timestamp_argument(args.timestamp)
    if timestamp is None:
        logging.error('Invalid timestamp specified')
        sys.exit(1)

    index_file = args.index
    with open(index_file, 'r') as f:
        index = json.load(f)

    output_file = args.output_file
    if not output_file.endswith(EXPECTED_OUTPUT_FILE_SUFFIX):
        logging.warning(f'Output file will be in {EXPECTED_OUTPUT_FILE_SUFFIX} format, but different file suffix was '
                        f'specified.')

    logging.info('Reading input files...')
    input_dir = sanitize_dir(args.input_dir)
    max_timestamp_difference = timedelta(hours=args.max_timestamp_difference)
    # prefix -> as -> set of collectors
    prefix_maps = defaultdict(lambda: defaultdict(set))
    total_collector_count = 0
    for source, collectors in index['sources'].items():
        for collector in collectors:
            collector_dir = f'{input_dir}{source}/{collector}/'
            candidate_file = get_candidate_file(collector_dir,
                                                timestamp,
                                                max_timestamp_difference,
                                                RTREE_FILE_FORMATS)
            if candidate_file is None:
                continue
            total_collector_count += 1
            with bz2.open(candidate_file[1], 'rb') as f:
                collector_rtree: radix.Radix = pickle.load(f)
            for node in collector_rtree.nodes():
                prefix_maps[node.prefix][node.data['as']].add(collector)

    logging.info(f'Read files from {total_collector_count} collectors')
    min_collector_count = 0
    if args.min_collector_ratio:
        min_collector_ratio = args.min_collector_ratio
        logging.info(f'Min. collector ratio: {min_collector_ratio}')
        min_collector_count = int(total_collector_count * min_collector_ratio)
    elif args.min_collector_count:
        min_collector_count = args.min_collector_count
    logging.info(f'Min. collector count: {min_collector_count}')

    merged_rtree = radix.Radix()
    total_prefixes = len(prefix_maps)
    used_prefixes = 0
    collector_count_agg = 0
    unique_prefixes = 0
    below_threshold_prefixes = 0
    contested_prefixes = 0
    for prefix, ases in prefix_maps.items():
        if len(ases) > 1:
            # Never include contested prefixes.
            contested_prefixes += 1
            continue
        unique_prefixes += 1
        asn, collector_set = tuple(ases.items())[0]
        if len(collector_set) < min_collector_count:
            below_threshold_prefixes += 1
            continue
        node = merged_rtree.add(prefix)
        node.data['as'] = asn
        node.data['seen_by_collectors'] = tuple(collector_set)
        used_prefixes += 1
        collector_count_agg += len(collector_set)

    # Statistics
    avg_collector_count = collector_count_agg / used_prefixes

    total_ignored_prefixes = contested_prefixes + below_threshold_prefixes
    total_ignored_prefixes_pct = total_ignored_prefixes / total_prefixes * 100

    below_threshold_prefixes_total_pct = below_threshold_prefixes / total_prefixes * 100
    below_threshold_prefixes_pct = 0
    if total_ignored_prefixes > 0:
        below_threshold_prefixes_pct = below_threshold_prefixes / total_ignored_prefixes * 100

    contested_prefixes_total_pct = contested_prefixes / total_prefixes * 100
    contested_prefixes_pct = 0
    if total_ignored_prefixes > 0:
        contested_prefixes_pct = contested_prefixes / total_ignored_prefixes * 100

    used_prefixes_pct = used_prefixes / total_prefixes * 100

    # autopep8: off
    logging.info(f'Used {used_prefixes} prefixes seen by {avg_collector_count:.2f} collectors on average')
    logging.info(f'                     Total: {total_prefixes:7,d} 100.00%')
    logging.info(f'                   Ignored: {total_ignored_prefixes:7,d} {total_ignored_prefixes_pct:6.2f}% 100.00%')
    logging.info(f'Announced by multiple ASes: {contested_prefixes:7,d} {contested_prefixes_total_pct:6.2f}% {contested_prefixes_pct:6.2f}%')
    logging.info(f'           Below threshold: {below_threshold_prefixes:7,d} {below_threshold_prefixes_total_pct:6.2f}% {below_threshold_prefixes_pct:6.2f}%')
    logging.info(f'                      Used: {used_prefixes:7,d} {used_prefixes_pct:6.2f}%')
    # autopep8: on

    with bz2.open(output_file, 'wb') as f:
        pickle.dump(merged_rtree, f)


if __name__ == '__main__':
    main()
    sys.exit(0)
