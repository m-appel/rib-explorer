DEFAULT_DATA_FOLDER = 'data/'
DEFAULT_INDEX_FOLDER = 'indexes/'
DEFAULT_MERGED_FOLDER = 'merged/'
DEFAULT_TRANSFORMED_FOLDER = 'transformed/'
DEFAULT_STATS_FOLDER = 'stats/'

FOLDER_FORMAT = '%Y.%m'

INDEX_OUTPUT_FILE_FORMAT = '%Y%m%d.index.json'
STATS_OUTPUT_FILE_FORMAT = '%Y%m%d.{type}-stats.csv'
EXPECTED_OUTPUT_FILE_SUFFIX = '.pickle.bz2'
RTREE_OUTPUT_FILE_FORMAT = '%Y%m%d{suffix}' + EXPECTED_OUTPUT_FILE_SUFFIX

# Used for argparse help texts, which do not like % characters.
TIMESTAMP_FORMAT_ESCAPED = 'YYYY-mm-ddTHH:MM'
TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M'

ROUTE_VIEWS_RIB_FORMATS = ['rib.%Y%m%d.%H%M.bz2',
                           'route-views3-full-snapshot-%Y-%m-%d-%H%M.dat.bz2']
RIS_RIB_FORMATS = ['bview.%Y%m%d.%H%M.gz']
RIB_FILE_FORMATS = ROUTE_VIEWS_RIB_FORMATS + RIS_RIB_FORMATS

ROUTE_VIEWS_RTREE_FORMATS = ['rib.%Y%m%d.%H%M.pickle.bz2',
                             'route-views3-full-snapshot-%Y-%m-%d-%H%M.dat.pickle.bz2']
RIS_RTREE_FORMATS = ['bview.%Y%m%d.%H%M.pickle.bz2']
RTREE_FILE_FORMATS = ROUTE_VIEWS_RTREE_FORMATS + RIS_RTREE_FORMATS
