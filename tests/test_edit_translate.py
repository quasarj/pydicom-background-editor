from pydicom_background_editor.editor import Operation 

def test_translate_edits():

    data = {
        "edits": [
            {
                "arg1": "113100",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[0](0008,0100)",
                "tag_mode": "exact"
            },
            {
                "arg1": "DCM",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[0](0008,0102)",
                "tag_mode": "exact"
            },
            {
                "arg1": "Basic Application Confidentiality Profile",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[0](0008,0104)",
                "tag_mode": "exact"
            },
            {
                "arg1": "113101",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[1](0008,0100)",
                "tag_mode": "exact"
            },
            {
                "arg1": "DCM",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[1](0008,0102)",
                "tag_mode": "exact"
            },
            {
                "arg1": "Clean Pixel Data Option",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[1](0008,0104)",
                "tag_mode": "exact"
            },
            {
                "arg1": "113104",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[2](0008,0100)",
                "tag_mode": "exact"
            },
            {
                "arg1": "DCM",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[2](0008,0102)",
                "tag_mode": "exact"
            },
            {
                "arg1": "Clean Structured Content Option",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[2](0008,0104)",
                "tag_mode": "exact"
            },
            {
                "arg1": "113105",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[3](0008,0100)",
                "tag_mode": "exact"
            },
            {
                "arg1": "DCM",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[3](0008,0102)",
                "tag_mode": "exact"
            },
            {
                "arg1": "Clean Descriptors Option",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[3](0008,0104)",
                "tag_mode": "exact"
            },
            {
                "arg1": "113107",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[4](0008,0100)",
                "tag_mode": "exact"
            },
            {
                "arg1": "DCM",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[4](0008,0102)",
                "tag_mode": "exact"
            },
            {
                "arg1": "Retain Longitudinal Temporal Information Modified Dates Option",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[4](0008,0104)",
                "tag_mode": "exact"
            },
            {
                "arg1": "113108",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[5](0008,0100)",
                "tag_mode": "exact"
            },
            {
                "arg1": "DCM",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[5](0008,0102)",
                "tag_mode": "exact"
            },
            {
                "arg1": "Retain Patient Characteristics Option",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[5](0008,0104)",
                "tag_mode": "exact"
            },
            {
                "arg1": "113109",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[6](0008,0100)",
                "tag_mode": "exact"
            },
            {
                "arg1": "DCM",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[6](0008,0102)",
                "tag_mode": "exact"
            },
            {
                "arg1": "Retain Device Identity Option",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[6](0008,0104)",
                "tag_mode": "exact"
            },
            {
                "arg1": "113111",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[7](0008,0100)",
                "tag_mode": "exact"
            },
            {
                "arg1": "DCM",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[7](0008,0102)",
                "tag_mode": "exact"
            },
            {
                "arg1": "Retain Safe Private Option",
                "arg2": "",
                "op": "set_tag",
                "tag": "(0012,0064)[7](0008,0104)",
                "tag_mode": "exact"
            }
        ],
        "from_file": "/nas/new/public/posda/storage/e4/d7/69/e4d769e6bc213ee9c78148ff5c7e7f29",
        "to_file": "/nas/public/posda/cache2/edits/be82335e-d182-11f0-a69a-15f97ed50320/pat_148/studies/series_1252/201382653.dcm"
    }

    operations = Operation.translate_edits(data["edits"])
    print(operations)

if __name__ == "__main__":
    test_translate_edits()