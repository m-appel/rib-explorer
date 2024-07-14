import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from helpers.defines import DEFAULT_INDEX_FOLDER, INDEX_OUTPUT_FILE_FORMAT

ROUTE_VIEWS_INDEX_URL = 'http://routeviews.org'
RIS_API_ENDPOINT = 'https://stat.ripe.net/data/rrc-info/data.json'
RIS_COLLECTOR_FORMAT = 'rrc{id:02d}'
RIS_COLLECTOR_URL_FORMAT = 'https://data.ris.ripe.net/{collector}/'


def get_route_views_collector_name(url: str) -> str:
    url_split = url.strip('/').split('/')
    if len(url_split) != 2:
        logging.error(f'Failed to get collector name from: {url}')
        return str()
    return url_split[0]


def fetch_url(url: str) -> requests.Response:
    logging.info(f'Fetching data from {url}')
    r = requests.get(url)
    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        logging.error(f'Request failed: {e}')
        return None
    return r


def fetch_route_views_source() -> str:
    """Fetch the HTML source of the Route Views landing page."""
    r = fetch_url(ROUTE_VIEWS_INDEX_URL)
    if not r:
        return str()
    return r.text


def fetch_ris_data() -> dict:
    """Fetch the full RIS API endpoint JSON object."""
    r = fetch_url(RIS_API_ENDPOINT)
    if not r:
        return dict()
    try:
        data = r.json()
    except requests.JSONDecodeError as e:
        logging.error(f'JSON decoding failed: {e}')
        return dict()
    return data


def get_route_views_collectors(source: str) -> list:
    """Extract links to Route Views collectors from website."""
    soup = BeautifulSoup(source, 'html.parser')
    collector_links = list()
    for link in soup.find_all('a'):
        attrs = link.attrs
        if 'href' not in attrs or 'bgpdata' not in attrs['href']:
            continue
        url_suffix = attrs['href']
        url = f'{ROUTE_VIEWS_INDEX_URL}{url_suffix}'
        if url_suffix == '/bgpdata':
            # I guess for historical reasons route-views2 is not in a directory.
            collector_links.append(('route-views2', url))
            continue
        collector = get_route_views_collector_name(url_suffix)
        if not collector:
            continue
        collector_links.append((collector, url))
    logging.info(f'Found {len(collector_links)} Route Views collectors')
    return collector_links


def fetch_ris_collectors() -> list:
    """Build a list of RIS collector links.

    Create links from the URL template and the collector ids collected from the RIS API
    dump. Each collector has a numerical id from which the name is inferred according to
    the format rrc{id:02d}.
    """
    collector_data = fetch_ris_data()
    if not collector_data:
        return list()
    if 'data' not in collector_data or 'rrcs' not in collector_data['data']:
        logging.error(f'Failed to parse returned data structure: {collector_data}')
        return list()
    collector_links = list()
    for collector in collector_data['data']['rrcs']:
        if 'id' not in collector:
            logging.error(f'Missing "id" field for collector: {collector}')
            continue
        collector = RIS_COLLECTOR_FORMAT.format(id=collector['id'])
        url = RIS_COLLECTOR_URL_FORMAT.format(collector=collector)
        collector_links.append((collector, url))
    logging.info(f'Found {len(collector_links)} RIS collectors')
    return collector_links


def suffix_url(url: str) -> str:
    if not url.endswith('/'):
        url += '/'
    return url


def handle_route_views() -> dict:
    source = fetch_route_views_source()
    if not source:
        return dict()

    collector_links = get_route_views_collectors(source)
    ret = dict()
    for collector, url in sorted(collector_links):
        ret[collector] = suffix_url(url)
    return ret


def handle_ris() -> dict:
    collector_links = fetch_ris_collectors()
    ret = dict()
    for collector, url in sorted(collector_links):
        ret[collector] = suffix_url(url)
    return ret


def main() -> None:
    desc = """Fetch a list of all Route Views and RIPE RIS collectors."""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-o', '--output-dir',
                        default=DEFAULT_INDEX_FOLDER,
                        help=f'output directory (default: {DEFAULT_INDEX_FOLDER})')
    args = parser.parse_args()

    FORMAT = '%(asctime)s %(levelname)s %(message)s'
    logging.basicConfig(
        format=FORMAT,
        level=logging.INFO,
        handlers=[
            logging.FileHandler('build-index.log'),
            logging.StreamHandler(sys.stdout)
        ],
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    output_data = dict()
    output_data['created'] = datetime.now(tz=timezone.utc).isoformat()
    sources = dict()
    route_views = handle_route_views()
    if route_views:
        sources['routeviews'] = route_views
    ris = handle_ris()
    if ris:
        sources['ris'] = ris
    if not sources:
        sys.exit(1)
    output_data['sources'] = sources

    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, datetime.now(tz=timezone.utc).strftime(INDEX_OUTPUT_FILE_FORMAT))
    logging.info(f'Writing data to: {output_file}')

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=4)


if __name__ == '__main__':
    main()
    sys.exit(0)
