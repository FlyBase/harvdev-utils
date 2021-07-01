"""Db Report."""

import argparse
import logging


from harvdev_utils.chado_functions import (get_cvterm)

from sum_report import report, create_postgres_session
description = """
Code to display all feature data and relationships etc for a given database.

Can be used examine database (most likely the test one)

"""

examples = """

List the first 10 feature of each type for the test database
    python  db_report_examine.py -c tester.cfg

List 2 features of each type that have 'prop' in their name.
    python db_report_examine.py -c tester.cfg -l 2 -r prop

List all the genes
     python db_report_examine.py -c tester.cfg -t gene

"""

type_list = [
    'polypeptide', 'transgenic_transposable_element', 'allele', 'engineered_region',
    'golden_path', 'insertion_site', 'disease implicated variant', 'chromosome_arm',
    'transposable_element_insertion_site', 'point_mutation', 'engineered_plasmid', 'mRNA',
    'chromosome_band', 'cDNA_clone', 'gene', 'chemical entity', 'natural_transposable_element',
    'chromosome', 'chromosome_structure_variation']

alt_feat_type = {'disease implicated variant': 'FlyBase miscellaneous CV',
                 'chemical entity': 'FlyBase miscellaneous CV'}

parser2 = argparse.ArgumentParser(description=description, epilog=examples, formatter_class=argparse.RawDescriptionHelpFormatter)
parser2.add_argument('-t', '--type', help=' (feature type to make report for)', required=False)
parser2.add_argument('-c', '--config', help='Specify the location of the configuration file.', required=True)
parser2.add_argument('-o', '--obsolete', help='Specify if feature is obsolete.', default=False, action='store_true')
parser2.add_argument('-l', '--limit', help='Limit to x for each feature', type=int, default=10, required=False)
parser2.add_argument('-r', '--regex', help="regex of symbols to look up", required=False)

args = parser2.parse_args()

log = logging.getLogger(__name__)

if args.obsolete:
    obsolete = 't'
else:
    obsolete = 'f'


def get_sql_query():
    """Get sql query results."""
    cvname = 'SO'
    if feat_type in alt_feat_type:
        cvname = alt_feat_type[feat_type]
    cvterm = get_cvterm(session, cvname, feat_type)
    if not args.regex:
        feat_sql = "SELECT name FROM feature where type_id = {}".format(cvterm.cvterm_id)
    else:
        feat_sql = "SELECT name FROM feature where type_id = {} AND name like '%{}%'".format(cvterm.cvterm_id, args.regex)
    if args.obsolete:
        feat_sql += " AND is_obsolete = True"
    else:
        feat_sql += " AND is_obsolete = False"
    try:
        results = session.execute(feat_sql)
    except Exception:
        return None
    return results


if __name__ == '__main__':
    session = create_postgres_session(config_file=args.config, noheader=True)
    if args.type:
        type_list = [args.type]
    for feat_type in type_list:
        # print(dir(session))
        query_results = get_sql_query()
        if not query_results:
            continue
        count = 0
        while (count < args.limit):
            count += 1
            try:
                result = next(query_results)
                if result:
                    report(session, result[0], feat_type, True, args.limit, 'name', obsolete, noheader=True)
                    print()
            except StopIteration:
                continue
            except ValueError:  # Not found, this is okay
                continue
