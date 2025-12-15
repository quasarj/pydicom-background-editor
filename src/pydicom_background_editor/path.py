import dataclasses
import re
import pydicom
from pydicom.dataelem import DataElement
from pydicom import Dataset, datadict
from collections import namedtuple
from typing import NamedTuple

class ElementPair(NamedTuple):
    element: Dataset
    ds_chain: list[Dataset]

@dataclasses.dataclass
class Segment:
    tag: str
    group: int
    element: int
    is_private: bool = False
    owner: str | None = None

    def __init__(self, tag: str):
        self.tag = tag

        if '"' in tag:
            self.is_private = True
            group, self.owner, ele = tag.split('"')

            group = group.strip(",")
            ele = ele.strip(",")
        else:
            group, ele = tag.split(",")

        self.group = int(group, 16)
        self.element = int(ele, 16)


@dataclasses.dataclass
class Sequence:
    value: int
    wildcard: bool

    def __init__(self, value: str):
        if value.startswith("<") and value.endswith(">"):
            self.wildcard = True
            self.value = int(value.strip("<>"))
        else:
            self.wildcard = False
            self.value = int(value)


class Path(list):
    pass


def add_tag(ds: Dataset, parsed_path: Path, value: str, vr: str | None = None) -> None:
    """
    Assuming the final tag in the parsed_path does not actually exist,
    but that all other tags do exist, this method creates the missing
    tag and sets it to the value provided.
    
    If the path includes sequence hops and those sequences or items don't exist,
    they will be created automatically.
    """

    
    element_to_add = parsed_path.pop()

    if vr is None:
        dict_entry = datadict.get_entry([element_to_add.group, element_to_add.element])
        if dict_entry is None:
            raise ValueError(f"Cannot find VR for tag {element_to_add.tag}")

        vr = dict_entry[0] if dict_entry is not None else None

    if len(parsed_path) == 0:
        # we are at the root level, no need to parse
        ds.add_new((element_to_add.group, element_to_add.element), vr, value)
        return

    # traverse to the parent of the element to add, creating intermediate structures as needed
    eles = _traverse_or_create(ds, parsed_path)
    for ele in eles:
        ele.element.add_new((element_to_add.group, element_to_add.element), vr, value)


def _traverse_or_create(ds: Dataset, parsed_path: Path) -> list[ElementPair]:
    """
    Traverse a path, creating intermediate sequence structures if they don't exist.
    
    This is similar to traverse(), but if a path element doesn't exist, it will be created:
    - If a Segment (tag) doesn't exist and has VR=SQ, an empty sequence is created
    - If a Sequence hop refers to an index that doesn't exist, empty Dataset items are created
    
    Returns:
        List of ElementPairs pointing to the final location(s) in the path
    """
    from pydicom.sequence import Sequence as PydicomSequence
    
    if len(parsed_path) == 0:
        return [ElementPair(ds, [ds])]
    
    current_datasets = [(ds, [ds])]  # List of (current_ds, ds_chain) tuples
    
    for item in parsed_path:
        next_datasets = []
        
        if isinstance(item, Segment):
            # For each current dataset, navigate or create the segment
            for current_ds, ds_chain in current_datasets:
                if item.is_private:
                    try:
                        private_block = current_ds.private_block(item.group, item.owner or "", create=False)
                        next_elem = current_ds.get(private_block.get_tag(item.element))
                    except KeyError:
                        # Private block doesn't exist - create it
                        private_block = current_ds.private_block(item.group, item.owner or "", create=True)
                        # Need to determine VR for private tag
                        next_vr = datadict.private_dictionary_VR([item.group, item.element], item.owner) # type: ignore
                        if next_vr == 'SQ':
                            private_block.add_new(item.element, next_vr, PydicomSequence([]))
                            next_elem = current_ds.get(private_block.get_tag(item.element))
                        else:
                            # Not a sequence, this shouldn't happen in a path with more items
                            raise ValueError(f"Cannot traverse through non-sequence private tag {item.tag}")
                else:
                    next_elem = current_ds.get((item.group, item.element))
                
                if next_elem is None:
                    # Tag doesn't exist - create it if it's a sequence
                    tag_vr = datadict.dictionary_VR([item.group, item.element]) # type: ignore
                    if tag_vr == 'SQ':
                        # Create empty sequence
                        current_ds.add_new((item.group, item.element), 'SQ', PydicomSequence([]))
                        next_elem = current_ds.get((item.group, item.element))
                    else:
                        # Not a sequence, shouldn't happen in middle of path
                        raise ValueError(f"Cannot traverse through non-existent non-sequence tag {item.tag}")
                
                # next_elem is a DataElement, we need its value for sequences
                if hasattr(next_elem, 'value'):
                    next_datasets.append((next_elem, ds_chain))
                else:
                    next_datasets.append((next_elem, ds_chain))
        
        elif isinstance(item, Sequence):
            # For each current dataset, navigate or create sequence items
            for current_elem, ds_chain in current_datasets:
                # current_elem should be a DataElement with VR=SQ
                if not hasattr(current_elem, 'value'):
                    raise ValueError(f"Expected DataElement with sequence value")
                
                seq = current_elem.value
                if not isinstance(seq, PydicomSequence):
                    raise ValueError(f"Expected PydicomSequence, got {type(seq)}")
                
                if item.wildcard:
                    # Wildcard - iterate through all existing items
                    if len(seq) == 0:
                        # No items exist - create one empty item
                        seq.append(Dataset())
                    
                    for seq_item in seq:
                        next_datasets.append((seq_item, ds_chain + [seq_item]))
                else:
                    # Specific index
                    index = int(item.value)
                    
                    # Create empty items up to the requested index if needed
                    while len(seq) <= index:
                        seq.append(Dataset())
                    
                    next_datasets.append((seq[index], ds_chain + [seq[index]]))
        
        current_datasets = next_datasets
    
    # Convert final (ds, ds_chain) tuples to ElementPairs
    return [ElementPair(ds, ds_chain) for ds, ds_chain in current_datasets]


