"""Test sequence creation and population with Operations."""

from pydicom.dataset import Dataset
from pydicom.sequence import Sequence as PydicomSequence
from pydicom.tag import Tag

from pydicom_background_editor.editor import Operation, Editor


def test_create_sequence_by_setting_nested_tag():
    """Test that setting a tag inside a non-existent sequence creates the sequence."""
    ds = Dataset()
    editor = Editor()
    
    # This should automatically create the sequence and first item
    operation = Operation(
        op="set_tag",
        tag="<(0012,0064)[0](0010,0020)>",
        val1="PATIENT001",
        val2=""
    )
    
    editor.apply_edits(ds, [operation])
    
    # Verify the sequence was created
    assert (0x0012, 0x0064) in ds
    seq = ds[0x0012, 0x0064]
    assert seq.VR == "SQ"
    assert len(seq.value) == 1
    assert seq.value[0][0x0010, 0x0020].value == "PATIENT001"


def test_create_multiple_sequence_items():
    """Test creating multiple items in a sequence."""
    ds = Dataset()
    editor = Editor()
    
    operations = [
        Operation(op="set_tag", tag="<(0012,0064)[0](0010,0020)>", val1="PATIENT001", val2=""),
        Operation(op="set_tag", tag="<(0012,0064)[1](0010,0020)>", val1="PATIENT002", val2=""),
        Operation(op="set_tag", tag="<(0012,0064)[2](0010,0020)>", val1="PATIENT003", val2=""),
    ]
    
    editor.apply_edits(ds, operations)
    
    # Verify all items were created
    assert (0x0012, 0x0064) in ds
    seq = ds[0x0012, 0x0064]
    assert len(seq.value) == 3
    assert seq.value[0][0x0010, 0x0020].value == "PATIENT001"
    assert seq.value[1][0x0010, 0x0020].value == "PATIENT002"
    assert seq.value[2][0x0010, 0x0020].value == "PATIENT003"


def test_sparse_sequence_creation():
    """Test creating sequence items at non-consecutive indices."""
    ds = Dataset()
    editor = Editor()
    
    # Create item at index 2 (should create 0, 1, 2)
    operation = Operation(
        op="set_tag",
        tag="<(0012,0064)[2](0010,0020)>",
        val1="PATIENT003",
        val2=""
    )
    
    editor.apply_edits(ds, [operation])
    
    # Verify items 0, 1, 2 were all created (0 and 1 are empty)
    assert (0x0012, 0x0064) in ds
    seq = ds[0x0012, 0x0064]
    assert len(seq.value) == 3
    assert len(seq.value[0]) == 0  # Empty
    assert len(seq.value[1]) == 0  # Empty
    assert seq.value[2][0x0010, 0x0020].value == "PATIENT003"


def test_nested_sequence_creation():
    """Test creating nested sequences."""
    ds = Dataset()
    editor = Editor()
    
    # Create a deeply nested tag
    operation = Operation(
        op="set_tag",
        tag="<(0040,0275)[0](0040,0008)[0](0008,0100)>",  # Request Attributes > Item > Code Sequence > Item > Code Value
        val1="CODE123",
        val2=""
    )
    
    editor.apply_edits(ds, [operation])
    
    # Verify the nested structure was created
    assert (0x0040, 0x0275) in ds
    outer_seq = ds[0x0040, 0x0275]
    assert len(outer_seq.value) == 1
    
    inner_seq = outer_seq.value[0][0x0040, 0x0008]
    assert inner_seq.VR == "SQ"
    assert len(inner_seq.value) == 1
    assert inner_seq.value[0][0x0008, 0x0100].value == "CODE123"


def test_add_to_existing_empty_sequence():
    """Test adding items to a sequence that was created empty."""
    ds = Dataset()
    editor = Editor()
    
    # First create an empty sequence
    op1 = Operation(
        op="set_tag",
        tag="<(0012,0064)>",
        val1="",
        val2=""
    )
    editor.apply_edits(ds, [op1])
    
    # Verify it's empty
    assert (0x0012, 0x0064) in ds
    assert len(ds[0x0012, 0x0064].value) == 0
    
    # Now add an item to it
    op2 = Operation(
        op="set_tag",
        tag="<(0012,0064)[0](0010,0020)>",
        val1="PATIENT001",
        val2=""
    )
    editor.apply_edits(ds, [op2])
    
    # Verify the item was added
    seq = ds[0x0012, 0x0064]
    assert len(seq.value) == 1
    assert seq.value[0][0x0010, 0x0020].value == "PATIENT001"


def test_wildcard_with_auto_created_sequence():
    """Test using wildcard on a sequence that's auto-created."""
    ds = Dataset()
    editor = Editor()
    
    # Use wildcard on non-existent sequence - should create one item
    operation = Operation(
        op="set_tag",
        tag="<(0012,0064)[<0>](0010,0020)>",
        val1="PATIENT_WILDCARD",
        val2=""
    )
    
    editor.apply_edits(ds, [operation])
    
    # Verify sequence was created with one item
    assert (0x0012, 0x0064) in ds
    seq = ds[0x0012, 0x0064]
    assert len(seq.value) == 1
    assert seq.value[0][0x0010, 0x0020].value == "PATIENT_WILDCARD"
