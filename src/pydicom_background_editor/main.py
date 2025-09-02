"""
From the original background editor help:

Usage:
BackgroundEditorTp.pl <?bkgrnd_id?> <activity_id> "<edit_desciption>" <notify>
or
BackgroundEditorTp.pl -h
Expects lines of the form:
<series_instance_uid>&<op>&<tag>&<val1>&<val2>

Lines specify the following things:
 - Series edits:
   An line with a value in series_instance_uid specifies a series to be edited.
   Such a line is not allowed to have anything in the <operation>, <tag>,
   <val1> or <val2> fields.  Generally, there will be some lines with values
   in <series_instance_uid> followed by some lines with values in these other
   fields.  The edits specified in lines following these series specifications
   are specified in lines which have values in for <operation> and <tag>, and
   may also have values in <val1> and <val2> (if the operation has parameters).
   The first line with a value in series_instance_uid following a list of
   operations resets the list of series (e.g.):
     <series1>
     <series2>
               <op1> <tag1>
               <op2> <tag2>
     <series3>
     <series4>
               <op3> <tag3>

      <op1> <tag1> and <op2> <tag2> are applied to <series1> and <series2>
      <op3> <tag3> is applied to <series3> and <series4>

Tags may be specified in any of the following ways (e.g):
  (0010,0010) - specifies the tag (0010,0010) tag_mode "exact"
  PatientName - Also specifies the tag (0010,0010) tag mode "exact",
     using keyword from standard
  Patient's Name - Also specifies the tag (0010,0010) tag mode "exact",
     using name from standard
  (0008,0008)[7] - Specifies the 8th item in the multi-valued tag (0008,0008)
     tag_mode "item".
     Note: you cant use tag names here.
  (0054,0016)[<0>](0018,1079) - Identifies all (0018,1079) tags which occur
     in any element of sequence contained in an (0054,0016) tag.
     tag_mode "pattern".
  (0054,0016)[0](0018,1079) - Identifies the (0018,1079) tag which occurs in
     the zero-ith (aka the first) element of the (0054,0016) sequence
     tag_mode "exact"
  ..(0018,1079) - Identifies all (0018,1079) tags which occur anywhere,
     either at root, or in any sequence.  tag_mode "exact"
  (0013,"CTP",10) - Identifies the tag (0013,xx10) which occurs in a group
     0013 in which (0013,0010) has the value "CTP ".
     tag_mode "private"
  (0013,1010) - Identifies the tag (0013,1010), which may also be (and usually
     is) the tag identified by (0013,"CTP",10).  It is generally foolish to
     count on this, but sometimes necessary to delve a little deeper
     (perhaps you intend to create some erroneously encoded files?)
     tag_mode "exact"
     This is not currently supported in this version and will cause an error.
     It may be suported in future versions, but has a serious conflict with
     support for "private" tag modes and both modes may not be supported in a
     single edit session.
   Along these lines, tag patterns which specify exact private tags
     eg "(00e1,1039)[<0>](0008,1110)[<1>](0008,1155)"
     are considered abominations and flagged as errors.
     patterns like:
     '(00e1,"ELSCINT1",39)[<0>](0008,1110)[<1>](0008,1155)' are fine, as are
     patterns like:
     (00e1,"ELSCINT1",39)[<0>](0008,1110)[0](0008,1155), or
     (00e1,"ELSCINT1",39)[0](0008,1110)[<0>](0008,1155)
   Also, repeating tags (e.g. (60xx,0051)) are not supported.  They may
      actually work if you enter the full tag value, but generally Posda support
      for repeating tags is a little sketchy.
   There is a horrible kludge to support deleting repeating blocks. A tag of one
      of the following formats:
      60xx
      50xx
      is allowed and specifies a tag_mode of "group_pattern" <op> must be
      "delete_matching_group"
   Another horrible kludge allows remapping private blocks (e.g):
      0013
      This is specifically to support the op move_owner_block ("CTP", "10") (note arg is hex string, not number)


The contents of the fields <tag>, <value1>, and <value2> may by enclosed in
  "meta-quotes" (i.e. "<(0010,0010)>" for "(0010,0010)".  This is to prevent
  Excel from doing unnatural things to the values contained within.  If you
  want to specify a value which is actually includes meta-quotes, you have
  to double up the metaquotes. e.g."<<placeholder>>".  This script will strip
  only one level of metaquotes. caveat usor.
  Further complicating this, is an additional bit of extradorinary Excel
  madness which causes it to be (sometimes) almost impossible to delete a
  leading single quote in a cell. (I have no idea why or how they implemented
  this, but it must have been hard).
  So sometimes, metaquotes effectively look like "'<(0010,0010)>".
  A lone single quote before the left metaquote will be deleted along with
  the metaquotes.

Edited files will be stored underneath the specified <dest_root> in the
following hierarchy:
  <dest_dir>/pat_<n>/study_<n1>/series_<n2>/<file_id>.dcm

where "pat_<n>" (for some n) corresponds to a unique "from" patient (in posda),
"study_<n1>" (for some n1) corresponds to a unique "from" study (in posda),
"series_<n2>" (for some n2) corresponds to a unique "from" series (in posda),
and "<file_id>" is the "from" file_id (in posda).  Since any of these may be
changed in editing (they are usually, but not necessarily, changed consistently
in the edits). Again caveat usor.

As in all things, if you don't know what you are doing, you should:
  1) Ask yourself why you are doing it, or
  2) Ask someone to help, so you have some idea what you're doing, and
  3) Be very careful doing it.
I'm not sure about the whether the above is ((1 or 2) and 3) or
  (1 or (2 and 3)) or whether it matters.

On the other hand, this script can't do a lot of damage, all it does is create
new files in the <dest_root> directory.  As long as you don't specify a really
bad place to create these files, recovery from a bad run simply means deleting
the bogus files you created.
Edit operations currently supported:
  shift_date(<tag>, <shift_count>)
  shift_date_by_year(<tag>, <shift_count>)
  copy_date_from_tag_to_dt(<tag>, <from_tag>)
  copy_from_tag(<tag>, <from_tag>)
  delete_tag(<tag>)
  set_tag(<tag>, <value>)
  substitute(<tag>, <existing_value>, <new_value>)
  string_replace(<tag>, <old_text>, <new_text>)
  empty_tag(<tag>)
  short_hash(<tag>)
  hash_unhashed_uid(<tag>, <uid_root>)
  date_difference(<ref_tag>, <date>)

This script uses the "NewSubprocessEditor.pl" as a subprocess to apply the
edits in parallel to individual files.

Maintainers:
Be careful that the version of this file is compatable with the version of
"NewSubprocessEditor.pl".  Why would it not be?  If you have changed one but
not the other...
"""

