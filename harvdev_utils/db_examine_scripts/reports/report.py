import argparse
from cell_line import CellLineReport
import sys

import logging

log = logging.getLogger(__name__)

table_types = {'cell_line': CellLineReport}

parser = argparse.ArgumentParser()
parser.add_argument('-n', '--name', help=' (name to make report for)', required=True)
parser.add_argument('-t', '--tablename', help=' (table name to look up name in)', required=True)
parser.add_argument('-b', '--by', help='lookup by', choices=['name', 'uniquename'], default='name')
parser.add_argument('-d', '--debug', help='dump out all debug messages', default=False, action='store_true')
parser.add_argument('-c', '--config', help='Specify the location of the configuration file.', required=True)
parser.add_argument('-l', '--limit', help='Limit to x for each table', type=int, default=0, required=False)
args = parser.parse_args()

if args.debug:
    print("Running in Debug mode")
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(levelname)s -- %(message)s')
    logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
    # comment/uncomment out below to notsee/see NOTICE messages for sql functions.
    # logging.getLogger('sqlalchemy.dialects.postgresql').setLevel(logging.INFO)
else:
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(levelname)s -- %(message)s')

if __name__ == '__main__':
    if args.tablename not in table_types:
        log.error("Only table types of the following are allowed presently:-")
        for table in table_types.keys():
            print("\t{}".format(table))
        exit(-1)
    params_to_send = {
        'config': args.config,
        'name': args.name,
        'lookup_by': args.by}
    tt = table_types[args.tablename](params_to_send)
    tt.dump_data()
