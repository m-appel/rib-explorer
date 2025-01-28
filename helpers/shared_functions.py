import logging
import os
from datetime import datetime, timedelta, timezone

from helpers.defines import DEFAULT_INDEX_FOLDER, FOLDER_FORMAT, INDEX_OUTPUT_FILE_FORMAT, STATS_OUTPUT_FILE_FORMAT, TIMESTAMP_FORMAT


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
    month_folder = os.path.join(collector_dir, timestamp.strftime(FOLDER_FORMAT))
    if not os.path.exists(month_folder):
        logging.warning(f'Folder does not exist: {month_folder}')
        return None
    best_diff = None
    best_file = None
    for entry in os.scandir(month_folder):
        if not entry.is_file():
            continue
        file_ts = None
        file_path = os.path.join(month_folder, entry.name)
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


def get_latest_index_file(timestamp: datetime) -> str:
    latest = None
    file_name = str()
    for entry in os.scandir(DEFAULT_INDEX_FOLDER):
        try:
            entry_dt = datetime.strptime(entry.name, INDEX_OUTPUT_FILE_FORMAT).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if not latest or entry_dt > latest:
            latest = entry_dt
            file_name = entry.name
    if latest is None:
        logging.error('Failed to find valid index file.')
        return str()
    if timestamp > latest:
        logging.warning(f'Latest index file is older than the requested timestamp. Index: {latest}')
    return os.path.join(DEFAULT_INDEX_FOLDER, file_name)


def get_stat_file_name(timestamp: datetime, stats_dir: str, stat_type: str) -> str:
    output_file_name = timestamp.strftime(STATS_OUTPUT_FILE_FORMAT).format(type=stat_type)
    return os.path.join(stats_dir, output_file_name)