from collections import defaultdict
import pydicom
import re
import dataclasses
import csv
from pprint import pprint

@dataclasses.dataclass
class Segment():
    tag: str
    group: int
    element: int
    is_private: bool = False
    owner: str | None = None

    def __init__(self, tag: str):
        self.tag = tag

        if '"' in tag:
            self.is_private = True
            group, self.owner, ele = tag.split('"')

            group = group.strip(",")
            ele = ele.strip(",")
        else:
            group, ele = tag.split(",")

        self.group = int(group, 16)
        self.element = int(ele, 16)

@dataclasses.dataclass
class Sequence():
    value: int
    wildcard: bool

    def __init__(self, value: str):
        if value.startswith("<") and value.endswith(">"):
            self.wildcard = True
            self.value = int(value.strip("<>"))
        else:
            self.wildcard = False
            self.value = int(value)

@dataclasses.dataclass
class Operation():
    op: str
    tag: str
    val1: str
    val2: str

    @staticmethod
    def from_csv_row(row: dict) -> "Operation":
        return Operation(
            op=row["op"],
            tag=row["tag"],
            val1=row["val1"],
            val2=row["val2"],
        )

def parse_path(path):
    if not (path.startswith("<") and path.endswith(">")):
        raise ValueError("Path is missing Bills; it looks invalid")

    path = path.strip("<>")

    # Match the entire path; this should break it into a set of matches
    # for each component in the path
    # This regex matches either:
    # - A group of digits inside parentheses (e.g. (0008,1110))
    # - A group of digits inside square brackets (e.g. [<0>], or [2])
    regex = r"\(([^)]+)\)|\[(<[^>]+>|[^\]]+)\]"

    matches = re.findall(regex, path)

    output = []
    for segment, sequence in matches:
        if segment:
            s = Segment(segment)
            output.append(s)
        if sequence:
            s = Sequence(sequence)
            output.append(s)

    return output

def traverse_path(ds, parsed_path):
    """
    Traverse a path and return the matching elements
    
    TODO: this may need to be expanded to handle Multivalue items
    the same way Posda does - I _think_ they can be referenced
    the same way as DICOM Sequences?
    """
    if len(parsed_path) == 0:
        return [ds]

    item, *remaning_path = parsed_path

    if isinstance(item, Segment):
        # Traverse the DICOM dataset using the segment
        ds = ds.get((item.group, item.element))
        return traverse_path(ds, remaning_path)

    elif isinstance(item, Sequence):
        # Handle sequences
        seq = ds.value # get the actual pydicom Sequence object
        seq_length = len(seq)

        if not item.wildcard:
            # Exact index
            exact_index = int(item.value)
            if exact_index >= seq_length:
                return []
            ds = seq[exact_index]
            return traverse_path(ds, remaning_path)
        else:
            # wildcard index, we have to recurse for each entry
            ret = []
            for i in range(seq_length):
                x = traverse_path(seq[i], remaning_path)
                # print(">>", x)
                ret.extend(x)
            return ret


def main():
    required_fields = [
        'series_instance_uid',
        'op',
        'tag',
        'val1',
        'val2',
    ]
    # input_filename = "background_editor_example_input2.csv"
    input_filename = "short.csv"
    with open(input_filename) as infile:
        reader = csv.DictReader(infile)

        # make sure we have the required fields
        if not all(field in reader.fieldnames for field in required_fields):
            raise ValueError(f"Input file is missing one of the required fields: {required_fields}")

        # group edits into a dict by series_instance_uid
        edit_groups = defaultdict(list)
        for series, ops in generate_edit_groups(reader):
            for s in series:
                edit_groups[s].extend(ops)

        for s, o in edit_groups.items():
            print(s)
            pprint(o)

def generate_edit_groups(reader):
        series_list = []
        op_list = []
        last_type = None
        for row in reader:
            if row['series_instance_uid']:
                # if this is the end of a set
                if last_type == 'op':
                    yield series_list, op_list
                    series_list = []
                    op_list = []

                series_list.append(row['series_instance_uid'])
                last_type = 'series'
            else:
                op_list.append(Operation.from_csv_row(row))
                last_type = 'op'

        if series_list or op_list:
            yield series_list, op_list

if __name__ == "__main__":
    main()
