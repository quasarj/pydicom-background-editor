import dataclasses
import re


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


def parse(path):
    if not (path.startswith("<") and path.endswith(">")):
        raise ValueError("Path is missing Bills; it looks invalid")

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

    return output


def traverse(ds, parsed_path) -> list:
    """
    Traverse a path and return the matching elements

    TODO: this may need to be expanded to handle Multivalue items
    the same way Posda does - I _think_ they can be referenced
    the same way as DICOM Sequences?
    """
    return _traverse_path(ds, ds, parsed_path)


def _traverse_path(ds, base_ds, parsed_path) -> list:
    if len(parsed_path) == 0:
        return [ds]

    if ds is None:
        return []

    item, *remaning_path = parsed_path

    if isinstance(item, Segment):
        # Traverse the DICOM dataset using the segment

        if item.is_private:
            try:
                private_block = ds.private_block(item.group, item.owner, create=False)
            except KeyError:
                # for some reason, the private creator block can be defined
                # either in at the base of the dataset, or nested
                private_block = base_ds.private_block(
                    item.group, item.owner, create=False
                )

            ds = ds.get(private_block.get_tag(item.element))
        else:
            ds = ds.get((item.group, item.element))
        return _traverse_path(ds, base_ds, remaning_path)

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
            return _traverse_path(ds, base_ds, remaning_path)
        else:
            # wildcard index, we have to recurse for each entry
            ret = []
            for i in range(seq_length):
                x = _traverse_path(seq[i], base_ds, remaning_path)
                # print(">>", x)
                ret.extend(x)
            return ret

    return []