"""Search archives for specific fields WITH values."""
import re
import argparse
import subprocess
help = r"""   Search archive file, start with most recent and search backwards.

   Required field name: (-f --field)
     AND/OR
   Required value: (-v --value)

   Option to find a certain number of these.
     Default is 1. (-l --limit)

   Option to search just cambridge OR harvard.
     Default both. (-s --site)

   # Later maybe Option to lookup specific value too.

   Usage examples
   # Find examples of GA2c that have value and NOT blank
   python search_archives.py -l 5 -f GA2c

   # Find up to 999 examples maximum of Oseg1
   python search_archives.py -v Oseg3 -l 999

   # find examples of GA1a with the value 'zyd[JF01872]'
   # NOTE: Safer to put ANY names with special chars like []!\ etc in quotes.
   python search_archives.py -f GA1a -v 'zyd[JF01872]'

   Disclaimer:
      When specifying a field and a value it will NOT find examples where they are on seperate lines.
      i.e. when we have multiple values and it is not on the same line.
"""
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=help)
parser.add_argument('-l', '--limit', help='Limit to x finds', type=int, default=1, required=False)
parser.add_argument('-s', '--site', help="Restrict to harvard or cambridge", default=None, required=False)
parser.add_argument('-f', '--field', help="Proforma filed name", default=None, required=False)
parser.add_argument('-v', '--value', help="value, symbol name etc", default=None, required=False)
parser.add_argument('-d', '--debug', help="For debugging NOT recomended", default=False, action='store_true', required=False)
args = parser.parse_args()

cam_start = '/data/camdata/proforma/'
harv_start = '/data/harvcur/archive/'
debug = False

if args.debug:
    debug = True
field_search = True

if not (args.field or args.value):
    print("field or value is required")
    print(help)
    exit(-1)

process_cam = False
process_harv = False
if args.site:
    if args.site == 'cambridge':
        process_cam = True
    elif args.site == 'harvard':
        process_harv = True
    else:
        print("Site must be unspecified OR cambridge or harvard NOT {}".format(args.site))
else:
    process_cam = True
    process_harv = True


def get_ordered_directory_list(base_dir):
    """Get list of directorys to examine.

    This is the same for cambridge as harvard so does not matter which.
    """
    dir_list = []
    cmd = "ls -lt {}".format(base_dir)
    if debug:
        print(cmd)
    output = subprocess.getoutput(cmd)
    pattern = r"\d{4}_\d{2}"

    for line in output.split('\n'):
        if debug:
            print(line)
        filename = line.split()[-1].strip()
        if re.match(pattern, filename):
            dir_list.append(filename)
    return dir_list


def search_proforma(grep_dir_string, field=None, value=None):  # noqa
    """Lookup field or value in the files represented by grep_dir_string."""
    if field and value:
        cmd = "grep '\\![c]* {}[.]' {} | grep {}".format(field, grep_dir_string, value)
    elif field:
        cmd = "grep '\\![c]* {}[.]' {}".format(field, grep_dir_string)
    else:
        cmd = "grep '{}' {}".format(value, grep_dir_string)

    if debug:
        print("command is {}".format(cmd))
    output = subprocess.getoutput(cmd)
    if debug:
        print(output)
    count = 0
    for line in output.split('\n'):
        if not line:
            continue
        if debug:
            print("line is {}".format(line))
        if 'Is a directory' in line:
            continue
        if field:  # make sure it has a value
            col_split = line.strip().split(':')
            FILENAME = 0
            VALUE = 2
            #print("col_split {}, {}".format(col_split, len(col_split)))
            if len(col_split) >= 4:
                prof_value = ':'.join(col_split[VALUE:])
            else:
                prof_value = col_split[VALUE]
            if prof_value:
                count += 1
                print("{}\t{}\t{}".format(col_split[FILENAME], field, prof_value))
        else:
            count += 1
            print(line)
    return count


if __name__ == '__main__':
    # get list of directory to check
    dir_list = get_ordered_directory_list(cam_start)
    found = 0
    for sub_dir in dir_list:
        if found < args.limit:
            print("searching\t{}".format(sub_dir))
            if process_harv:
                found += search_proforma("{}{}/*/*".format(harv_start, sub_dir),
                                         field=args.field, value=args.value)
            if process_cam:
                found += search_proforma("{}{}/*/*/*".format(cam_start, sub_dir),
                                         field=args.field, value=args.value)
            if found > args.limit:
                print("Stopping due to limit being passed")
                exit(0)
    if not found:
        print("Sorry nothing found for this")
    else:
        print("Total of {} found".format(found))
