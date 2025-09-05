from pydicom_background_editor.path import parse, traverse, Segment, Sequence
from pprint import pprint
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence as PydicomSequence
from pydicom.tag import Tag

def make_test_dataset():
    """Construct a pydicom Dataset with nested Sequences and private tags for tests."""

    ds = Dataset()

    # Basic attributes
    ds.PatientName = "Test^Patient"
    ds.StudyInstanceUID = "1.2.840.12345.1"
    ds.ImageType = r"ORIGINAL\PRIMARY\AXIAL"

    # Private creator (0029,0010) for the group 0x0029
    ds.add_new(Tag(0x0029, 0x0010), 'LO', "INTELERAD MEDICAL SYSTEMS")
    # A private element in the block assigned by the above creator:
    # The element 0x1020 corresponds to that private creator's block and element 0x20.
    ds.add_new(Tag(0x0029, 0x1020), 'LO', "PRIVATE_VALUE_20")

    # Private tags the block way
    private_block = ds.private_block(0x0013, "CTP", create=True)
    private_block.add_new(0x10, 'LO', "TCIA-Fake-Project")
    private_block.add_new(0x11, 'LO', "TCIA-Fake-Site")
    private_block.add_new(0x13, 'LO', "12345678")

    # Build nested sequences similar to paths used in tests

    # Structure for (0008,1115)[...](0008,114a)[...](0008,1150)
    item_1150 = Dataset()
    item_1150.add_new(Tag(0x0008, 0x1150), 'UI', "1.2.840.10008.5.1.4.1.1.128")  # terminal element

    seq_114a = PydicomSequence([item_1150] * 100)
    parent_114a_item = Dataset()
    parent_114a_item.add_new(Tag(0x0008, 0x114a), 'SQ', seq_114a)

    seq_1115 = PydicomSequence([parent_114a_item])
    ds.add_new(Tag(0x0008, 0x1115), 'SQ', seq_1115)

    # Deeply nested structure for (5200,9230)[...](0008,9124)[...](0008,2112)[...](0040,a170)[...](0008,0100)
    leaf = Dataset()
    leaf.add_new(Tag(0x0008, 0x0100), 'LO', "121322")  # terminal value used in tests

    seq_a170 = PydicomSequence([leaf] * 200)
    item_2112 = Dataset()
    item_2112.add_new(Tag(0x0040, 0xA170), 'SQ', seq_a170)

    seq_2112 = PydicomSequence([item_2112] * 5)
    item_9124 = Dataset()
    item_9124.add_new(Tag(0x0008, 0x2112), 'SQ', seq_2112)

    seq_9124 = PydicomSequence([item_9124])
    item_5200 = Dataset()
    item_5200.add_new(Tag(0x0008, 0x9124), 'SQ', seq_9124)

    seq_5200 = PydicomSequence([item_5200])
    ds.add_new(Tag(0x5200, 0x9230), 'SQ', seq_5200)

    # Add an additional item under the private group to demonstrate mixing private/public
    extra_priv_item = Dataset()
    # a private element inside an item (same private creator block)
    extra_priv_item.add_new(Tag(0x0029, 0x0010), 'LO', "NEW CREATOR")
    extra_priv_item.add_new(Tag(0x0029, 0x1021), 'LO', "PRIVATE_VALUE_21")

    seq_extra = PydicomSequence([extra_priv_item] * 2)
    ds.add_new(Tag(0x6000, 0x0010), 'SQ', seq_extra)  # arbitrary additional sequence

    return ds

def test_ds():
    ds = make_test_dataset()
    assert ds is not None

def test_things():
    ds = make_test_dataset()
    res = traverse(ds, parse("<(6001,0010)[0]>"))
    print(res)


def test_parse_path_simple_segment():
    """Test parsing of a simple DICOM path segment."""
    simple_path_segment = "<(0008,1110)>"
    parsed = parse(simple_path_segment)

    assert len(parsed) == 1
    seg = parsed[0]
    assert isinstance(seg, Segment)
    assert seg.tag == '0008,1110'
    assert seg.group == 0x0008
    assert seg.element == 0x1110

def test_parse_path_concrete_index():
    """Tests parsing of a DICOM path segment with a concrete index."""
    element = "<(0008,1110)[1]>"
    parsed = parse(element)

    assert len(parsed) == 2
    one, two = parsed
    
    assert isinstance(one, Segment)
    assert one.tag == '0008,1110'
    assert one.group == 0x0008
    assert one.element == 0x1110

    assert isinstance(two, Sequence)
    assert two.value == 1
    assert two.wildcard == False

def test_parse_path_wildcard_index():
    """Tests parsing of a DICOM path segment with a wildcard index."""
    element = "<(0008,1110)[<0>]>"
    parsed = parse(element)

    assert len(parsed) == 2
    one, two = parsed
    
    assert isinstance(one, Segment)
    assert one.tag == '0008,1110'
    assert one.group == 0x0008
    assert one.element == 0x1110

    assert isinstance(two, Sequence)
    assert two.value == 0
    assert two.wildcard == True


    
def test_parse_path_private_simple():
    """Tests parsing of a simple private path element"""

    element = '<(0029,"INTELERAD MEDICAL SYSTEMS",20)>'
    parsed = parse(element)

    assert len(parsed) == 1
    seg = parsed[0]
    assert isinstance(seg, Segment)

    assert seg.is_private == True
    assert seg.tag == '0029,"INTELERAD MEDICAL SYSTEMS",20'
    assert seg.group == 0x0029
    assert seg.owner == "INTELERAD MEDICAL SYSTEMS"
    assert seg.element == 0x20

