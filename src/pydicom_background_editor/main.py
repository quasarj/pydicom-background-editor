"""
Background Editor using pydicom
"""

import sys
import logging
from collections import defaultdict
import csv
from pprint import pprint
from pathlib import Path
import argparse
import pydicom

from .editor import Editor, Operation
from .input import get_input_data, respond_ok, respond_error

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def parse_args():
    parser = argparse.ArgumentParser(prog="pydicom-background-editor", description=__doc__)
    parser.add_argument("input", nargs="?", default="very_simple_real.csv", help="Input CSV file with edits")
    parser.add_argument("activity_id", help="the activity to run against")
    args = parser.parse_args()

    return args

def main_old() -> None:
    """CLI entrypoint: read CSV of edits and group them by Series Instance UID.
    """
    args = parse_args()

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

        ## TODO: temp list for testing, this is a pathology file
        files = [
            "/Users/quasar/Documents/DICOM/pathology/a3e6a5cc1bfbeda4bb229fa728486259",
        ]
        ds = pydicom.dcmread(files[0], defer_size=1024)

        for s, o in edit_groups.items():
            # print(s)
            # pprint(o)

            # first_op = o[0] # just for testing
            # editor.apply_edits(ds, [first_op])

            editor.apply_edits(ds, o)

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

def test2():
    files = [
        "/Users/quasar/Documents/DICOM/pathology/a3e6a5cc1bfbeda4bb229fa728486259",
    ]

    for file in files:
        ds = pydicom.dcmread(file, stop_before_pixels=True)
        pprint(ds)

def get_input_data_test():
    ## example/fake data that would be read from stdin storable
    data = {
        "edits": [
            {
                "arg1": "",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)",
                "tag_mode": "exact"
            },
            {
                "arg1": "113100",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[0](0008,0100)",
                "tag_mode": "exact"
            },
            {
                "arg1": "DCM",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[0](0008,0102)",
                "tag_mode": "exact"
            },
            {
                "arg1": "Basic Application Confidentiality Profile",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[0](0008,0104)",
                "tag_mode": "exact"
            },
            {
                "arg1": "113101",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[1](0008,0100)",
                "tag_mode": "exact"
            },
            {
                "arg1": "DCM",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[1](0008,0102)",
                "tag_mode": "exact"
            },
            {
                "arg1": "Clean Pixel Data Option",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[1](0008,0104)",
                "tag_mode": "exact"
            },
            {
                "arg1": "113104",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[2](0008,0100)",
                "tag_mode": "exact"
            },
            {
                "arg1": "DCM",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[2](0008,0102)",
                "tag_mode": "exact"
            },
            {
                "arg1": "Clean Structured Content Option",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[2](0008,0104)",
                "tag_mode": "exact"
            },
            {
                "arg1": "113105",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[3](0008,0100)",
                "tag_mode": "exact"
            },
            {
                "arg1": "DCM",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[3](0008,0102)",
                "tag_mode": "exact"
            },
            {
                "arg1": "Clean Descriptors Option",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[3](0008,0104)",
                "tag_mode": "exact"
            },
            {
                "arg1": "113107",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[4](0008,0100)",
                "tag_mode": "exact"
            },
            {
                "arg1": "DCM",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[4](0008,0102)",
                "tag_mode": "exact"
            },
            {
                "arg1": "Retain Longitudinal Temporal Information Modified Dates Option",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[4](0008,0104)",
                "tag_mode": "exact"
            },
            {
                "arg1": "113108",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[5](0008,0100)",
                "tag_mode": "exact"
            },
            {
                "arg1": "DCM",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[5](0008,0102)",
                "tag_mode": "exact"
            },
            {
                "arg1": "Retain Patient Characteristics Option",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[5](0008,0104)",
                "tag_mode": "exact"
            },
            {
                "arg1": "113109",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[6](0008,0100)",
                "tag_mode": "exact"
            },
            {
                "arg1": "DCM",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[6](0008,0102)",
                "tag_mode": "exact"
            },
            {
                "arg1": "Retain Device Identity Option",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[6](0008,0104)",
                "tag_mode": "exact"
            },
            {
                "arg1": "113111",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[7](0008,0100)",
                "tag_mode": "exact"
            },
            {
                "arg1": "DCM",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[7](0008,0102)",
                "tag_mode": "exact"
            },
            {
                "arg1": "Retain Safe Private Option",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[7](0008,0104)",
                "tag_mode": "exact"
            }
        ],
        "from_file": "/nas/new/public/posda/storage/e4/d7/69/e4d769e6bc213ee9c78148ff5c7e7f29",
        "to_file": "/nas/public/posda/cache2/edits/be82335e-d182-11f0-a69a-15f97ed50320/pat_148/studies/series_1252/201382653.dcm"
    }

    return data
    
def test():
    data = get_input_data()
    
    # from_file = data["from_file"]
    # to_file = data["to_file"]
    from_file = "/Users/quasar/Documents/DICOM/pathology/a3e6a5cc1bfbeda4bb229fa728486259"
    to_file = "./out.dcm"
    editor = Editor()

    raw_edits = data["edits"]
    operations = Operation.translate_edits(raw_edits)

    ds = pydicom.dcmread(from_file, defer_size=1024)
    editor.apply_edits(ds, operations)
    ds.save_as(to_file)

    # print(ds)

def main() -> None:

    if sys.argv[1:]:
        print(__doc__)
        sys.exit(1)

    # print("Testing input from stdin, in storable format. Waiting up to 15 seconds to get data...")
    edits = get_input_data()
    # print("Raw edits:")
    # pprint(edits)

    operations = Operation.translate_edits(edits["edits"])
    from_file = edits["from_file"]
    to_file = edits["to_file"]

    editor = Editor()

    # print("Edits translated to Operations:")
    # pprint(operations)

    print("Editing begins now...")
    ds = pydicom.dcmread(from_file, defer_size=1024)
    editor.apply_edits(ds, operations)
    ds.save_as(to_file)

    respond_ok({
        "to_file": to_file,
        "from_file": from_file,
    })


if __name__ == "__main__":
    # main()
    test()
