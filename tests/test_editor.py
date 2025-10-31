from pydicom_background_editor.path import parse, traverse
from pydicom_background_editor.editor import Operation, Editor

from dataset import make_test_dataset


def test_ds():
    ds = make_test_dataset()
    assert ds is not None


def test_strip_metaquotes():
    """Test that Operation._strip_metaquotes correctly removes angle brackets."""
    # Basic case
    assert Operation._strip_metaquotes("<value>") == "value"
    
    # Empty value
    assert Operation._strip_metaquotes("<>") == ""
    
    # No brackets
    assert Operation._strip_metaquotes("value") == "value"
    
    # Only one bracket
    assert Operation._strip_metaquotes("<value") == "<value"
    assert Operation._strip_metaquotes("value>") == "value>"
    
    # Empty string
    assert Operation._strip_metaquotes("") == ""
    
    # Excel quirk: leading single quote
    assert Operation._strip_metaquotes("'<value>") == "value"
    
    # Complex values
    assert Operation._strip_metaquotes("<1.3.6.1.4.1.14519.5.2.1>") == "1.3.6.1.4.1.14519.5.2.1"
    assert Operation._strip_metaquotes("<21113544>") == "21113544"


def test_from_csv_row_strips_metaquotes():
    """Test that Operation.from_csv_row strips metaquotes from val1 and val2."""
    row = {
        "op": "set_tag",
        "tag": '<(0010,0010)>',
        "val1": "<John Doe>",
        "val2": "<>",
    }
    
    op = Operation.from_csv_row(row)
    
    assert op.op == "set_tag"
    assert op.tag == '<(0010,0010)>'  # tag is not stripped
    assert op.val1 == "John Doe"  # brackets stripped
    assert op.val2 == ""  # brackets stripped, leaving empty string


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

    ele.element.value = "Some New Value"

    # now do a second lookup
    res = traverse(ds, parsed)

    ele, *none = res

    assert ele.element.value == "Some New Value"


def test_edit_2():
    ds = make_test_dataset()

    path = (
        "<(5200,9230)[<0>](0008,9124)[<0>](0008,2112)[<0>](0040,a170)[<0>](0008,0100)>"
    )

    parsed = parse(path)

    res = traverse(ds, parsed)

    assert len(res) == 1000
    assert res[0].element.value == "121322"

    for ele in res:
        ele.element.VR = "UI"
        ele.element.value = "122222"

    # test one of them
    path = "<(5200,9230)[0](0008,9124)[0](0008,2112)[4](0040,a170)[98](0008,0100)>"
    parsed = parse(path)
    res = traverse(ds, parsed)

    assert len(res) == 1
    assert res[0].element.value == "122222"
    assert res[0].element.VR == "UI"

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
    assert res[0].element.value == "1.2.999.99999.5.1.4.1.1.128"


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
        assert elem.element.value == "999322"  # "121322" -> "999322"


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
            tag="<(0004,1202)>",  # Non-existent tag
            val1="anything",
            val2="replacement",
        )
    ]

    # Should not raise an error
    editor.apply_edits(ds, operations)

    # Tag should still not exist
    res = traverse(ds, parse("<(0004,1202)>"))
    assert all(tag.element is None for tag in res)


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
    assert res[0].element.value == "TCIA-Real-Project"