def parse(path: str) -> Path:
    ## TODO: disabled for now, looks like we need to handle both cases
    # if not (path.startswith("<") and path.endswith(">")):
    #     raise ValueError("Path is missing Bills; it looks invalid")

    path = path.strip("<>")

    # Match the entire path; this should break it into a set of matches
    # for each component in the path
    # This regex matches either:
    # - A group of digits inside parentheses (e.g. (0008,1110))
    # - A group of digits inside square brackets (e.g. [<0>], or [2])
    regex = r"\(([^)]+)\)|\[(<[^>]+>|[^\]]+)\]"

    matches = re.findall(regex, path)

    output = []
    for segment, sequence in matches:
        if segment:
            s = Segment(segment)
            output.append(s)
        if sequence:
            s = Sequence(sequence)
            output.append(s)

    return Path(output)


def traverse(ds: Dataset, parsed_path: Path) -> list[ElementPair]:
    """
    Traverse a path and return the matching elements

    TODO: this may need to be expanded to handle Multivalue items
    the same way Posda does - I _think_ they can be referenced
    the same way as DICOM Sequences?
    """
    return _traverse_path(ds, [ds], parsed_path)

# TODO: we need to keep track of the entire chain of datasets, not just the base one, I think
# in order to be able to check them all for the closest private creator block above
# the current one
def _traverse_path(ds: Dataset, ds_chain: list[Dataset], parsed_path: Path) -> list[ElementPair]:
    # This will be hit when we have reached the end of the path, or
    # the path was empty to begin with
    if len(parsed_path) == 0:
        return [ElementPair(ds, ds_chain)]

    # This will be hit on a path where the node does not exist
    if ds is None:
        return []

    item, *remaining_path = parsed_path
    remaining_path = Path(remaining_path)

    if isinstance(item, Segment):
        # Traverse the DICOM dataset using the segment

        if item.is_private:
            try:
                private_block = ds.private_block(item.group, item.owner or "", create=False)
            except KeyError:
                # for some reason, the private creator block can be defined
                # either in at the base of the dataset, or nested
                # TODO: we might have to check every ds in the chain
                private_block = ds_chain[0].private_block(
                    item.group, item.owner or "", create=False
                )

            ds = ds.get(private_block.get_tag(item.element)) # type: ignore
        else:
            ds = ds.get((item.group, item.element)) # type: ignore

        if isinstance(ds, DataElement):
            # if this ds is actually a DataElement, skip
            # adding it to the ds_chain. This mainaly handles keeping
            # Sequences out of the chain, ans well as the final element
            extended_chain = ds_chain
        else:
            extended_chain = ds_chain + [ds]
        return _traverse_path(ds, extended_chain, remaining_path)

    elif isinstance(item, Sequence):
        # Handle sequences
        seq = ds.value  # get the actual pydicom Sequence object
        seq_length = len(seq)

        if not item.wildcard:
            # Exact index
            exact_index = int(item.value)
            if exact_index >= seq_length:
                return []
            ds = seq[exact_index]
            return _traverse_path(ds, ds_chain + [ds], remaining_path)
        else:
            # wildcard index, we have to recurse for each entry
            ret = []
            for i in range(seq_length):
                x = _traverse_path(seq[i], ds_chain + [seq[i]], remaining_path)
                ret.extend(x)
            return ret

    return [] # this should never be hit, but included for completeness