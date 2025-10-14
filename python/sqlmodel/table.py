from datetime import date, datetime, timezone
from uuid import UUID

from sqlmodel import TIMESTAMP, Column, Field, SQLModel, UniqueConstraint
from uuid_extensions import uuid7


class SomeTable(SQLModel, table=True):
    __tablename__ = "some_table"
    model_config = {"arbitrary_types_allowed": True}
    __table_args__ = (
        UniqueConstraint("int_column", "bool_column", name="uix_int_bool"),
    )
    id: UUID = Field(primary_key=True, default_factory=uuid7)
    index_column: str = Field(index=True, unique=True)
    int_column: int
    bool_column: bool
    datetime_column: datetime
    date_column: date
    created_at: TIMESTAMP = Field(
        sa_column=Column(
            TIMESTAMP,
            nullable=False,
        ),
        default_factory=lambda: datetime.now(timezone.utc),
    )


class UseForeignKey(SQLModel, table=True):
    __tablename__ = "use_foreign_key"
    id: int = Field(primary_key=True, default_factory=uuid7)
    some_table_id: UUID = Field(foreign_key="some_table.id")
