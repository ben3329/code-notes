import os
from enum import Enum
from tempfile import TemporaryDirectory

from fastapi import BackgroundTasks, FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()


@app.get("/file_response")
async def file_response(
    background_tasks: BackgroundTasks,
):
    tmp_dir = TemporaryDirectory(delete=False)
    filename = "sample.pdf"
    background_tasks.add_task(tmp_dir.cleanup)
    return FileResponse(
        os.path.join(tmp_dir.name, filename),
        media_type="application/pdf",
        filename=filename,
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Access-Control-Expose-Headers": "content-disposition",  # frontend에서 filename 가져오기 위해 필요
        },
        background=background_tasks,
    )


class TestEnum(Enum):
    A = "A"
    B = "B"
    C = "C"


class TestEnumOut(BaseModel):
    data: TestEnum


@app.get("/enum")
async def get_enum() -> list[str]:
    return [e.value for e in TestEnum]


@app.get("/enum_out")
async def get_enum_out() -> list[TestEnumOut]:
    return [TestEnumOut(data=e) for e in TestEnum]


# 이렇게 할 경우 frontend에서 code generator 사용 시 enum 객체로 인식 안됨
@app.get("/enum_invalid")
async def get_enum_invalid() -> list[TestEnum]:
    return list(TestEnum)
