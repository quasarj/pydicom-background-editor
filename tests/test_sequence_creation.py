"""Test creating sequences from scratch."""

from pydicom.dataset import Dataset
from pydicom.sequence import Sequence as PydicomSequence
from pydicom.tag import Tag

from pydicom_background_editor.editor import Operation, Editor


def test_create_empty_sequence():
    """Test creating an empty sequence with VR=SQ."""
    ds = Dataset()
    
    # Try to create a sequence tag
    editor = Editor()
    operation = Operation(
        op="set_tag",
        tag="<(0012,0064)>",  # Clinical Trial Subject ID
        val1="",  # Empty value - what should this do for SQ?
        val2=""
    )
    
    editor.apply_edits(ds, [operation])
    
    # What do we get?
    print(f"Tag exists: {(0x0012, 0x0064) in ds}")
    if (0x0012, 0x0064) in ds:
        elem = ds[0x0012, 0x0064]
        print(f"VR: {elem.VR}")
        print(f"Value type: {type(elem.value)}")
        print(f"Value: {elem.value}")


def test_create_sequence_with_empty_item():
    """Test creating a sequence with one empty item."""
    ds = Dataset()
    
    # Try to create a sequence tag with an item reference
    editor = Editor()
    operation = Operation(
        op="set_tag",
        tag="<(0012,0064)[0]>",  # This implies we want a sequence with at least one item
        val1="",
        val2=""
    )
    
    try:
        editor.apply_edits(ds, [operation])
        print("Operation succeeded")
        
        if (0x0012, 0x0064) in ds:
            elem = ds[0x0012, 0x0064]
            print(f"VR: {elem.VR}")
            print(f"Value type: {type(elem.value)}")
            print(f"Value length: {len(elem.value)}")
    except Exception as e:
        print(f"Operation failed: {e}")


def test_workflow_create_then_populate():
    """Test the workflow: create empty sequence, then add tags to items."""
    ds = Dataset()
    editor = Editor()
    
    # Step 1: Create a sequence (how?)
    # Option A: Set the sequence tag directly to empty
    # Option B: Set a tag inside a sequence item that doesn't exist yet
    # Option C: Use a special operation
    
    # Let's try Option B - reference a sequence item that doesn't exist
    operations = [
        Operation(
            op="set_tag",
            tag="<(0012,0064)[0](0010,0020)>",  # Patient ID inside Clinical Trial sequence
            val1="PATIENT001",
            val2=""
        )
    ]
    
    try:
        editor.apply_edits(ds, operations)
        print("Step 1 succeeded")
        
        if (0x0012, 0x0064) in ds:
            seq = ds[0x0012, 0x0064]
            print(f"Sequence VR: {seq.VR}")
            print(f"Sequence length: {len(seq.value)}")
            if len(seq.value) > 0:
                print(f"First item has tags: {len(seq.value[0])} tags")
                print(f"First item content: {seq.value[0]}")
        else:
            print("Sequence tag was not created!")
    except Exception as e:
        print(f"Step 1 failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=== Test 1: Create empty sequence ===")
    test_create_empty_sequence()
    print("\n=== Test 2: Create sequence with empty item ===")
    test_create_sequence_with_empty_item()
    print("\n=== Test 3: Workflow - create then populate ===")
    test_workflow_create_then_populate()
