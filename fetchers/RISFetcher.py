import logging
from datetime import datetime, timezone

from fetchers import BaseFetcher
from helpers.defines import RIS_RIB_FORMATS


class RISFetcher(BaseFetcher):
    def __init__(self, collector: str, url: str, timestamp: datetime, output_dir: str = 'data/') -> None:
        super().__init__(collector, url, timestamp, output_dir)
        self.output_dir = f'{output_dir}ris/{collector}/{timestamp.strftime(self.folder_format)}/'

    def get_file_list(self) -> bool:
        base_index = super().fetch_url(self.url)
        if not base_index:
            return True
        links = super().parse_link_list(base_index)
        self.file_list = list()
        for link in links:
            if not link.endswith('.gz') or link.startswith('updates'):
                logging.debug(f'Skipping file {link}')
                continue
            file_ts = None
            for format in RIS_RIB_FORMATS:
                try:
                    file_ts = datetime.strptime(link, format).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
            if file_ts is None:
                logging.error(f'Failed to get timestamp from file {link}')
                continue
            self.file_list.append((file_ts, link, f'{self.url}{link}'))
        logging.debug(f'Found {len(self.file_list)} files.')
        return False
