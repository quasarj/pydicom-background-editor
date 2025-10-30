import dataclasses
import logging
from pydicom import datadict
from pydicom.dataset import Dataset
from pydicom.multival import MultiValue
from pydicom.valuerep import MAX_VALUE_LEN
from .path import traverse, parse, add_tag

logger = logging.getLogger(__name__)


new_dict_items = {
       0x00130010: ('LO', '1', "Project Name", 'false'),
       0x00130011: ('LO', '1', "Trial Name", 'false'),
       0x00130012: ('LO', '1', "Site Name", 'false'),
       0x00130013: ('LO', '1', "Site Id", 'false'),
       0x00130014: ('LO', '1', "Visibility", 'false'),
       0x00130015: ('LO', '1', "Batch", 'false'),
       0x00130050: ('LO', '1', "Year of Study", 'false'),
       0x00130051: ('LO', '1', "Year of Diagnosis", 'false'),
}
datadict.add_private_dict_entries("CTP", new_dict_items)

def truncate_value(value: str, vr: str) -> str:
    """Truncate a string value to fit within DICOM VR limits, if applicable.
    
    Args:
        value: The string value to potentially truncate
        vr: The DICOM Value Representation (e.g. 'LO', 'PN', etc.)

    Returns:
        The truncated string value, or the original value if no truncation is needed
    """
    max_length = MAX_VALUE_LEN.get(vr, None)
    if max_length is not None and len(value) > max_length:
        logger.warning(f"Truncating value for VR {vr}: {value} -> {value[:max_length]}")
        return value[:max_length]
    return value

@dataclasses.dataclass
class Operation():
    op: str
    tag: str
    val1: str
    val2: str

    @staticmethod
    def _strip_metaquotes(value: str) -> str:
        """Strip Excel-style meta-quotes (angle brackets) from a value.
        
        Removes outer <> brackets if present. Handles edge cases like:
        - Empty strings
        - Strings without brackets
        - Strings with only one bracket
        - Strings with leading single quote before left bracket
        
        Args:
            value: The string value to strip
            
        Returns:
            The value with outer angle brackets removed
        """
        if not value:
            return value
            
        # Strip leading single quote if present (Excel quirk)
        if value.startswith("'<"):
            value = value[1:]
        
        # Strip outer angle brackets
        if value.startswith("<") and value.endswith(">"):
            return value[1:-1]
        
        return value

    @staticmethod
    def from_csv_row(row: dict) -> "Operation":
        return Operation(
            op=row["op"],
            tag=row["tag"],
            val1=Operation._strip_metaquotes(row["val1"]),
            val2=Operation._strip_metaquotes(row["val2"]),
        )

class Editor:
    def __init__(self):
        pass

    def apply_edits(self, ds: Dataset, operations: list[Operation]):
        for op in operations:
            op_function = "_op_" + op.op
            #execute op_function on self
            getattr(self, op_function)(ds, op)

    def _op_delete_tag(self, ds: Dataset, op: Operation):
        parsed_path = parse(op.tag)
        tags = traverse(ds, parsed_path)
        logger.debug(f"Deleting tag {op.tag}")

        for tag in tags:
            if tag.element is not None:
                del tag.ds_chain[-1][tag.element.tag]

    def _op_set_tag(self, ds: Dataset, op: Operation):
        # use traverse_path to find the actual tag to edit
        parsed_path = parse(op.tag)
        tags = traverse(ds, parsed_path)
        logger.debug(f"Setting tag {op.tag} to {op.val1}")

        last_segment = parsed_path[-1]

        if last_segment.is_private:
            new_value = op.val1
            new_vr = datadict.private_dictionary_VR([last_segment.group, last_segment.element], last_segment.owner) # type: ignore
        else:
            new_vr = datadict.dictionary_VR([last_segment.group, last_segment.element]) # type: ignore
            new_value = truncate_value(op.val1, new_vr)

        for tag in tags:
            if tag is not None and tag.element is not None:
                tag.element.value = new_value
            else:
                # the tag was not present in the dataset, so we must add it
                add_tag(ds, parsed_path, new_value, new_vr)

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
        logger.debug(f"String Replacing tag {op.tag} from {op.val1} to {op.val2}")

        last_segment = parsed_path[-1]

        if last_segment.is_private:
            # TODO: we likely need to handle this better
            current_vr = 'UN'
        else:
            current_vr = datadict.dictionary_VR([last_segment.group, last_segment.element]) # type: ignore
        
        for tag in tags:
            if tag.element is not None:
                current_value = tag.element.value
                if op.val1 not in str(current_value):
                    continue  # No occurrence to replace
                
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
                    replaced_value = str(current_value).replace(op.val1, op.val2)
                    new_value = truncate_value(replaced_value, current_vr)
                
                tag.element.value = new_value

    def _op_empty_tag(self, ds: Dataset, op: Operation):
        """Set tag value to empty string.
        
        Traverses to the target tag(s) and sets their value to an empty string.
        If the tag doesn't exist, it will be created with an empty value.
        Works with both single tags and wildcard paths that match multiple elements.
        
        Args:
            ds: The DICOM dataset to modify
            op: Operation containing tag path (val1 and val2 are ignored)
        """
        parsed_path = parse(op.tag)
        tags = traverse(ds, parsed_path)
        logger.debug(f"Emptying tag {op.tag}")

        last_segment = parsed_path[-1]

        if last_segment.is_private:
            new_vr = datadict.private_dictionary_VR([last_segment.group, last_segment.element], last_segment.owner) # type: ignore
        else:
            new_vr = datadict.dictionary_VR([last_segment.group, last_segment.element]) # type: ignore

        for tag in tags:
            if tag.element is not None:
                tag.element.value = ""
            else:
                # the tag was not present in the dataset, so we must add it
                add_tag(ds, parsed_path, "", new_vr)