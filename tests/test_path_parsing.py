from pydicom_background_editor.path import parse, traverse, Segment, Sequence


def test_parse_path_simple_segment():
    """Test parsing of a simple DICOM path segment."""
    simple_path_segment = "<(0008,1110)>"
    parsed = parse(simple_path_segment)

    assert len(parsed) == 1
    seg = parsed[0]
    assert isinstance(seg, Segment)
    assert seg.tag == "0008,1110"
    assert seg.group == 0x0008
    assert seg.element == 0x1110


def test_parse_path_concrete_index():
    """Tests parsing of a DICOM path segment with a concrete index."""
    element = "<(0008,1110)[1]>"
    parsed = parse(element)

    assert len(parsed) == 2
    one, two = parsed

    assert isinstance(one, Segment)
    assert one.tag == "0008,1110"
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
    assert one.tag == "0008,1110"
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
    assert one.tag == "0008,1110"
    assert one.group == 0x0008
    assert one.element == 0x1110

    assert isinstance(two, Sequence)
    assert two.value == 3
    assert two.wildcard == False

    assert isinstance(three, Segment)
    assert three.tag == "0008,1155"
    assert three.group == 0x0008
    assert three.element == 0x1155
    assert three.is_private == False

    assert isinstance(four, Sequence)
    assert four.value == 1
    assert four.wildcard == True

    assert isinstance(five, Segment)
    assert five.tag == "0008,1125"
    assert five.group == 0x0008
    assert five.element == 0x1125
    assert five.is_private == False

    assert isinstance(six, Sequence)
    assert six.value == 2
    assert six.wildcard == True

    assert isinstance(seven, Segment)
    assert seven.tag == "0023,0010"
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
