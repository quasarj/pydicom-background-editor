from pydicom_background_editor.path import parse, traverse
from pydicom_background_editor.editor import Operation, Editor

from dataset import make_test_dataset


def test_ds():
    ds = make_test_dataset()
    assert ds is not None


def test_things():
    ds = make_test_dataset()
    res = traverse(ds, parse("<(6001,0010)[0]>"))
    print(res)

def test_editor_1():
    ds = make_test_dataset()
    editor = Editor()

    # define some example operations
    operations = [
        Operation(op="set_tag", tag="<(0010,0010)>", val1="John Doe", val2=""),
        Operation(op="set_tag", tag="<(0010,0020)>", val1="123456", val2=""),
    ]

    editor.apply_edits(ds, operations)

    assert ds[0x0010, 0x0010].value == "John Doe"
    assert ds[0x0010, 0x0020].value == "123456"

def test_edit():
    ds = make_test_dataset()

    path = '<(0013,"CTP",11)>'

    parsed = parse(path)

    res = traverse(ds, parsed)

    ele, *none = res

    ele.value = "Some New Value"

    # now do a second lookup
    res = traverse(ds, parsed)

    ele, *none = res

    assert ele.value == "Some New Value"


def test_edit_2():
    ds = make_test_dataset()

    path = (
        "<(5200,9230)[<0>](0008,9124)[<0>](0008,2112)[<0>](0040,a170)[<0>](0008,0100)>"
    )

    parsed = parse(path)

    res = traverse(ds, parsed)

    assert len(res) == 1000
    assert res[0].value == "121322"

    for ele in res:
        ele.VR = "UI"
        ele.value = "122222"

    # test one of them
    path = "<(5200,9230)[0](0008,9124)[0](0008,2112)[4](0040,a170)[98](0008,0100)>"
    parsed = parse(path)
    res = traverse(ds, parsed)

    assert len(res) == 1
    assert res[0].value == "122222"
    assert res[0].VR == "UI"
