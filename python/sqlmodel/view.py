from dataclasses import Field
from uuid import UUID

from sqlmodel import SQLModel

"""
View도 Table과 동일하게 정의.
alembic 에서는 import 하면 안됨. 
Optimizer Hint를 사용하려면 select(...).prefix_with("/*+ INDEX(my_table idx_col) */") 를 사용
"""

"""
DROP VIEW IF EXISTS some_view;
CREATE
SQL SECURITY INVOKER
VIEW some_view AS
SELECT id, index_column, int_column, bool_column
FROM some_table;
"""


class SomeView(SQLModel, table=True):
    __tablename__ = "some_view"
    id: UUID = Field(primary_key=True)
    index_column: str = Field(index=True, unique=True)
    int_column: int
    bool_column: bool
