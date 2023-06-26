import logging
import os
from datetime import datetime, timedelta, timezone

from helpers.defines import FOLDER_FORMAT, TIMESTAMP_FORMAT


def sanitize_dir(dir: str) -> str:
    if not dir.endswith('/'):
        dir += '/'
    return dir


def parse_timestamp_argument(arg: str) -> datetime:
    try:
        timestamp = datetime.strptime(arg, TIMESTAMP_FORMAT).replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return timestamp


def get_candidate_file(
        collector_dir: str,
        timestamp: datetime,
        max_timestamp_difference: timedelta,
        file_formats: list) -> str:
    """Find the file closest to the specified timestamp.

    Looks for files according to file_formats in collector_dir that are close to
    timestamp. max_timestamp_difference can be used to limit the acceptable deviation
    from the specified timestamp. Returns None if no valid file is found.
    """
    month_folder = f'{collector_dir}{timestamp.strftime(FOLDER_FORMAT)}/'
    if not os.path.exists(month_folder):
        logging.warning(f'Folder does not exist: {month_folder}')
        return None
    best_diff = None
    best_file = None
    for entry in os.scandir(month_folder):
        if not entry.is_file():
            continue
        file_ts = None
        file_path = f'{month_folder}{entry.name}'
        for format in file_formats:
            try:
                file_ts = datetime.strptime(entry.name, format).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        if file_ts is None:
            logging.error(f'Failed to get timestamp for file: {file_path}')
            continue
        file_diff = abs(file_ts - timestamp)
        if file_diff > max_timestamp_difference:
            continue
        if best_diff is None or file_diff < best_diff:
            best_diff = file_diff
            best_file = (entry.name, file_path)
    if best_file is None:
        logging.warning(f'No valid file found in folder: {month_folder}')
    return best_file
