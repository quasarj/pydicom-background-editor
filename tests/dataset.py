
from pydicom_background_editor.path import parse, traverse, Segment, Sequence
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