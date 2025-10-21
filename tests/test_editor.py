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


def test_string_replace_simple():
    """Test basic string replacement on a simple tag."""
    ds = make_test_dataset()
    editor = Editor()

    # Set up a tag with a known value
    ds.StudyInstanceUID = "1.3.6.1.4.1.14519.5.2.1.12345"

    operations = [
        Operation(
            op="string_replace",
            tag="<(0020,000d)>",  # StudyInstanceUID
            val1="1.3.6.1.4.1.14519.5.2.1",
            val2="1.3.6.1.4.1.14519.5.2.1.2111.3544",
        )
    ]

    editor.apply_edits(ds, operations)

    assert ds.StudyInstanceUID == "1.3.6.1.4.1.14519.5.2.1.2111.3544.12345"


def test_string_replace_nested_sequence():
    """Test string replacement in a nested sequence with concrete index."""
    ds = make_test_dataset()
    editor = Editor()

    # The nested path has value "1.2.840.10008.5.1.4.1.1.128"
    operations = [
        Operation(
            op="string_replace",
            tag="<(0008,1115)[0](0008,114a)[0](0008,1150)>",
            val1="1.2.840.10008",
            val2="1.2.999.99999",
        )
    ]

    editor.apply_edits(ds, operations)

    # Verify the replacement
    res = traverse(ds, parse("<(0008,1115)[0](0008,114a)[0](0008,1150)>"))
    assert len(res) == 1
    assert res[0].value == "1.2.999.99999.5.1.4.1.1.128"


def test_string_replace_wildcard():
    """Test string replacement with wildcard traversal affecting multiple elements."""
    ds = make_test_dataset()
    editor = Editor()

    # Use wildcard to replace in all matching elements
    operations = [
        Operation(
            op="string_replace",
            tag="<(5200,9230)[<0>](0008,9124)[<0>](0008,2112)[<0>](0040,a170)[<0>](0008,0100)>",
            val1="121",
            val2="999",
        )
    ]

    editor.apply_edits(ds, operations)

    # Check that all 1000 elements were modified
    res = traverse(ds, parse("<(5200,9230)[<0>](0008,9124)[<0>](0008,2112)[<0>](0040,a170)[<0>](0008,0100)>"))
    assert len(res) == 1000
    for elem in res:
        assert elem.value == "999322"  # "121322" -> "999322"


def test_string_replace_no_match():
    """Test string replacement when the search string is not found."""
    ds = make_test_dataset()
    editor = Editor()

    original_value = ds.StudyInstanceUID

    operations = [
        Operation(
            op="string_replace",
            tag="<(0020,000d)>",
            val1="NONEXISTENT",
            val2="REPLACEMENT",
        )
    ]

    editor.apply_edits(ds, operations)

    # Value should remain unchanged
    assert ds.StudyInstanceUID == original_value


def test_string_replace_missing_tag():
    """Test that string_replace handles missing tags gracefully (no error)."""
    ds = make_test_dataset()
    editor = Editor()

    # Use a tag that doesn't exist in the dataset
    operations = [
        Operation(
            op="string_replace",
            tag="<(0099,9999)>",  # Non-existent tag
            val1="anything",
            val2="replacement",
        )
    ]

    # Should not raise an error
    editor.apply_edits(ds, operations)

    # Tag should still not exist
    res = traverse(ds, parse("<(0099,9999)>"))
    assert all(tag is None for tag in res)


def test_string_replace_multiple_occurrences():
    """Test that string_replace replaces all occurrences in a multi-valued field."""
    ds = make_test_dataset()
    editor = Editor()

    # ImageType is a multi-valued field (list) in pydicom
    # Original value from make_test_dataset() is ['ORIGINAL', 'PRIMARY', 'AXIAL']
    # Let's modify it to have multiple occurrences of ORIGINAL
    ds.ImageType = ['ORIGINAL', 'PRIMARY', 'ORIGINAL', 'AXIAL']

    operations = [
        Operation(
            op="string_replace",
            tag="<(0008,0008)>",  # ImageType
            val1="ORIGINAL",
            val2="MODIFIED",
        )
    ]

    editor.apply_edits(ds, operations)

    # Both occurrences of ORIGINAL should be replaced
    assert ds.ImageType == ['MODIFIED', 'PRIMARY', 'MODIFIED', 'AXIAL']


def test_string_replace_private_tag():
    """Test string replacement on a private tag."""
    ds = make_test_dataset()
    editor = Editor()

    operations = [
        Operation(
            op="string_replace",
            tag='<(0013,"CTP",10)>',
            val1="TCIA-Fake",
            val2="TCIA-Real",
        )
    ]

    editor.apply_edits(ds, operations)

    res = traverse(ds, parse('<(0013,"CTP",10)>'))
    assert len(res) == 1
    assert res[0].value == "TCIA-Real-Project"
