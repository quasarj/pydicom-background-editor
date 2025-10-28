# """
# From the original background editor help:

# Usage:
# BackgroundEditor# Another horrible kludge allows remapping private blocks (e.g):
#       0013
#       This is specifically to support the op move_owner_block ("CTP", "10") (note arg is hex string, not number)

import logging

# The contents of the fields <tag>, <value1>, and <value2> may by enclosed in<?bkgrnd_id?> <activity_id> "<edit_desciption>" <notify>
# or
# BackgroundEditorTp.pl -h
# Expects lines of the form:
# <series_instance_uid>&<op>&<tag>&<val1>&<val2>

# Lines specify the following things:
#  - Series edits:
#    An line with a value in series_instance_uid specifies a series to be edited.
#    Such a line is not allowed to have anything in the <operation>, <tag>,
#    <val1> or <val2> fields.  Generally, there will be some lines with values
#    in <series_instance_uid> followed by some lines with values in these other
#    fields.  The edits specified in lines following these series specifications
#    are specified in lines which have values in for <operation> and <tag>, and
#    may also have values in <val1> and <val2> (if the operation has parameters).
#    The first line with a value in series_instance_uid following a list of
#    operations resets the list of series (e.g.):
#      <series1>
#      <series2>
#                <op1> <tag1>
#                <op2> <tag2>
#      <series3>
#      <series4>
#                <op3> <tag3>

#       <op1> <tag1> and <op2> <tag2> are applied to <series1> and <series2>
#       <op3> <tag3> is applied to <series3> and <series4>

# Tags may be specified in any of the following ways (e.g):
#   (0010,0010) - specifies the tag (0010,0010) tag_mode "exact"
#   PatientName - Also specifies the tag (0010,0010) tag mode "exact",
#      using keyword from standard
#   Patient's Name - Also specifies the tag (0010,0010) tag mode "exact",
#      using name from standard
#   (0008,0008)[7] - Specifies the 8th item in the multi-valued tag (0008,0008)
#      tag_mode "item".
#      Note: you cant use tag names here.
#   (0054,0016)[<0>](0018,1079) - Identifies all (0018,1079) tags which occur
#      in any element of sequence contained in an (0054,0016) tag.
#      tag_mode "pattern".
#   (0054,0016)[0](0018,1079) - Identifies the (0018,1079) tag which occurs in
#      the zero-ith (aka the first) element of the (0054,0016) sequence
#      tag_mode "exact"
#   ..(0018,1079) - Identifies all (0018,1079) tags which occur anywhere,
#      either at root, or in any sequence.  tag_mode "exact"
#   (0013,"CTP",10) - Identifies the tag (0013,xx10) which occurs in a group
#      0013 in which (0013,0010) has the value "CTP ".
#      tag_mode "private"
#   (0013,1010) - Identifies the tag (0013,1010), which may also be (and usually
#      is) the tag identified by (0013,"CTP",10).  It is generally foolish to
#      count on this, but sometimes necessary to delve a little deeper
#      (perhaps you intend to create some erroneously encoded files?)
#      tag_mode "exact"
#      This is not currently supported in this version and will cause an error.
#      It may be suported in future versions, but has a serious conflict with
#      support for "private" tag modes and both modes may not be supported in a
#      single edit session.
#    Along these lines, tag patterns which specify exact private tags
#      eg "(00e1,1039)[<0>](0008,1110)[<1>](0008,1155)"
#      are considered abominations and flagged as errors.
#      patterns like:
#      '(00e1,"ELSCINT1",39)[<0>](0008,1110)[<1>](0008,1155)' are fine, as are
#      patterns like:
#      (00e1,"ELSCINT1",39)[<0>](0008,1110)[0](0008,1155), or
#      (00e1,"ELSCINT1",39)[0](0008,1110)[<0>](0008,1155)
#    Also, repeating tags (e.g. (60xx,0051)) are not supported.  They may
#       actually work if you enter the full tag value, but generally Posda support
#       for repeating tags is a little sketchy.
#    There is a horrible kludge to support deleting repeating blocks. A tag of one
#       of the following formats:
#       60xx
#       50xx
#       is allowed and specifies a tag_mode of "group_pattern" <op> must be
#       "delete_matching_group"
#    Another horrible kludge allows remapping private blocks (e.g):
#       0013
#       This is specifically to support the op move_owner_block ("CTP", "10") (note arg is hex string, not number)


