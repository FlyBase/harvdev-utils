"""Feature Summary.

List a features and its connections in a summary.
"""
import argparse
import logging
import sys

from sum_report import report, create_postgres_session

description = """
Code to display all feature data and relationships etc for a given feature.

Can be used as the basis for future proforma work.

"""

examples = """

Dref-XR has feature expressions.
i.e. python feature_summary.py -c chado.cfg -f Dref-XR -l 2 -t RNA

Bre1 has feature grpmember
python feature_summary.py -c chado.cfg -f Bre1 -l 2

feature interaction:-
python feature_summary.py -c chado.cfg -f 'Ppat-Dpck-XP' -l 2 -t protein

test db:-
python3 feature_summary.py -f symbol-41 -b symbol -c tester.cfg

"""
parser = argparse.ArgumentParser(description=description, epilog=examples, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('-f', '--featuresymbol', help=' (feature symbol to make report for)', required=True)
parser.add_argument('-t', '--type', help=' (feature type to make report for)', required=False)
parser.add_argument('-b', '--by', help='lookup by', choices=['symbol', 'name', 'uniquename'], default='symbol')
parser.add_argument('-d', '--debug', help='dump out all debug messages', default=False, action='store_true')
parser.add_argument('-c', '--config', help='Specify the location of the configuration file.', required=True)
parser.add_argument('-o', '--obsolete', help='Specify if feature is obsolete.', default=False, action='store_true')
parser.add_argument('-n', '--noheader', help='Don not add header info, like database connection details etc', default=False, action='store_true')
args = parser.parse_args()

log = logging.getLogger(__name__)


if args.debug:
    print("Running in Debug mode")
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(levelname)s -- %(message)s')
    logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
    # comment/uncomment out below to notsee/see NOTICE messages for sql functions.
    # logging.getLogger('sqlalchemy.dialects.postgresql').setLevel(logging.INFO)
else:
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(levelname)s -- %(message)s')

if args.obsolete:
    obsolete = 't'
else:
    obsolete = 'f'

if args.noheader:
    noheader = True
else:
    noheader = False

if __name__ == '__main__':
    session = create_postgres_session(config_file=args.config, noheader=True)
    report(session, args.featuresymbol, args.type, args.debug, 0, args.by, obsolete, noheader=True)
