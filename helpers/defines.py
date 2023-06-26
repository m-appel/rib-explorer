FOLDER_FORMAT = '%Y.%m'
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
