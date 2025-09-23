from docxtpl import DocxTemplate

"""
String은 {{ key }} 로 치환
Image는 대체 텍스트에 key 작성
"""


def write_docx_with_template(
    template_path: str,
    out_path: str,
    metadata: dict[str, str | int | float],
    pic_dict: dict[str, str],  # key: 대체 텍스트, value: 이미지 경로
) -> None:
    doc = DocxTemplate(template_path)

    doc.render(metadata)
    for key, pic_path in pic_dict.items():
        doc.replace_pic(key, pic_path)

    doc.save(out_path)