def test_delete_tag_simple():
    """Test deleting an existing tag."""
    ds = make_test_dataset()
    editor = Editor()

    test_tag = "<(0008,0008)>"  # ImageType

    operations = [
        Operation(
            op="delete_tag",
            tag=test_tag,
            val1="",
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    # search for the deleted tag
    res = traverse(ds, parse(test_tag))
    assert all(tag.element is None for tag in res)

def test_delete_tag_wildcard():
    """Test deleting an existing tag."""
    ds = make_test_dataset()
    editor = Editor()

    test_tag = "<(5200,9230)[<0>](0008,9124)[<0>](0008,2112)[<0>](0040,a170)[<0>](0008,0100)>"

    operations = [
        Operation(
            op="delete_tag",
            tag=test_tag,
            val1="",
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    # search for the deleted tag
    res = traverse(ds, parse(test_tag))
    assert all(tag.element is None for tag in res)

def test_delete_tag_nonexistent():
    """Test deleting a non-existent tag."""
    ds = make_test_dataset()
    editor = Editor()

    test_tag = "<(0008,dead)>"

    operations = [
        Operation(
            op="delete_tag",
            tag=test_tag,
            val1="",
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    # search for the deleted tag
    res = traverse(ds, parse(test_tag))
    assert all(tag.element is None for tag in res)


def test_empty_tag_simple():
    """Test emptying an existing tag."""
    ds = make_test_dataset()
    editor = Editor()

    # Set up a tag with a known value
    ds.StudyInstanceUID = "1.3.6.1.4.1.14519.5.2.1.12345"

    operations = [
        Operation(
            op="empty_tag",
            tag="<(0020,000d)>",  # StudyInstanceUID
            val1="",
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    assert ds.StudyInstanceUID == ""


def test_empty_tag_nested_sequence():
    """Test emptying a tag in a nested sequence with concrete index."""
    ds = make_test_dataset()
    editor = Editor()

    # The nested path has value "1.2.840.10008.5.1.4.1.1.128"
    operations = [
        Operation(
            op="empty_tag",
            tag="<(0008,1115)[0](0008,114a)[0](0008,1150)>",
            val1="",
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    # Verify the tag was emptied
    res = traverse(ds, parse("<(0008,1115)[0](0008,114a)[0](0008,1150)>"))
    assert len(res) == 1
    assert res[0].element.value == ""


def test_empty_tag_wildcard():
    """Test emptying tags with wildcard traversal affecting multiple elements."""
    ds = make_test_dataset()
    editor = Editor()

    # Use wildcard to empty all matching elements
    operations = [
        Operation(
            op="empty_tag",
            tag="<(5200,9230)[<0>](0008,9124)[<0>](0008,2112)[<0>](0040,a170)[<0>](0008,0100)>",
            val1="",
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    # Check that all 1000 elements were emptied
    res = traverse(ds, parse("<(5200,9230)[<0>](0008,9124)[<0>](0008,2112)[<0>](0040,a170)[<0>](0008,0100)>"))
    assert len(res) == 1000
    for elem in res:
        assert elem.element.value == ""


def test_empty_tag_missing_creates():
    """Test that empty_tag creates the tag if it doesn't exist."""
    ds = make_test_dataset()
    editor = Editor()

    # Use a tag that doesn't exist in the dataset
    operations = [
        Operation(
            op="empty_tag",
            tag="<(0010,0030)>",  # PatientBirthDate - doesn't exist in test dataset
            val1="",
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    # Tag should now exist with empty value
    res = traverse(ds, parse("<(0010,0030)>"))
    assert len(res) == 1
    assert res[0].element is not None
    assert res[0].element.value == ""


def test_empty_tag_private():
    """Test emptying a private tag."""
    ds = make_test_dataset()
    editor = Editor()

    # Verify the tag has a value initially
    res_before = traverse(ds, parse('<(0013,"CTP",10)>'))
    assert len(res_before) == 1
    assert res_before[0].element.value == "TCIA-Fake-Project"

    operations = [
        Operation(
            op="empty_tag",
            tag='<(0013,"CTP",10)>',
            val1="",
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    res = traverse(ds, parse('<(0013,"CTP",10)>'))
    assert len(res) == 1
    assert res[0].element.value == ""


def test_substitute_simple_match():
    """Test substituting a value when it matches."""
    ds = make_test_dataset()
    editor = Editor()

    # Set up a tag with a known value
    ds.StudyInstanceUID = "1.3.6.1.4.1.14519.5.2.1.12345"

    operations = [
        Operation(
            op="substitute",
            tag="<(0020,000d)>",  # StudyInstanceUID
            val1="1.3.6.1.4.1.14519.5.2.1.12345",
            val2="9.9.9.9.9.9.9.9.9",
        )
    ]

    editor.apply_edits(ds, operations)

    assert ds.StudyInstanceUID == "9.9.9.9.9.9.9.9.9"


def test_substitute_simple_no_match():
    """Test that substitute doesn't change value when it doesn't match."""
    ds = make_test_dataset()
    editor = Editor()

    # Set up a tag with a known value
    ds.StudyInstanceUID = "1.3.6.1.4.1.14519.5.2.1.12345"
    original_value = ds.StudyInstanceUID

    operations = [
        Operation(
            op="substitute",
            tag="<(0020,000d)>",  # StudyInstanceUID
            val1="DIFFERENT_VALUE",
            val2="9.9.9.9.9.9.9.9.9",
        )
    ]

    editor.apply_edits(ds, operations)

    # Value should remain unchanged
    assert ds.StudyInstanceUID == original_value


def test_substitute_missing_tag():
    """Test that substitute handles missing tags gracefully (no error, no creation)."""
    ds = make_test_dataset()
    editor = Editor()

    # Use a tag that doesn't exist in the dataset
    operations = [
        Operation(
            op="substitute",
            tag="<(0010,0030)>",  # PatientBirthDate - doesn't exist
            val1="20000101",
            val2="20100101",
        )
    ]

    # Should not raise an error
    editor.apply_edits(ds, operations)

    # Tag should still not exist (unlike empty_tag or set_tag)
    res = traverse(ds, parse("<(0010,0030)>"))
    assert all(tag.element is None for tag in res)


def test_substitute_nested_sequence():
    """Test substituting a value in a nested sequence."""
    ds = make_test_dataset()
    editor = Editor()

    # The nested path has value "1.2.840.10008.5.1.4.1.1.128"
    operations = [
        Operation(
            op="substitute",
            tag="<(0008,1115)[0](0008,114a)[0](0008,1150)>",
            val1="1.2.840.10008.5.1.4.1.1.128",
            val2="9.9.9.9.9",
        )
    ]

    editor.apply_edits(ds, operations)

    # Verify the substitution
    res = traverse(ds, parse("<(0008,1115)[0](0008,114a)[0](0008,1150)>"))
    assert len(res) == 1
    assert res[0].element.value == "9.9.9.9.9"


def test_substitute_wildcard():
    """Test substituting with wildcard traversal affecting multiple elements."""
    ds = make_test_dataset()
    editor = Editor()

    # Use wildcard to substitute in all matching elements
    operations = [
        Operation(
            op="substitute",
            tag="<(5200,9230)[<0>](0008,9124)[<0>](0008,2112)[<0>](0040,a170)[<0>](0008,0100)>",
            val1="121322",
            val2="999999",
        )
    ]

    editor.apply_edits(ds, operations)

    # Check that all 1000 elements were modified
    res = traverse(ds, parse("<(5200,9230)[<0>](0008,9124)[<0>](0008,2112)[<0>](0040,a170)[<0>](0008,0100)>"))
    assert len(res) == 1000
    for elem in res:
        assert elem.element.value == "999999"


def test_substitute_wildcard_no_match():
    """Test that substitute with wildcard doesn't change non-matching values."""
    ds = make_test_dataset()
    editor = Editor()

    # Use wildcard but with a non-matching value
    operations = [
        Operation(
            op="substitute",
            tag="<(5200,9230)[<0>](0008,9124)[<0>](0008,2112)[<0>](0040,a170)[<0>](0008,0100)>",
            val1="NONEXISTENT",
            val2="999999",
        )
    ]

    editor.apply_edits(ds, operations)

    # Check that no elements were modified (all still have original value "121322")
    res = traverse(ds, parse("<(5200,9230)[<0>](0008,9124)[<0>](0008,2112)[<0>](0040,a170)[<0>](0008,0100)>"))
    assert len(res) == 1000
    for elem in res:
        assert elem.element.value == "121322"


def test_substitute_multi_valued():
    """Test that substitute works on multi-valued fields."""
    ds = make_test_dataset()
    editor = Editor()

    # ImageType is a multi-valued field (list) in pydicom
    # Original value from make_test_dataset() is ['ORIGINAL', 'PRIMARY', 'AXIAL']
    ds.ImageType = ['ORIGINAL', 'PRIMARY', 'ORIGINAL', 'AXIAL']

    operations = [
        Operation(
            op="substitute",
            tag="<(0008,0008)>",  # ImageType
            val1="ORIGINAL",
            val2="MODIFIED",
        )
    ]

    editor.apply_edits(ds, operations)

    # Both occurrences of ORIGINAL should be replaced
    assert ds.ImageType == ['MODIFIED', 'PRIMARY', 'MODIFIED', 'AXIAL']


def test_substitute_multi_valued_no_match():
    """Test that substitute on multi-valued field leaves non-matching values unchanged."""
    ds = make_test_dataset()
    editor = Editor()

    # Set up multi-valued field
    ds.ImageType = ['ORIGINAL', 'PRIMARY', 'AXIAL']
    original_value = list(ds.ImageType)

    operations = [
        Operation(
            op="substitute",
            tag="<(0008,0008)>",  # ImageType
            val1="NONEXISTENT",
            val2="MODIFIED",
        )
    ]

    editor.apply_edits(ds, operations)

    # No values should be changed
    assert list(ds.ImageType) == original_value


def test_substitute_private_tag():
    """Test substituting a value in a private tag."""
    ds = make_test_dataset()
    editor = Editor()

    operations = [
        Operation(
            op="substitute",
            tag='<(0013,"CTP",10)>',
            val1="TCIA-Fake-Project",
            val2="TCIA-Real-Project",
        )
    ]

    editor.apply_edits(ds, operations)

    res = traverse(ds, parse('<(0013,"CTP",10)>'))
    assert len(res) == 1
    assert res[0].element.value == "TCIA-Real-Project"


def test_substitute_private_tag_no_match():
    """Test that substitute on private tag doesn't change non-matching value."""
    ds = make_test_dataset()
    editor = Editor()

    operations = [
        Operation(
            op="substitute",
            tag='<(0013,"CTP",10)>',
            val1="WRONG_VALUE",
            val2="TCIA-Real-Project",
        )
    ]

    editor.apply_edits(ds, operations)

    res = traverse(ds, parse('<(0013,"CTP",10)>'))
    assert len(res) == 1
    assert res[0].element.value == "TCIA-Fake-Project"  # Unchanged


def test_shift_date_forward():
    """Test shifting a DA (Date) field forward by positive days."""
    ds = make_test_dataset()
    editor = Editor()

    # StudyDate is "20241030" (Oct 30, 2024)
    operations = [
        Operation(
            op="shift_date",
            tag="<(0008,0020)>",  # StudyDate (DA)
            val1="5",  # Shift forward 5 days
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    # Should be Nov 4, 2024
    assert ds.StudyDate == "20241104"


def test_shift_date_backward():
    """Test shifting a DA (Date) field backward by negative days."""
    ds = make_test_dataset()
    editor = Editor()

    # StudyDate is "20241030" (Oct 30, 2024)
    operations = [
        Operation(
            op="shift_date",
            tag="<(0008,0020)>",  # StudyDate (DA)
            val1="-10",  # Shift backward 10 days
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    # Should be Oct 20, 2024
    assert ds.StudyDate == "20241020"


def test_shift_date_datetime_field():
    """Test shifting a DT (DateTime) field preserves time portion."""
    ds = make_test_dataset()
    editor = Editor()

    # AcquisitionDateTime is "20241030143055.123456"
    operations = [
        Operation(
            op="shift_date",
            tag="<(0008,002a)>",  # AcquisitionDateTime (DT)
            val1="7",  # Shift forward 7 days
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    # Date should change, but time portion should remain the same
    # Should be Nov 6, 2024 at 14:30:55.123456
    assert ds.AcquisitionDateTime == "20241106143055.123456"


def test_shift_date_across_year_boundary():
    """Test shifting a date across year boundary."""
    ds = make_test_dataset()
    editor = Editor()

    # Set a date near year end
    ds.StudyDate = "20241225"  # Dec 25, 2024

    operations = [
        Operation(
            op="shift_date",
            tag="<(0008,0020)>",  # StudyDate (DA)
            val1="10",  # Shift forward 10 days
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    # Should be Jan 4, 2025
    assert ds.StudyDate == "20250104"


def test_shift_date_leap_year():
    """Test shifting across Feb 29 in leap year."""
    ds = make_test_dataset()
    editor = Editor()

    # 2024 is a leap year
    ds.StudyDate = "20240228"  # Feb 28, 2024

    operations = [
        Operation(
            op="shift_date",
            tag="<(0008,0020)>",  # StudyDate (DA)
            val1="2",  # Shift forward 2 days
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    # Should be Mar 1, 2024 (goes through Feb 29)
    assert ds.StudyDate == "20240301"


def test_shift_date_missing_tag():
    """Test that shift_date handles missing tags gracefully."""
    ds = make_test_dataset()
    editor = Editor()

    operations = [
        Operation(
            op="shift_date",
            tag="<(0010,0030)>",  # PatientBirthDate - doesn't exist
            val1="10",
            val2="",
        )
    ]

    # Should not raise an error
    editor.apply_edits(ds, operations)

    # Tag should still not exist
    res = traverse(ds, parse("<(0010,0030)>"))
    assert all(tag.element is None for tag in res)


def test_shift_date_non_date_vr():
    """Test that shift_date skips tags that are not date VRs."""
    ds = make_test_dataset()
    editor = Editor()

    original_value = ds.StudyInstanceUID

    operations = [
        Operation(
            op="shift_date",
            tag="<(0020,000d)>",  # StudyInstanceUID (UI, not DA or DT)
            val1="10",
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    # Value should remain unchanged
    assert ds.StudyInstanceUID == original_value


def test_shift_date_invalid_days():
    """Test that shift_date handles invalid day values gracefully."""
    ds = make_test_dataset()
    editor = Editor()

    original_value = ds.StudyDate

    operations = [
        Operation(
            op="shift_date",
            tag="<(0008,0020)>",  # StudyDate (DA)
            val1="invalid",  # Invalid number
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    # Value should remain unchanged
    assert ds.StudyDate == original_value


def test_shift_date_invalid_date_format():
    """Test that shift_date handles invalid date formats gracefully."""
    ds = make_test_dataset()
    editor = Editor()

    # Set an invalid date format; this will produce a warning from pydicom! it is expected
    ds.StudyDate = "INVALID"

    operations = [
        Operation(
            op="shift_date",
            tag="<(0008,0020)>",  # StudyDate (DA)
            val1="10",
            val2="",
        )
    ]

    # Should not raise an error
    editor.apply_edits(ds, operations)

    # Value should remain unchanged
    assert ds.StudyDate == "INVALID"


def test_shift_date_zero_days():
    """Test shifting by zero days (no change)."""
    ds = make_test_dataset()
    editor = Editor()

    original_value = ds.StudyDate

    operations = [
        Operation(
            op="shift_date",
            tag="<(0008,0020)>",  # StudyDate (DA)
            val1="0",
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    # Value should remain the same
    assert ds.StudyDate == original_value


def test_copy_from_tag_simple():
    """Test simple copy from one tag to another."""
    ds = make_test_dataset()
    editor = Editor()

    # Copy PatientName to another tag
    operations = [
        Operation(
            op="copy_from_tag",
            tag="<(0010,0020)>",  # PatientID (destination)
            val1="<(0010,0010)>",  # PatientName (source)
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    # PatientID should now have the value from PatientName
    assert ds.PatientID == ds.PatientName


def test_copy_from_tag_same_vr():
    """Test copying between tags with the same VR."""
    ds = make_test_dataset()
    editor = Editor()

    # Copy StudyDate to SeriesDate (both are DA)
    original_study_date = ds.StudyDate

    operations = [
        Operation(
            op="copy_from_tag",
            tag="<(0008,0021)>",  # SeriesDate (destination)
            val1="<(0008,0020)>",  # StudyDate (source)
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    assert ds.SeriesDate == original_study_date


def test_copy_from_tag_vr_conversion():
    """Test copying with VR conversion (UI to LO)."""
    ds = make_test_dataset()
    editor = Editor()

    # Copy StudyInstanceUID (UI) to a LO field
    operations = [
        Operation(
            op="copy_from_tag",
            tag="<(0010,0010)>",  # PatientName (LO) (destination)
            val1="<(0020,000d)>",  # StudyInstanceUID (UI) (source)
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    assert ds.PatientName == ds.StudyInstanceUID


def test_copy_from_tag_wildcard_source_first_match():
    """Test that wildcard in source uses first matching tag."""
    ds = make_test_dataset()
    editor = Editor()

    # Use wildcard in source - should take first match
    # The nested path has 1000 elements all with value "121322"
    operations = [
        Operation(
            op="copy_from_tag",
            tag="<(0010,0010)>",  # PatientName (destination)
            val1="<(5200,9230)[<0>](0008,9124)[<0>](0008,2112)[<0>](0040,a170)[<0>](0008,0100)>",
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    assert ds.PatientName == "121322"


def test_copy_from_tag_wildcard_dest_all_updated():
    """Test that wildcard in destination updates all matching tags."""
    ds = make_test_dataset()
    editor = Editor()

    # Set PatientName to a known value
    ds.PatientName = "TestValue"

    # Copy to all matching wildcard destinations
    operations = [
        Operation(
            op="copy_from_tag",
            tag="<(5200,9230)[<0>](0008,9124)[<0>](0008,2112)[<0>](0040,a170)[<0>](0008,0100)>",
            val1="<(0010,0010)>",  # PatientName (source)
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    # Check that all 1000 elements were updated
    res = traverse(ds, parse("<(5200,9230)[<0>](0008,9124)[<0>](0008,2112)[<0>](0040,a170)[<0>](0008,0100)>"))
    assert len(res) == 1000
    for elem in res:
        assert elem.element.value == "TestValue"


def test_copy_from_tag_missing_source():
    """Test that copy_from_tag handles missing source gracefully."""
    ds = make_test_dataset()
    editor = Editor()

    original_value = ds.PatientName

    operations = [
        Operation(
            op="copy_from_tag",
            tag="<(0010,0010)>",  # PatientName (destination)
            val1="<(0010,0030)>",  # PatientBirthDate (doesn't exist)
            val2="",
        )
    ]

    # Should not raise an error
    editor.apply_edits(ds, operations)

    # PatientName should remain unchanged
    assert ds.PatientName == original_value


def test_copy_from_tag_missing_dest_creates():
    """Test that copy_from_tag creates destination tag if it doesn't exist."""
    ds = make_test_dataset()
    editor = Editor()

    operations = [
        Operation(
            op="copy_from_tag",
            tag="<(0010,0030)>",  # PatientBirthDate (doesn't exist)
            val1="<(0008,0020)>",  # StudyDate (source)
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    # PatientBirthDate should now exist with StudyDate's value
    assert ds.PatientBirthDate == ds.StudyDate


def test_copy_from_tag_nested_sequence():
    """Test copying from nested sequence to top-level tag."""
    ds = make_test_dataset()
    editor = Editor()

    operations = [
        Operation(
            op="copy_from_tag",
            tag="<(0010,0010)>",  # PatientName (destination)
            val1="<(0008,1115)[0](0008,114a)[0](0008,1150)>",  # Nested UI
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    # Verify the copy
    res = traverse(ds, parse("<(0008,1115)[0](0008,114a)[0](0008,1150)>"))
    expected_value = res[0].element.value
    assert ds.PatientName == expected_value


def test_copy_from_tag_private_tag():
    """Test copying from a private tag."""
    ds = make_test_dataset()
    editor = Editor()

    operations = [
        Operation(
            op="copy_from_tag",
            tag="<(0010,0010)>",  # PatientName (destination)
            val1='<(0013,"CTP",10)>',  # Private tag (source)
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    res = traverse(ds, parse('<(0013,"CTP",10)>'))
    expected_value = res[0].element.value
    assert ds.PatientName == expected_value


def test_copy_from_tag_to_private_tag():
    """Test copying to a private tag."""
    ds = make_test_dataset()
    editor = Editor()

    ds.PatientName = "TestPatient"

    operations = [
        Operation(
            op="copy_from_tag",
            tag='<(0013,"CTP",11)>',  # Private tag (destination)
            val1="<(0010,0010)>",  # PatientName (source)
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    res = traverse(ds, parse('<(0013,"CTP",11)>'))
    assert res[0].element.value == "TestPatient"


def test_copy_from_tag_empty_source_val1():
    """Test that copy_from_tag handles empty val1 gracefully."""
    ds = make_test_dataset()
    editor = Editor()

    original_value = ds.PatientName

    operations = [
        Operation(
            op="copy_from_tag",
            tag="<(0010,0010)>",  # PatientName (destination)
            val1="",  # Empty source path
            val2="",
        )
    ]

    # Should not raise an error
    editor.apply_edits(ds, operations)

    # PatientName should remain unchanged
    assert ds.PatientName == original_value


def test_copy_from_tag_with_metaquotes():
    """Test that copy_from_tag handles meta-quoted source paths."""
    ds = make_test_dataset()
    editor = Editor()

    operations = [
        Operation(
            op="copy_from_tag",
            tag="<(0010,0020)>",  # PatientID (destination)
            val1="<(0010,0010)>",  # PatientName (source) - already has meta-quotes
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    assert ds.PatientID == ds.PatientName


def test_copy_from_tag_truncates_for_vr():
    """Test that long values are truncated to fit destination VR."""
    ds = make_test_dataset()
    editor = Editor()

    # Create a very long value (SH has max 16 chars)
    ds.StudyInstanceUID = "1.2.3.4.5.6.7.8.9.0.1.2.3.4.5.6.7.8.9.0"  # Much longer than SH allows

    operations = [
        Operation(
            op="copy_from_tag",
            tag="<(0008,0050)>",  # AccessionNumber (SH - max 16 chars) (destination)
            val1="<(0020,000d)>",  # StudyInstanceUID (source)
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    # Value should be truncated to 16 chars
    assert len(ds.AccessionNumber) <= 16


def test_hash_unhashed_uid_simple():
    """Test hashing a UID that doesn't start with the root."""
    ds = make_test_dataset()
    editor = Editor()

    original_uid = ds.StudyInstanceUID
    uid_root = "9.9.9"

    operations = [
        Operation(
            op="hash_unhashed_uid",
            tag="<(0020,000d)>",  # StudyInstanceUID
            val1=uid_root,
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    # UID should be changed and start with the root
    assert ds.StudyInstanceUID != original_uid
    assert ds.StudyInstanceUID.startswith(uid_root)


def test_hash_unhashed_uid_already_hashed():
    """Test that UIDs already starting with root are not re-hashed."""
    ds = make_test_dataset()
    editor = Editor()

    # Set UID to already have the root
    uid_root = "9.9.9"
    ds.StudyInstanceUID = f"{uid_root}.12345.67890"
    original_uid = ds.StudyInstanceUID

    operations = [
        Operation(
            op="hash_unhashed_uid",
            tag="<(0020,000d)>",  # StudyInstanceUID
            val1=uid_root,
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    # UID should remain unchanged
    assert ds.StudyInstanceUID == original_uid


def test_hash_unhashed_uid_empty_value():
    """Test that empty UIDs are not modified."""
    ds = make_test_dataset()
    editor = Editor()

    # Set UID to empty string
    ds.StudyInstanceUID = ""

    operations = [
        Operation(
            op="hash_unhashed_uid",
            tag="<(0020,000d)>",  # StudyInstanceUID
            val1="9.9.9",
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    # UID should remain empty
    assert ds.StudyInstanceUID == ""


def test_hash_unhashed_uid_wildcard():
    """Test hashing multiple UIDs with wildcard."""
    ds = make_test_dataset()
    editor = Editor()

    # The nested UIDs currently have value "1.2.840.10008.5.1.4.1.1.128"
    uid_root = "9.9.9"

    operations = [
        Operation(
            op="hash_unhashed_uid",
            tag="<(0008,1115)[<0>](0008,114a)[<0>](0008,1150)>",
            val1=uid_root,
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    # All matching UIDs should be hashed and start with root
    res = traverse(ds, parse("<(0008,1115)[<0>](0008,114a)[<0>](0008,1150)>"))
    assert len(res) == 100  # 100 items in the sequence
    for elem in res:
        assert elem.element.value.startswith(uid_root)
        assert elem.element.value != "1.2.840.10008.5.1.4.1.1.128"


def test_hash_unhashed_uid_mixed_already_hashed_and_unhashed():
    """Test with mix of already-hashed and unhashed UIDs."""
    ds = make_test_dataset()
    editor = Editor()

    uid_root = "9.9.9"
    
    # Set some UIDs to already be hashed, others not
    # We'll use the nested sequence - set first 50 to already hashed, rest unhashed
    res = traverse(ds, parse("<(0008,1115)[0](0008,114a)[<0>](0008,1150)>"))
    for i, elem in enumerate(res[:50]):
        elem.element.value = f"{uid_root}.1207885.{i}"
    
    # Store the first 50 "already hashed" values
    already_hashed_values = [elem.element.value for elem in res[:50]]

    operations = [
        Operation(
            op="hash_unhashed_uid",
            tag="<(0008,1115)[0](0008,114a)[<0>](0008,1150)>",
            val1=uid_root,
            val2="",
        )
    ]

    editor.apply_edits(ds, operations)

    # Check results
    res_after = traverse(ds, parse("<(0008,1115)[0](0008,114a)[<0>](0008,1150)>"))
    
    # First 50 should remain unchanged
    for i, elem in enumerate(res_after[:50]):
        assert elem.element.value == already_hashed_values[i]
    
    # Remaining should be hashed and start with root
    for elem in res_after[50:]:
        assert elem.element.value.startswith(uid_root)
        assert elem.element.value != "1.2.840.10008.5.1.4.1.1.128"


def test_hash_unhashed_uid_missing_tag():
    """Test that missing tags are handled gracefully."""
    ds = make_test_dataset()
    editor = Editor()

    operations = [
        Operation(
            op="hash_unhashed_uid",
            tag="<(0008,9999)>",  # Non-existent tag
            val1="9.9.9",
            val2="",
        )
    ]

    # Should not raise an error
    editor.apply_edits(ds, operations)

    # Tag should still not exist
    res = traverse(ds, parse("<(0008,9999)>"))
    assert all(tag.element is None for tag in res)


def test_hash_unhashed_uid_empty_root():
    """Test that empty uid_root is handled gracefully."""
    ds = make_test_dataset()
    editor = Editor()

    original_uid = ds.StudyInstanceUID

    operations = [
        Operation(
            op="hash_unhashed_uid",
            tag="<(0020,000d)>",  # StudyInstanceUID
            val1="",  # Empty uid_root
            val2="",
        )
    ]

    # Should not raise an error
    editor.apply_edits(ds, operations)

    # UID should remain unchanged
    assert ds.StudyInstanceUID == original_uid


def test_hash_unhashed_uid_idempotent():
    """Test that running hash_unhashed_uid twice produces same result."""
    ds = make_test_dataset()
    editor = Editor()

    uid_root = "9.9.9"

    operations = [
        Operation(
            op="hash_unhashed_uid",
            tag="<(0020,000d)>",  # StudyInstanceUID
            val1=uid_root,
            val2="",
        )
    ]

    # First hash
    editor.apply_edits(ds, operations)
    first_hash = ds.StudyInstanceUID

    # Second hash - should not change
    editor.apply_edits(ds, operations)
    second_hash = ds.StudyInstanceUID

    assert first_hash == second_hash
    assert first_hash.startswith(uid_root)