def test_parse_path_complex_mixed():
    """Tests parsing of a complex path with mixed wildcard and concrete indexes"""

    element = '<(0008,1110)[3](0008,1155)[<1>](0008,1125)[<2>](0023,0010)[9](0029,"QUASAR",13)">'
    parsed = parse(element)

    assert len(parsed) == 9
    one, two, three, four, five, six, seven, eight, nine = parsed

    assert isinstance(one, Segment)
    assert one.tag == '0008,1110'
    assert one.group == 0x0008
    assert one.element == 0x1110

    assert isinstance(two, Sequence)
    assert two.value == 3
    assert two.wildcard == False

    assert isinstance(three, Segment)
    assert three.tag == '0008,1155'
    assert three.group == 0x0008
    assert three.element == 0x1155
    assert three.is_private == False

    assert isinstance(four, Sequence)
    assert four.value == 1
    assert four.wildcard == True

    assert isinstance(five, Segment)
    assert five.tag == '0008,1125'
    assert five.group == 0x0008
    assert five.element == 0x1125
    assert five.is_private == False

    assert isinstance(six, Sequence)
    assert six.value == 2
    assert six.wildcard == True

    assert isinstance(seven, Segment)
    assert seven.tag == '0023,0010'
    assert seven.group == 0x0023
    assert seven.element == 0x0010
    assert seven.is_private == False

    assert isinstance(eight, Sequence)
    assert eight.value == 9
    assert eight.wildcard == False

    assert isinstance(nine, Segment)
    assert nine.tag == '0029,"QUASAR",13'
    assert nine.group == 0x0029
    assert nine.owner == "QUASAR"
    assert nine.element == 0x13
    assert nine.is_private == True

def test_traverse_path_missing_initial_tag():
    """Tests traversing a path with a missing initial tag."""
    ds = make_test_dataset()

    path = "<(1234,0000)[90]>"
    parsed = parse(path)
    res = traverse(ds, parsed)
    assert len(res) == 0

def test_traverse_path_missing_seq():
    """Tests traversing a path with a missing sequence tag."""

    ds = make_test_dataset()
    path = "<(5200,9230)[325](0008,9124)[2](0008,2112)[0](0040,a170)[0](0008,0100)>"
    parsed = parse(path)
    res = traverse(ds, parsed)
    assert len(res) == 0

def test_traverse_path_missing_nested_tag():
    """Tests traversing a path with a missing nested tag."""

    ds = make_test_dataset()
    path = "<(5200,9230)[325](0008,9124)[0](0008,9999)[0](0040,a170)[0](0008,0100)>"
    parsed = parse(path)
    res = traverse(ds, parsed)
    assert len(res) == 0

def test_traverse_path_simple():
    ds = make_test_dataset()

    path = "<(5200,9230)[0](0008,9124)[0](0008,2112)[0](0040,a170)[0](0008,0100)>"

    parsed = parse(path)

    res = traverse(ds, parsed)

    assert len(res) == 1
    assert res[0].value == '121322'

def test_traverse_path_wild1():
    ds = make_test_dataset()

    path = "<(0008,1115)[<0>](0008,114a)[<0>](0008,1150)>"

    parsed = parse(path)

    res = traverse(ds, parsed)

    assert len(res) == 100
    assert res[0].value == '1.2.840.10008.5.1.4.1.1.128'

def test_traverse_path_wild2():
    ds = make_test_dataset()

    path = "<(5200,9230)[<0>](0008,9124)[<1>](0008,2112)[<2>](0040,a170)[<3>](0008,0100)>"

    parsed = parse(path)

    res = traverse(ds, parsed)

    assert len(res) == 1000
    assert res[0].value == '121322'

def test_traverse_private():
    ds = make_test_dataset()

    path = "<(0013,\"CTP\",11)>"

    parsed = parse(path)

    res = traverse(ds, parsed)

    assert len(res) == 1
    assert res[0].value == 'TCIA-Fake-Site'

def test_traverse_private_nested():
    ds = make_test_dataset()

    # path = "<(6000,0010)>[<0>](0029,\"INTELERAD MEDICAL SYSTEMS\",21)>"
    path = "<(6000,0010)>[<0>](0029,\"NEW CREATOR\",21)>"

    parsed = parse(path)

    res = traverse(ds, parsed)

    assert len(res) == 2
    assert res[0].value == 'PRIVATE_VALUE_21'

    
def test_edit():
    ds = make_test_dataset()

    path = "<(0013,\"CTP\",11)>"

    parsed = parse(path)

    res = traverse(ds, parsed)

    ele, *none = res
    
    ele.value = "Some New Value"

    # now do a second lookup
    res = traverse(ds, parsed)

    ele, *none = res

    assert ele.value == "Some New Value"
    
def test_edit_2():
    ds = make_test_dataset()

    path = "<(5200,9230)[<0>](0008,9124)[<0>](0008,2112)[<0>](0040,a170)[<0>](0008,0100)>"

    parsed = parse(path)

    res = traverse(ds, parsed)

    assert len(res) == 1000
    assert res[0].value == '121322'

    for ele in res:
        ele.VR = 'UI'
        ele.value = '122222'

        
    # test one of them
    path = "<(5200,9230)[0](0008,9124)[0](0008,2112)[4](0040,a170)[98](0008,0100)>"
    parsed = parse(path)
    res = traverse(ds, parsed)

    assert len(res) == 1
    assert res[0].value == '122222'
    assert res[0].VR == 'UI'
