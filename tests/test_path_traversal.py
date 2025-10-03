from pydicom_background_editor.path import parse, traverse, Segment, Sequence, add_tag
from dataset import make_test_dataset
from pydicom.dataset import Dataset


def test_traverse_path_missing_initial_tag():
    """Tests traversing a path with a missing initial tag."""
    ds = make_test_dataset()

    path = "<(1234,0000)[90]>"
    parsed = parse(path)
    res = traverse(ds, parsed)
    assert len(res) == 0


def test_traverse_path_missing_seq():
    """Tests traversing a path with a missing sequence tag."""

    ds = make_test_dataset()
    path = "<(5200,9230)[325](0008,9124)[2](0008,2112)[0](0040,a170)[0](0008,0100)>"
    parsed = parse(path)
    res = traverse(ds, parsed)
    assert len(res) == 0


def test_traverse_path_missing_nested_tag():
    """Tests traversing a path with a missing nested tag."""

    ds = make_test_dataset()
    path = "<(5200,9230)[325](0008,9124)[0](0008,9999)[0](0040,a170)[0](0008,0100)>"
    parsed = parse(path)
    res = traverse(ds, parsed)
    assert len(res) == 0


def test_traverse_path_simple():
    ds = make_test_dataset()

    path = "<(5200,9230)[0](0008,9124)[0](0008,2112)[0](0040,a170)[0](0008,0100)>"

    parsed = parse(path)

    res = traverse(ds, parsed)

    assert len(res) == 1
    assert res[0].value == "121322"


def test_traverse_path_wild1():
    ds = make_test_dataset()

    path = "<(0008,1115)[<0>](0008,114a)[<0>](0008,1150)>"

    parsed = parse(path)

    res = traverse(ds, parsed)

    assert len(res) == 100
    assert res[0].value == "1.2.840.10008.5.1.4.1.1.128"


def test_traverse_path_wild2():
    ds = make_test_dataset()

    path = (
        "<(5200,9230)[<0>](0008,9124)[<1>](0008,2112)[<2>](0040,a170)[<3>](0008,0100)>"
    )

    parsed = parse(path)

    res = traverse(ds, parsed)

    assert len(res) == 1000
    assert res[0].value == "121322"


def test_traverse_private():
    ds = make_test_dataset()

    path = '<(0013,"CTP",11)>'

    parsed = parse(path)

    res = traverse(ds, parsed)

    assert len(res) == 1
    assert res[0].value == "TCIA-Fake-Site"


def test_traverse_private_nested():
    ds = make_test_dataset()

    # path = "<(6000,0010)>[<0>](0029,\"INTELERAD MEDICAL SYSTEMS\",21)>"
    path = '<(6000,0010)>[<0>](0029,"NEW CREATOR",21)>'

    parsed = parse(path)

    res = traverse(ds, parsed)

    assert len(res) == 2
    assert res[0].value == "PRIVATE_VALUE_21"


def test_add_tag_root():
    ds = make_test_dataset()

    path = "<(0008,1030)>"
    parsed_path = parse(path)

    add_tag(ds, parsed_path, "NEW VALUE")

    assert ds[0x0008, 0x1030].value == "NEW VALUE"

def test_add_tag_seq():
    ds = make_test_dataset()

    path = "<(5200,9230)[0](0008,1030)>"
    parsed_path = parse(path)

    add_tag(ds, parsed_path, "NEW VALUE", 'CS')

    assert ds[0x5200, 0x9230][0][0x0008, 0x1030].value == "NEW VALUE"
    assert ds[0x5200, 0x9230][0][0x0008, 0x1030].VR == "CS"

def test_add_tag_seq2():
    ds = make_test_dataset()

    path = "<(5200,9230)[0](0008,1030)>"
    parsed_path = parse(path)

    add_tag(ds, parsed_path, [Dataset()], 'SQ')


    assert ds[0x5200, 0x9230][0][0x0008, 0x1030].value == "NEW VALUE"
    assert ds[0x5200, 0x9230][0][0x0008, 0x1030].VR == "CS"