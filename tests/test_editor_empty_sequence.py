"""Test set_tag operation with empty sequences."""

from pydicom.dataset import Dataset
from pydicom.sequence import Sequence as PydicomSequence
from pydicom.tag import Tag

from pydicom_background_editor.editor import Operation, Editor


def test_set_tag_in_empty_sequence():
    """Test setting a tag inside an empty sequence item.
    
    This tests the fix for the issue where if a sequence item exists but is empty,
    traverse() returns an empty list and add_tag is never called.
    """
    # Create a dataset with a sequence containing an empty item
    ds = Dataset()
    
    # Add a sequence with one empty item
    empty_item = Dataset()
    seq = PydicomSequence([empty_item])
    ds.add_new(Tag(0x0008, 0x1110), 'SQ', seq)
    
    # Verify the sequence item is empty
    assert len(ds[0x0008, 0x1110].value[0]) == 0
    
    # Now try to set a tag inside that empty sequence item
    editor = Editor()
    operation = Operation(
        op="set_tag",
        tag="<(0008,1110)[0](0010,0010)>",
        val1="Test^Patient",
        val2=""
    )
    
    editor.apply_edits(ds, [operation])
    
    # Verify the tag was added to the previously empty sequence item
    assert ds[0x0008, 0x1110].value[0][0x0010, 0x0010].value == "Test^Patient"
    assert ds[0x0008, 0x1110].value[0][0x0010, 0x0010].VR == "PN"


def test_set_tag_in_nested_empty_sequence():
    """Test setting a tag inside a nested empty sequence item."""
    # Create a dataset with nested sequences where the innermost item is empty
    ds = Dataset()
    
    # First level: add a sequence with one item
    first_item = Dataset()
    
    # Second level: add a nested sequence with one empty item
    empty_item = Dataset()
    inner_seq = PydicomSequence([empty_item])
    first_item.add_new(Tag(0x0008, 0x1115), 'SQ', inner_seq)
    
    outer_seq = PydicomSequence([first_item])
    ds.add_new(Tag(0x0040, 0x0275), 'SQ', outer_seq)
    
    # Verify the innermost sequence item is empty
    assert len(ds[0x0040, 0x0275].value[0][0x0008, 0x1115].value[0]) == 0
    
    # Now try to set a tag inside that empty sequence item
    editor = Editor()
    operation = Operation(
        op="set_tag",
        tag="<(0040,0275)[0](0008,1115)[0](0008,1150)>",
        val1="1.2.840.10008.5.1.4.1.1.7",
        val2=""
    )
    
    editor.apply_edits(ds, [operation])
    
    # Verify the tag was added to the previously empty sequence item
    assert ds[0x0040, 0x0275].value[0][0x0008, 0x1115].value[0][0x0008, 0x1150].value == "1.2.840.10008.5.1.4.1.1.7"
    assert ds[0x0040, 0x0275].value[0][0x0008, 0x1115].value[0][0x0008, 0x1150].VR == "UI"


def test_set_tag_modifies_existing_not_empty():
    """Test that set_tag still works correctly when the tag already exists."""
    ds = Dataset()
    
    # Add a sequence with one item that has a tag
    item = Dataset()
    item.add_new(Tag(0x0010, 0x0010), 'PN', "Original^Name")
    seq = PydicomSequence([item])
    ds.add_new(Tag(0x0008, 0x1110), 'SQ', seq)
    
    # Verify the original value
    assert ds[0x0008, 0x1110].value[0][0x0010, 0x0010].value == "Original^Name"
    
    # Now modify that tag
    editor = Editor()
    operation = Operation(
        op="set_tag",
        tag="<(0008,1110)[0](0010,0010)>",
        val1="Modified^Name",
        val2=""
    )
    
    editor.apply_edits(ds, [operation])
    
    # Verify the tag was modified
    assert ds[0x0008, 0x1110].value[0][0x0010, 0x0010].value == "Modified^Name"
    assert ds[0x0008, 0x1110].value[0][0x0010, 0x0010].VR == "PN"


def test_set_tag_multiple_empty_items_with_wildcard():
    """Test setting tags in multiple empty sequence items using wildcard."""
    ds = Dataset()
    
    # Add a sequence with three empty items
    empty_item1 = Dataset()
    empty_item2 = Dataset()
    empty_item3 = Dataset()
    seq = PydicomSequence([empty_item1, empty_item2, empty_item3])
    ds.add_new(Tag(0x0008, 0x1110), 'SQ', seq)
    
    # Verify all items are empty
    assert len(ds[0x0008, 0x1110].value[0]) == 0
    assert len(ds[0x0008, 0x1110].value[1]) == 0
    assert len(ds[0x0008, 0x1110].value[2]) == 0
    
    # Now try to set a tag in all items using wildcard
    editor = Editor()
    operation = Operation(
        op="set_tag",
        tag="<(0008,1110)[<0>](0008,1155)>",
        val1="1.2.840.10008.5.1.4.1.1.1",
        val2=""
    )
    
    editor.apply_edits(ds, [operation])
    
    # Verify the tag was added to all three previously empty sequence items
    assert ds[0x0008, 0x1110].value[0][0x0008, 0x1155].value == "1.2.840.10008.5.1.4.1.1.1"
    assert ds[0x0008, 0x1110].value[1][0x0008, 0x1155].value == "1.2.840.10008.5.1.4.1.1.1"
    assert ds[0x0008, 0x1110].value[2][0x0008, 0x1155].value == "1.2.840.10008.5.1.4.1.1.1"
    assert ds[0x0008, 0x1110].value[0][0x0008, 0x1155].VR == "UI"
