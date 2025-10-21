import dataclasses
from pydicom.dataset import Dataset
from pydicom.multival import MultiValue
from .path import traverse, parse, add_tag


@dataclasses.dataclass
class Operation():
    op: str
    tag: str
    val1: str
    val2: str

    @staticmethod
    def from_csv_row(row: dict) -> "Operation":
        return Operation(
            op=row["op"],
            tag=row["tag"],
            val1=row["val1"],
            val2=row["val2"],
        )

class Editor:
    def __init__(self):
        pass

    def apply_edits(self, ds: Dataset, operations: list[Operation]):
        for op in operations:
            op_function = "_op_" + op.op
            #execute op_function on self
            getattr(self, op_function)(ds, op)

    def _op_set_tag(self, ds: Dataset, op: Operation):
        # use traverse_path to find the actual tag to edit
        parsed_path = parse(op.tag)
        tags = traverse(ds, parsed_path)
        print(f"Setting tag {op.tag} to {op.val1}")
        for tag in tags:
            if tag is not None:
                tag.value = op.val1
            if tag is None:
                # the tag was not present in the dataset, so we must add it
                add_tag(ds, parsed_path, op.val1, 'UN')

    def _op_string_replace(self, ds: Dataset, op: Operation):
        """Replace substring in tag value(s).
        
        Traverses to the target tag(s) and replaces all occurrences of val1 with val2.
        If the tag doesn't exist, no action is taken (unlike set_tag which creates it).
        Works with both single tags and wildcard paths that match multiple elements.
        Handles both single-valued and multi-valued DICOM fields.
        
        Args:
            ds: The DICOM dataset to modify
            op: Operation containing tag path, val1 (search), and val2 (replace)
        """
        parsed_path = parse(op.tag)
        tags = traverse(ds, parsed_path)
        
        for tag in tags:
            if tag is not None:
                current_value = tag.value
                
                # Handle multi-valued fields (lists/MultiValue)
                if isinstance(current_value, (list, MultiValue)):
                    # Perform replacement on each value
                    new_list = [str(v).replace(op.val1, op.val2) for v in current_value]
                    # Preserve MultiValue type if original was MultiValue
                    if isinstance(current_value, MultiValue):
                        new_value = type(current_value)(str, new_list)
                    else:
                        new_value = new_list
                else:
                    # Single value - convert to string for replacement
                    new_value = str(current_value).replace(op.val1, op.val2)
                
                tag.value = new_value