# The contents of the fields <tag>, <value1>, and <value2> may by enclosed in
#   "meta-quotes" (i.e. "<(0010,0010)>" for "(0010,0010)".  This is to prevent
#   Excel from doing unnatural things to the values contained within.  If you
#   want to specify a value which is actually includes meta-quotes, you have
#   to double up the metaquotes. e.g."<<placeholder>>".  This script will strip
#   only one level of metaquotes. caveat usor.
#   Further complicating this, is an additional bit of extradorinary Excel
#   madness which causes it to be (sometimes) almost impossible to delete a
#   leading single quote in a cell. (I have no idea why or how they implemented
#   this, but it must have been hard).
#   So sometimes, metaquotes effectively look like "'<(0010,0010)>".
#   A lone single quote before the left metaquote will be deleted along with
#   the metaquotes.

# Edited files will be stored underneath the specified <dest_root> in the
# following hierarchy:
#   <dest_dir>/pat_<n>/study_<n1>/series_<n2>/<file_id>.dcm

# where "pat_<n>" (for some n) corresponds to a unique "from" patient (in posda),
# "study_<n1>" (for some n1) corresponds to a unique "from" study (in posda),
# "series_<n2>" (for some n2) corresponds to a unique "from" series (in posda),
# and "<file_id>" is the "from" file_id (in posda).  Since any of these may be
# changed in editing (they are usually, but not necessarily, changed consistently
# in the edits). Again caveat usor.

# As in all things, if you don't know what you are doing, you should:
#   1) Ask yourself why you are doing it, or
#   2) Ask someone to help, so you have some idea what you're doing, and
#   3) Be very careful doing it.
# I'm not sure about the whether the above is ((1 or 2) and 3) or
#   (1 or (2 and 3)) or whether it matters.

# On the other hand, this script can't do a lot of damage, all it does is create
# new files in the <dest_root> directory.  As long as you don't specify a really
# bad place to create these files, recovery from a bad run simply means deleting
# the bogus files you created.
# Edit operations currently supported:
#   shift_date(<tag>, <shift_count>)
#   shift_date_by_year(<tag>, <shift_count>)
#   copy_date_from_tag_to_dt(<tag>, <from_tag>)
#   copy_from_tag(<tag>, <from_tag>)
#   delete_tag(<tag>)
#   set_tag(<tag>, <value>)
#   substitute(<tag>, <existing_value>, <new_value>)
#   string_replace(<tag>, <old_text>, <new_text>)
#   empty_tag(<tag>)
#   short_hash(<tag>)
#   hash_unhashed_uid(<tag>, <uid_root>)
#   date_difference(<ref_tag>, <date>)

# This script uses the "NewSubprocessEditor.pl" as a subprocess to apply the
# edits in parallel to individual files.

# Maintainers:
# Be careful that the version of this file is compatable with the version of
# "NewSubprocessEditor.pl".  Why would it not be?  If you have changed one but
# not the other...
# """

from collections import defaultdict
import csv
from pprint import pprint
from pathlib import Path
import argparse
import pydicom

from .editor import Editor, Operation


def main(argv: list[str] | None = None) -> None:
    """CLI entrypoint: read CSV of edits and group them by Series Instance UID.

    Args:
        argv: Optional list of command-line arguments (for testing).
    """
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(prog="pydicom-background-editor")
    parser.add_argument("input", nargs="?", default="short.csv", help="Input CSV file with edits")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    required_fields = [
        "series_instance_uid",
        "op",
        "tag",
        "val1",
        "val2",
    ]

    with input_path.open("r", newline="") as infile:
        reader = csv.DictReader(infile)

        # make sure we have the required fields
        if reader.fieldnames is None:
            raise ValueError("Input file is missing field names")
        if not all(field in reader.fieldnames for field in required_fields):
            raise ValueError(f"Input file is missing one of the required fields: {required_fields}")

        # group edits into a dict by series_instance_uid
        edit_groups = defaultdict(list)
        for series, ops in generate_edit_groups(reader):
            for s in series:
                edit_groups[s].extend(ops)

        editor = Editor()
        ds = pydicom.dcmread("files/seg.dcm")
        for s, o in edit_groups.items():
            # print(s)
            # pprint(o)

            # first_op = o[0] # just for testing
            # editor.apply_edits(ds, [first_op])

            editor.apply_edits(ds, o)

            break

        ds.save_as("files/output.dcm")


def generate_edit_groups(reader):
    series_list = []
    op_list = []
    last_type = None
    for row in reader:
        if row["series_instance_uid"]:
            # if this is the end of a set
            if last_type == "op":
                yield series_list, op_list
                series_list = []
                op_list = []

            series_list.append(row["series_instance_uid"])
            last_type = "series"
        else:
            op_list.append(Operation.from_csv_row(row))
            last_type = "op"

    if series_list or op_list:
        yield series_list, op_list


if __name__ == "__main__":
    main()
