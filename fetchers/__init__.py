import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Tuple

import requests
from bs4 import BeautifulSoup

from helpers.defines import FOLDER_FORMAT


class BaseFetcher(ABC):
    def __init__(self, collector: str, url: str, timestamp: datetime, output_dir: str = 'data/') -> None:
        self.folder_format = FOLDER_FORMAT
        # If no file for the specified time is found, fetch the
        # next best, but only if the time difference is below this
        # threshold.
        self.max_timestamp_difference = timedelta(hours=24)

        self.collector = collector
        self.url = f'{url}{timestamp.strftime(self.folder_format)}/'
        self.timestamp = timestamp
        self.output_dir = str()
        self.file_list = list()
        logging.debug(f'{collector} {timestamp}')

    def get_closest_file(self) -> Tuple[datetime, str, str]:
        closest_file = None
        closest_diff = None
        for file_info in self.file_list:
            file_ts = file_info[0]
            file_ts_diff = abs(file_ts - self.timestamp)
            if file_ts_diff > self.max_timestamp_difference:
                continue
            if closest_diff is None or file_ts_diff < closest_diff:
                closest_file = file_info
                closest_diff = file_ts_diff
        if closest_file is None:
            logging.warning(f'Failed to find valid file for collector {self.collector}')
        else:
            logging.debug(f'{self.collector} {closest_diff} {closest_file[0]} {closest_file[1]}')
        return closest_file

    def fetch(self) -> None:
        if (self.get_file_list()):
            return
        candidate_file = self.get_closest_file()
        if candidate_file is None:
            return
        output_file = f'{self.output_dir}{candidate_file[1]}'
        if os.path.exists(output_file):
            logging.info(f'{self.collector}: File already cached {output_file}')
            return
        fetched_file = self.fetch_url(candidate_file[2])
        if fetched_file is None:
            return
        os.makedirs(self.output_dir, exist_ok=True)
        self.write_to_file(fetched_file, output_file)

    def fetch_url(self, url: str) -> requests.Response:
        logging.info(f'{self.collector} Fetching {url}')
        try:
            r = requests.get(url)
            r.raise_for_status()
        except requests.HTTPError as e:
            logging.error(f'{self.collector} Failed to fetch data from {url}: {e}')
            return None
        return r

    @abstractmethod
    def get_file_list() -> None:
        """Populate self.file_list with a list of timestamped files.

        Fetch files from self.url and parse valid files according to the format
        specified by the respective Fetcher instance.
        """
        pass

    @staticmethod
    def parse_link_list(response: requests.Response) -> list:
        """Extract all href links from the specified response."""
        ret = list()
        for link in BeautifulSoup(response.text, 'html.parser').find_all('a'):
            if 'href' in link.attrs:
                ret.append(link.attrs['href'])
        return ret

    @staticmethod
    def write_to_file(response: requests.Response, output_file: str) -> None:
        with open(output_file, 'wb') as f:
            f.write(response.content)
