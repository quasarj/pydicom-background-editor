import dataclasses
from pydicom.dataset import Dataset
from .path import traverse, parse


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
                pass