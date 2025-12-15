"""Test the specific workflow of creating and populating sequences."""

from pydicom.dataset import Dataset
from pydicom_background_editor.editor import Operation, Editor


def test_workflow_create_empty_then_add_items():
    """Test creating an empty sequence first, then adding items to it.
    
    This is the workflow mentioned by the user:
    1. Create empty sequence with set_tag to ""
    2. Add items to it with subsequent set_tag operations
    """
    ds = Dataset()
    editor = Editor()
    
    # Step 1: Create empty sequence
    operations = [
        Operation(
            op="set_tag",
            tag="<(0012,0064)>",  # De-identification Method Code Sequence
            val1="",
            val2=""
        ),
    ]
    editor.apply_edits(ds, operations)
    
    # Verify empty sequence was created
    assert (0x0012, 0x0064) in ds
    assert ds[0x0012, 0x0064].VR == "SQ"
    assert len(ds[0x0012, 0x0064].value) == 0
    
    # Step 2: Add items to the sequence
    operations = [
        Operation(
            op="set_tag",
            tag="<(0012,0064)[0](0008,0100)>",  # Code Value
            val1="113100",
            val2=""
        ),
        Operation(
            op="set_tag",
            tag="<(0012,0064)[0](0008,0102)>",  # Coding Scheme Designator
            val1="DCM",
            val2=""
        ),
        Operation(
            op="set_tag",
            tag="<(0012,0064)[1](0008,0100)>",  # Second item
            val1="113101",
            val2=""
        ),
    ]
    editor.apply_edits(ds, operations)
    
    # Verify items were added
    seq = ds[0x0012, 0x0064]
    assert len(seq.value) == 2
    assert seq.value[0][0x0008, 0x0100].value == "113100"
    assert seq.value[0][0x0008, 0x0102].value == "DCM"
    assert seq.value[1][0x0008, 0x0100].value == "113101"


def test_workflow_direct_create_and_populate():
    """Test creating a sequence by directly setting tags in items that don't exist yet.
    
    This is the simpler workflow - just reference tags in sequence items and they
    will be created automatically.
    """
    ds = Dataset()
    editor = Editor()
    
    # Directly set tags in non-existent sequence items
    operations = [
        Operation(
            op="set_tag",
            tag="<(0012,0064)[0](0008,0100)>",
            val1="113100",
            val2=""
        ),
        Operation(
            op="set_tag",
            tag="<(0012,0064)[0](0008,0102)>",
            val1="DCM",
            val2=""
        ),
        Operation(
            op="set_tag",
            tag="<(0012,0064)[1](0008,0100)>",
            val1="113101",
            val2=""
        ),
    ]
    editor.apply_edits(ds, operations)
    
    # Verify everything was created
    assert (0x0012, 0x0064) in ds
    seq = ds[0x0012, 0x0064]
    assert seq.VR == "SQ"
    assert len(seq.value) == 2
    assert seq.value[0][0x0008, 0x0100].value == "113100"
    assert seq.value[0][0x0008, 0x0102].value == "DCM"
    assert seq.value[1][0x0008, 0x0100].value == "113101"


def test_workflow_mixed_approaches():
    """Test mixing both approaches in the same dataset."""
    ds = Dataset()
    editor = Editor()
    
    operations = [
        # Create one sequence explicitly empty
        Operation(op="set_tag", tag="<(0012,0064)>", val1="", val2=""),
        
        # Create another sequence implicitly by referencing an item
        Operation(op="set_tag", tag="<(0040,0275)[0](0040,a040)>", val1="SOMETHING", val2=""),  # (0040,a040) = Value Type, VR=CS
        
        # Add to the first sequence
        Operation(op="set_tag", tag="<(0012,0064)[0](0008,0100)>", val1="CODE1", val2=""),
        
        # Add more to the second sequence
        Operation(op="set_tag", tag="<(0040,0275)[1](0040,a040)>", val1="ELSE", val2=""),
    ]
    
    editor.apply_edits(ds, operations)
    
    # Verify both sequences exist and are populated
    assert (0x0012, 0x0064) in ds
    assert len(ds[0x0012, 0x0064].value) == 1
    assert ds[0x0012, 0x0064].value[0][0x0008, 0x0100].value == "CODE1"
    
    assert (0x0040, 0x0275) in ds
    assert len(ds[0x0040, 0x0275].value) == 2
    assert ds[0x0040, 0x0275].value[0][0x0040, 0xa040].value == "SOMETHING"
    assert ds[0x0040, 0x0275].value[1][0x0040, 0xa040].value == "ELSE"
