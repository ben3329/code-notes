import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


def drop_foreign_key_from_column_name(table_name, column_name):
    inspector = inspect(op.get_bind())
    foreign_keys = inspector.get_foreign_keys(table_name)
    for fk in foreign_keys:
        if column_name in fk["constrained_columns"]:
            op.drop_constraint(fk["name"], table_name, type_="foreignkey")
            break


def _check_referencing_tables(referenced_table_name, referenced_column_name):
    # Connect to the database
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    refer_info = []

    # Get all tables
    for table_name in inspector.get_table_names():
        # Get foreign keys for each table
        foreign_keys = inspector.get_foreign_keys(table_name)

        for fk in foreign_keys:
            if (
                fk["referred_table"] == referenced_table_name
                and referenced_column_name in fk["referred_columns"]
            ):
                refer_info.append(
                    {
                        "table": table_name,
                        "columns": fk["constrained_columns"],
                        "fk_name": fk["name"],
                        "fk_options": fk["options"],  # 'ondelete', 'onupdate'
                        "org_table": fk["referred_table"],
                        "org_columns": fk["referred_columns"],
                    }
                )
    return refer_info


def _drop_foreign_keys(refer_info):
    for ref in refer_info:
        op.drop_constraint(ref["fk_name"], ref["table"], type_="foreignkey")


def _create_foreign_keys(refer_info):
    for ref in refer_info:
        op.create_foreign_key(
            ref["fk_name"],
            ref["table"],
            ref["org_table"],
            ref["columns"],
            ref["org_columns"],
            ondelete=ref["fk_options"].get("ondelete"),
            onupdate=ref["fk_options"].get("onupdate"),
        )


def _get_column_type_str(column_info):
    column_type = column_info["type"]
    if column_type.length:
        column_type_str = f"{column_type.__visit_name__.upper()}({column_type.length})"
    else:
        column_type_str = column_type.__visit_name__.upper()
    return column_type_str


def _get_column_info_str(column_info):
    info_list = []
    info_list.append("NOT NULL" if not column_info["nullable"] else "NULL")
    if column_info["default"] is not None:
        info_list.append(f"DEFAULT {column_info['default']}")
    if column_info["comment"]:
        info_list.append(f"COMMENT '{column_info['comment']}'")
    column_info_str = " ".join(info_list)
    return column_info_str


def _get_column_info(table, column_name):
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = inspector.get_columns(table)
    for column in columns:
        if column["name"] == column_name:
            return column
    return None


def _check_is_foreign_key(table_name, column_name):
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    foreign_keys = inspector.get_foreign_keys(table_name)
    for fk in foreign_keys:
        if column_name in fk["constrained_columns"]:
            return True
    return False


def set_collation_for_all():
    character_set = "utf8mb4"
    collation = "utf8mb4_bin"
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Change the collation of the entire schema (database)
    database_name = conn.engine.url.database
    op.execute(
        f"ALTER DATABASE {database_name} CHARACTER SET {character_set} COLLATE {collation};"
    )

    tables = inspector.get_table_names()
    for table in tables:
        # Change the collation for each text column in the table
        columns = inspector.get_columns(table)
        for column in columns:
            if isinstance(column["type"], (sa.String, sa.Text)):
                if column["type"].collation == collation:
                    continue
                if _check_is_foreign_key(table, column["name"]):
                    continue
                refer_info = _check_referencing_tables(table, column["name"])
                if refer_info:  # If there are foreign keys, we need to drop them first
                    _drop_foreign_keys(refer_info)
                    org_columns = refer_info[0]["org_columns"]
                    for org_column in org_columns:
                        column_info = _get_column_info(table, org_column)
                        if isinstance(column_info["type"], (sa.String, sa.Text)):
                            column_type_str = _get_column_type_str(column_info)
                            column_info_str = _get_column_info_str(column_info)
                            op.execute(
                                f"ALTER TABLE {table} MODIFY `{org_column}` {column_type_str} CHARACTER SET {character_set} COLLATE {collation} {column_info_str};"
                            )
                    for ref in refer_info:
                        for fk_column in ref["columns"]:
                            fk_column_info = _get_column_info(ref["table"], fk_column)
                            if isinstance(fk_column_info["type"], (sa.String, sa.Text)):
                                column_type_str = _get_column_type_str(fk_column_info)
                                column_info_str = _get_column_info_str(fk_column_info)
                                op.execute(
                                    f"ALTER TABLE {ref['table']} MODIFY `{fk_column}` {column_type_str} CHARACTER SET {character_set} COLLATE {collation} {column_info_str};"
                                )

                    _create_foreign_keys(refer_info)
                else:  # No foreign key
                    column_type_str = _get_column_type_str(column)
                    column_info_str = _get_column_info_str(column)

                    op.execute(
                        f"ALTER TABLE {table} MODIFY `{column['name']}` {column_type_str} CHARACTER SET {character_set} COLLATE {collation} {column_info_str};"
                    )
    for table in tables:
        # Change the collation of the table
        op.execute(
            f"ALTER TABLE {table} CONVERT TO CHARACTER SET {character_set} COLLATE {collation};"
        )
