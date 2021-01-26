"""Check for proforma log and xml files."""
from collections import deque
import re


def xort_logfile_check(filename):
    """Check output from xort.

    filename: full filename and path of xort log file.
              will normally be something like
              /users/falls/DB_update/epicycle_log/harv_2017_02_e5_p1.load

    return wether okay or not and an error string
    """
    okay = True
    errors = []

    # check log file for the word ERROR
    count = 0
    old_lines = deque(maxlen=10)
    count = 0
    bingo_you_success = False
    with open(filename, "r") as log_file:
        for line in log_file:
            count += 1
            old_lines.append(line)
            if "bingo ....you success" in line:
                bingo_you_success = True
            if 'ERROR' in line:
                okay = False
                errors.append((count, filename, old_lines))
    error_lines = ""
    if not okay:
        for item in errors:
            error_lines += "file:{}, line {}, 10 subsequent lines were {}".format(item[1], item[0], item[2])

    if not count:  # Must be a problem if empty
        error_lines = "Empty log file.This should not be possible!!"
        okay = False
    elif not bingo_you_success:
        error_lines = "Error: NO 'bingo ....you success' found"
        okay = False
    return okay, error_lines


def proforma_logfile_check(logfile):
    """Check proforma output.

    1) check logfile for string ERROR
       if found get file and lines around error i.e.
       /users/falls/DB_update/epicycle_log/harv_2017_02_e5_p1.log

    return wether okay or not and an error string
    """
    okay = True
    errors = []
    proforma_file_pattern = r'==Opening: ./proforma/(\S+)=='

    # check log file for the word ERROR
    old_lines = deque(maxlen=10)
    count = 0
    file_filename = None
    with open(logfile, "r") as log_file:
        for line in log_file:
            count += 1
            old_lines.append(line)
            fields = re.search(proforma_file_pattern, line)
            if fields:
                if fields.group(1):
                    file_filename = fields.group(1)
            if 'ERROR' in line:
                okay = False
                output = ''
                for old_line in old_lines:
                    output += "\tline: {}".format(old_line)
                errors.append((count, file_filename, output))
    error_lines = ""
    if not okay:
        for item in errors:
            error_lines += "file:{}, line {}, 10 subsequent lines were:-\n{}".format(item[1], item[0], item[2])

    if not count:  # Must be a problem if empty
        error_lines += "Empty log file.This should not be possible!!"
        okay = False
    if not file_filename:
        error_lines += "No file in log file. So no files processed?"
        okay = False

    return okay, error_lines


def check_xml(xmlfile):
    """Check xml ends in </chado>.

    return wether okay or not and an error string
    """
    okay = True
    error = ""
    line_count = 0
    # check xml ends with </chado>
    with open(xmlfile) as xml_file:
        for line in xml_file:
            line_count += 1
        if not line_count:
            okay = False
            error = "Empty file not allowed"
        elif '</chado>' not in line:
            error = "ERROR: {} does not end in '</chado>' but with '{}'.".format(xmlfile, line)
            okay = False
    return okay, error


def new_proforma_logfile_check(filename):
    """Check this log file to make and pass back success status.

    return wether okay or not and an error string
    """
    okay = True

    # check log file for the word ERROR
    count = 0
    error_lines = ""
    bingo_you_success = False
    with open(filename, "r") as log_file:
        for line in log_file:
            count += 1
            if "bingo ....you success" in line:
                bingo_you_success = True

    if not count:  # Must be a problem if empty
        error_lines += "Empty log file. No data??\n"
        okay = False
    if not bingo_you_success:
        error_lines += "Error: NO 'bingo ....you success' found\n"
        okay = False
    return okay, error_lines
