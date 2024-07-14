import logging
import os
from datetime import datetime, timezone

from fetchers import BaseFetcher
from helpers.defines import DEFAULT_DATA_FOLDER, ROUTE_VIEWS_RIB_FORMATS


class RouteViewsFetcher(BaseFetcher):
    def __init__(self, collector: str, url: str, timestamp: datetime, output_dir: str = DEFAULT_DATA_FOLDER) -> None:
        super().__init__(collector, url, timestamp, output_dir)
        self.output_dir = os.path.join(output_dir, 'routeviews', collector, timestamp.strftime(self.folder_format))

    def get_file_list(self) -> bool:
        base_index = super().fetch_url(self.url)
        if not base_index:
            return True
        links = super().parse_link_list(base_index)
        if 'RIBS/' in links:
            # New format, need to go one layer deeper.
            self.url += 'RIBS/'
            directory_index = super().fetch_url(f'{self.url}')
            if not directory_index:
                return True
            links = super().parse_link_list(directory_index)
        self.file_list = list()
        for link in links:
            if not link.endswith('.bz2'):
                logging.debug(f'Skipping file {link}')
                continue
            file_ts = None
            for format in ROUTE_VIEWS_RIB_FORMATS:
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
