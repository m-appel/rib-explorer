import argparse
import json
import logging
import sys
from multiprocessing import Pool

from fetchers import BaseFetcher
from fetchers.RISFetcher import RISFetcher
from fetchers.RouteViewsFetcher import RouteViewsFetcher
from helpers.defines import TIMESTAMP_FORMAT_ESCAPED
from helpers.shared_functions import parse_timestamp_argument, sanitize_dir


def fetch(collector: BaseFetcher) -> None:
    collector.fetch()


def main() -> None:
    desc = """Takes an index file (created with build-index.py) and a timestamp fo fetch RIBs for
    the specified timestamp in parallel."""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('index')
    parser.add_argument('timestamp', help=f'UTC timestamp in {TIMESTAMP_FORMAT_ESCAPED} format')
    parser.add_argument('-o', '--output-dir',
                        default='data/',
                        help='change default output directory')
    parser.add_argument('-n', '--num-workers',
                        type=int,
                        default=4,
                        help='number of parallel workers')
    args = parser.parse_args()

    FORMAT = '%(asctime)s %(levelname)s %(message)s'
    logging.basicConfig(
        format=FORMAT,
        handlers=[
            logging.FileHandler('fetch-snapshots.log'),
            logging.StreamHandler(sys.stdout)
        ],
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logging.info(f'Started {sys.argv}')

    timestamp = parse_timestamp_argument(args.timestamp)
    if timestamp is None:
        logging.error(f'Invalid timestamp specified')
        sys.exit(1)

    index_file = args.index
    with open(index_file, 'r') as f:
        index = json.load(f)

    output_dir = sanitize_dir(args.output_dir)
    collectors = list()
    # Build Route Views fetchers
    for collector, url in index['sources']['routeviews'].items():
        logging.debug(f'Creating RouteViewsFetcher {collector}')
        collectors.append(RouteViewsFetcher(collector, url, timestamp, output_dir))
    # Build RIS fetchers
    for collector, url in index['sources']['ris'].items():
        logging.debug(f'Creating RISFetcher {collector}')
        collectors.append(RISFetcher(collector, url, timestamp, output_dir))

    num_workers = args.num_workers
    logging.info(f'Starting {num_workers} workers')
    with Pool(num_workers) as p:
        p.map(fetch, collectors)


if __name__ == '__main__':
    main()
    sys.exit(0)
