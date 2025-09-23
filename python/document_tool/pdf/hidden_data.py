from collections import deque

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject,
    DictionaryObject,
    NameObject,
    NumberObject,
    TextStringObject,
)


def write_hidden_data(pdf_path: str, hidden_data: str) -> None:
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    if "/AcroForm" not in writer._root_object:
        acroform = DictionaryObject()
        acroform.update({NameObject("/Fields"): ArrayObject()})
        acroform_ref = writer._add_object(acroform)
        writer._root_object.update({NameObject("/AcroForm"): acroform_ref})

    acroform_ref = writer._root_object["/AcroForm"]
    acroform = acroform_ref.get_object()

    if NameObject("/Fields") not in acroform:
        acroform.update({NameObject("/Fields"): ArrayObject()})
    fields_array = acroform[NameObject("/Fields")]

    # 보이지 않는 텍스트 필드 생성 (/FT /Tx)
    # 필드 자체: 값 저장 + 내보내기 제외 + 읽기 전용
    hidden_field = DictionaryObject()
    hidden_field.update(
        {
            NameObject("/FT"): NameObject("/Tx"),  # Text field
            NameObject("/T"): TextStringObject("HiddenIdField"),  # 필드 이름
            NameObject("/V"): TextStringObject(hidden_data),  # 실제 값 저장
            NameObject("/Ff"): NumberObject(1 | 4),  # ReadOnly(1) + NoExport(4) = 5
        }
    )
    hidden_field_ref = writer._add_object(hidden_field)

    # 위젯 주석(/Subtype /Widget) 생성: 화면/인쇄에 표시되지 않도록 플래그 설정
    # /F 플래그: Hidden(2) + NoView(32) = 34  (Print 비트(4)는 켜지지 않음)
    widget_annot = DictionaryObject()
    widget_annot.update(
        {
            NameObject("/Type"): NameObject("/Annot"),
            NameObject("/Subtype"): NameObject("/Widget"),
            NameObject("/Rect"): ArrayObject(  # 0x0 사각형 (보이지 않음)
                [NumberObject(0), NumberObject(0), NumberObject(0), NumberObject(0)]
            ),
            NameObject("/F"): NumberObject(2 + 32),  # Hidden + NoView = 34
            NameObject("/Parent"): hidden_field_ref,  # 이 위젯이 속한 폼 필드
        }
    )
    widget_ref = writer._add_object(widget_annot)

    # 필드에 /Kids로 위젯 연결
    hidden_field.update({NameObject("/Kids"): ArrayObject([widget_ref])})

    # 첫 페이지의 /Annots에 위젯 추가
    first_page = writer.pages[0]
    if "/Annots" in first_page:
        first_page["/Annots"].append(widget_ref)
    else:
        first_page[NameObject("/Annots")] = ArrayObject([widget_ref])

    # 문서의 /AcroForm.Fields에 필드 등록
    fields_array.append(hidden_field_ref)

    with open(pdf_path, "wb") as f:
        writer.write(f)


def get_hidden_data_from_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    fields = reader.get_fields()
    if "HiddenIdField" in fields:
        return fields["HiddenIdField"]["/V"]
    raise ValueError("HiddenIdField not found in PDF")
