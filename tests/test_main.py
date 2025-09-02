import io
import csv
import pydicom
import pytest
import pydicom_background_editor
from pydicom_background_editor.main import parse_path, traverse_path, Segment, Sequence
from pprint import pprint
from functools import lru_cache

TEST_FILE = "files/6a1951dcd38e55e542304c26b0f18379"

@lru_cache(maxsize=1)
def get_ds():
    return pydicom.dcmread(TEST_FILE)

def test_parse_path_simple_segment():
    """Test parsing of a simple DICOM path segment."""
    simple_path_segment = "<(0008,1110)>"
    parsed = parse_path(simple_path_segment)

    assert len(parsed) == 1
    seg = parsed[0]
    assert isinstance(seg, Segment)
    assert seg.tag == '0008,1110'
    assert seg.group == 0x0008
    assert seg.element == 0x1110

    # simple path
    # path = "<(0008,1110)[1]>"
    # path = "<(0008,1110)[<0>]>"
    # path = "<(0008,1110)[<0>](0008,1155)>"
    # path = "<(0008,1110)[3](0008,1155)[<1>](0008,1125)[<2>](0023,0010)>"
    # path = "<(5200,9230)[<0>](0062,000A)[0](0062,000B)>"

def test_parse_path_concrete_index():
    """Tests parsing of a DICOM path segment with a concrete index."""
    element = "<(0008,1110)[1]>"
    parsed = parse_path(element)

    assert len(parsed) == 2
    one, two = parsed
    
    assert isinstance(one, Segment)
    assert one.tag == '0008,1110'
    assert one.group == 0x0008
    assert one.element == 0x1110

    assert isinstance(two, Sequence)
    assert two.value == 1
    assert two.wildcard == False

    
def test_parse_path_private_simple():
    """Tests parsing of a simple private path element"""

    element = '<(0029,"INTELERAD MEDICAL SYSTEMS",20)>'
    parsed = parse_path(element)

    assert len(parsed) == 1
    seg = parsed[0]
    assert isinstance(seg, Segment)

    assert seg.is_private == True
    assert seg.tag == '0029,"INTELERAD MEDICAL SYSTEMS",20'
    assert seg.group == 0x0029
    assert seg.owner == "INTELERAD MEDICAL SYSTEMS"
    assert seg.element == 0x20


def dont_test_path_index():
    ds = get_ds()

    path = "<(0008,1110)[1]>"



    parsed = parse_path(path)

    res = traverse_path(ds, parsed)

    print(res)

    # for tag in res:
    #     tag.value = 7
    #     print(tag.value) 

    # ds.save_as("out.dcm")

    def test_another():
        assert 1 == 1