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

    def _op_substitute(self, ds: Dataset, op: Operation):
        """Conditionally replace tag value only if it matches val1.
        
        Traverses to the target tag(s) and replaces the value with val2 only if
        the current value exactly matches val1. If the tag doesn't exist or the
        value doesn't match, no action is taken.
        Works with both single tags and wildcard paths that match multiple elements.
        Handles both single-valued and multi-valued DICOM fields.
        
        Args:
            ds: The DICOM dataset to modify
            op: Operation containing tag path, val1 (match value), and val2 (replacement)
        """
        parsed_path = parse(op.tag)
        tags = traverse(ds, parsed_path)
        logger.debug(f"Substituting tag {op.tag}: {op.val1} -> {op.val2}")

        last_segment = parsed_path[-1]

        if last_segment.is_private:
            new_vr = datadict.private_dictionary_VR([last_segment.group, last_segment.element], last_segment.owner) # type: ignore
        else:
            new_vr = datadict.dictionary_VR([last_segment.group, last_segment.element]) # type: ignore

        for tag in tags:
            if tag.element is not None:
                current_value = tag.element.value
                
                # Handle multi-valued fields (lists/MultiValue)
                if isinstance(current_value, (list, MultiValue)):
                    # Check if any value in the list matches val1
                    # Replace matching values with val2
                    new_list = []
                    modified = False
                    for v in current_value:
                        if str(v) == op.val1:
                            new_list.append(op.val2)
                            modified = True
                        else:
                            new_list.append(v)
                    
                    if modified:
                        # Preserve MultiValue type if original was MultiValue
                        if isinstance(current_value, MultiValue):
                            new_value = type(current_value)(str, new_list)
                        else:
                            new_value = new_list
                        tag.element.value = new_value
                else:
                    # Single value - check for exact match
                    if str(current_value) == op.val1:
                        new_value = truncate_value(op.val2, new_vr)
                        tag.element.value = new_value
            # If tag doesn't exist, do nothing (unlike set_tag or empty_tag)

    def _op_shift_date(self, ds: Dataset, op: Operation):
        """Shift a date value forward or backward by a number of days.
        
        Traverses to the target tag(s) and shifts date values by the number of days
        specified in val1. Positive values shift forward, negative values shift backward.
        Only works on tags with VR of 'DA' (Date) or 'DT' (DateTime).
        If the tag doesn't exist or the value cannot be parsed as a date, no action is taken.
        Works with both single tags and wildcard paths that match multiple elements.
        
        DICOM Date format (DA): YYYYMMDD
        DICOM DateTime format (DT): YYYYMMDDHHMMSS.FFFFFF&ZZXX (but we only shift the date portion)
        
        Args:
            ds: The DICOM dataset to modify
            op: Operation containing tag path and val1 (number of days to shift, can be negative)
        """
        from datetime import datetime, timedelta
        
        parsed_path = parse(op.tag)
        tags = traverse(ds, parsed_path)
        
        try:
            days_to_shift = int(op.val1)
        except (ValueError, TypeError):
            logger.warning(f"Invalid days value for shift_date: {op.val1}")
            return
        
        logger.debug(f"Shifting date tag {op.tag} by {days_to_shift} days")

        for tag in tags:
            if tag.element is None:
                continue
            
            vr = tag.element.VR
            
            # Only process date-related VRs
            if vr not in ('DA', 'DT'):
                logger.warning(f"Tag {tag.element.tag} has VR {vr}, not a date type (DA or DT). Skipping.")
                continue
            
            current_value = str(tag.element.value)
            
            try:
                if vr == 'DA':
                    # DICOM Date format: YYYYMMDD
                    if len(current_value) < 8:
                        logger.warning(f"Invalid DA format: {current_value}. Expected YYYYMMDD.")
                        continue
                    
                    # Parse the date (take first 8 characters)
                    date_str = current_value[:8]
                    date_obj = datetime.strptime(date_str, '%Y%m%d')
                    
                    # Shift the date
                    new_date = date_obj + timedelta(days=days_to_shift)
                    
                    # Format back to DICOM DA format
                    new_value = new_date.strftime('%Y%m%d')
                    
                    # Preserve any additional characters after the date (though unusual for DA)
                    if len(current_value) > 8:
                        new_value += current_value[8:]
                    
                    tag.element.value = new_value
                
                elif vr == 'DT':
                    # DICOM DateTime format: YYYYMMDDHHMMSS.FFFFFF&ZZXX
                    # We only shift the date portion (first 8 characters)
                    if len(current_value) < 8:
                        logger.warning(f"Invalid DT format: {current_value}. Expected at least YYYYMMDD.")
                        continue
                    
                    # Parse the date portion (first 8 characters)
                    date_str = current_value[:8]
                    date_obj = datetime.strptime(date_str, '%Y%m%d')
                    
                    # Shift the date
                    new_date = date_obj + timedelta(days=days_to_shift)
                    
                    # Format back to DICOM format, preserving time and timezone info
                    new_value = new_date.strftime('%Y%m%d') + current_value[8:]
                    
                    tag.element.value = new_value
            
            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse or shift date value '{current_value}': {e}")
                continue

    def _op_copy_from_tag(self, ds: Dataset, op: Operation):
        """Copy value from source tag to destination tag.
        
        Copies the value from the tag specified in val1 (source) to the tag specified
        in op.tag (destination). If the source path matches multiple tags (via wildcards),
        the value from the first matching tag is used. If the destination path matches
        multiple tags, all matching destination tags receive the same copied value.
        
        The value is converted to match the destination tag's VR. If conversion fails,
        an error is raised. If the source tag doesn't exist, no action is taken.
        If the destination tag doesn't exist, it will be created.
        
        Args:
            ds: The DICOM dataset to modify
            op: Operation containing:
                - tag: destination path
                - val1: source tag path (in meta-quoted form like "<(0010,0010)>")
                - val2: unused
        """
        # Parse and traverse the source path (val1)
        source_path_str = op.val1
        if not source_path_str:
            logger.warning(f"copy_from_tag requires val1 to specify source tag path")
            return
        
        # Strip meta-quotes from source path if present
        if source_path_str.startswith("<") and source_path_str.endswith(">"):
            source_path_str = source_path_str[1:-1]
        
        try:
            source_parsed = parse(f"<{source_path_str}>")
        except Exception as e:
            logger.warning(f"Failed to parse source path '{source_path_str}': {e}")
            return
        
        source_tags = traverse(ds, source_parsed)
        
        # Check if we found any source tags
        valid_sources = [t for t in source_tags if t.element is not None]
        if not valid_sources:
            logger.warning(f"Source tag {source_path_str} not found, cannot copy")
            return
        
        # Take the first matching source tag
        source_tag = valid_sources[0]
        source_value = source_tag.element.value
        source_vr = source_tag.element.VR
        
        logger.debug(f"Copying from {source_path_str} (VR={source_vr}, value={source_value}) to {op.tag}")
        
        # Parse and traverse the destination path
        dest_parsed = parse(op.tag)
        dest_tags = traverse(ds, dest_parsed)
        
        # Determine the destination VR
        dest_segment = dest_parsed[-1]
        if dest_segment.is_private:
            dest_vr = datadict.private_dictionary_VR([dest_segment.group, dest_segment.element], dest_segment.owner) # type: ignore
        else:
            dest_vr = datadict.dictionary_VR([dest_segment.group, dest_segment.element]) # type: ignore
        
        # Convert value to destination VR
        try:
            # Convert the value appropriately for the destination VR
            converted_value = self._convert_value_for_vr(source_value, source_vr, dest_vr)
        except Exception as e:
            logger.error(f"Failed to convert value '{source_value}' from VR {source_vr} to {dest_vr}: {e}")
            raise ValueError(f"Cannot convert value from VR {source_vr} to {dest_vr}") from e
        
        # Apply to all matching destination tags
        for dest_tag in dest_tags:
            if dest_tag.element is not None:
                dest_tag.element.value = converted_value
            else:
                # Destination tag doesn't exist, create it
                add_tag(ds, dest_parsed, converted_value, dest_vr)

    def _convert_value_for_vr(self, value, source_vr: str, dest_vr: str):
        """Convert a value from one VR to another.
        
        Attempts to convert a value from source VR to destination VR.
        Handles common conversions and applies appropriate formatting.
        
        Args:
            value: The value to convert (can be string, MultiValue, list, etc.)
            source_vr: The source Value Representation
            dest_vr: The destination Value Representation
            
        Returns:
            The converted value appropriate for the destination VR
            
        Raises:
            ValueError: If conversion is not possible
        """
        # If VRs are the same, just return the value (possibly as string)
        if source_vr == dest_vr:
            return value
        
        # Handle MultiValue - convert to string for processing
        if isinstance(value, MultiValue):
            # For multi-valued to single-valued, take first element
            value_str = str(value[0]) if len(value) > 0 else ""
        else:
            value_str = str(value)
        
        # Most string-based VRs can convert to each other
        string_vrs = {'AE', 'AS', 'CS', 'DA', 'DS', 'DT', 'IS', 'LO', 'LT', 
                      'PN', 'SH', 'ST', 'TM', 'UC', 'UI', 'UR', 'UT'}
        
        if source_vr in string_vrs and dest_vr in string_vrs:
            # Apply truncation for destination VR
            return truncate_value(value_str, dest_vr)
        
        # Numeric conversions
        if source_vr in {'DS', 'IS', 'FL', 'FD', 'SL', 'SS', 'UL', 'US'} and \
           dest_vr in {'DS', 'IS', 'FL', 'FD', 'SL', 'SS', 'UL', 'US'}:
            # Numeric types can generally convert between each other
            return value_str
        
        # Date/Time conversions
        if source_vr in {'DA', 'DT', 'TM'} and dest_vr in {'DA', 'DT', 'TM'}:
            return value_str
        
        # If we get here, try a generic string conversion
        # This may work for some cases but could fail
        logger.warning(f"Attempting generic conversion from VR {source_vr} to {dest_vr}")
        return truncate_value(value_str, dest_vr)