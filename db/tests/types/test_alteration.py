from datetime import timedelta, date
from decimal import Decimal

import pytest
from psycopg2.errors import InvalidParameterValue
from sqlalchemy import Table, Column, MetaData
from sqlalchemy import String, Numeric
from sqlalchemy.exc import DataError
from db import types, columns, tables
from db.tests.types import fixtures
from db.types import alteration
from db.types.base import PostgresType, MathesarCustomType, get_qualified_name, get_available_types


# We need to set these variables when the file loads, or pytest can't
# properly detect the fixtures.  Importing them directly results in a
# flake8 unused import error, and a bunch of flake8 F811 errors.
engine_with_types = fixtures.engine_with_types
engine_email_type = fixtures.engine_email_type
temporary_testing_schema = fixtures.temporary_testing_schema


BIGINT = PostgresType.BIGINT.value.upper()
BOOLEAN = PostgresType.BOOLEAN.value.upper()
DECIMAL = PostgresType.DECIMAL.value.upper()
DOUBLE = PostgresType.DOUBLE_PRECISION.value.upper()
EMAIL = get_qualified_name(MathesarCustomType.EMAIL.value).upper()
FLOAT = PostgresType.FLOAT.value.upper()
INTEGER = PostgresType.INTEGER.value.upper()
INTERVAL = PostgresType.INTERVAL.value.upper()
NUMERIC = PostgresType.NUMERIC.value.upper()
REAL = PostgresType.REAL.value.upper()
SMALLINT = PostgresType.SMALLINT.value.upper()
DATE = PostgresType.DATE.value.upper()
VARCHAR = "VARCHAR"


ISCHEMA_NAME = "ischema_name"
TARGET_DICT = "target_dict"
REFLECTED_NAME = "reflected_name"
SUPPORTED_MAP_NAME = "supported_map_name"
VALID = "valid"
INVALID = "invalid"


MASTER_DB_TYPE_MAP_SPEC = {
    # This dict specifies the full map of what types can be cast to what
    # target types in Mathesar.  Format of each top-level key, val pair is:
    # <db_set_type_name>: {
    #     ISCHEMA_NAME: <name for looking up in result of get_available_types>,
    #     REFLECTED_NAME: <name for reflection of db type>,
    #     SUPPORTED_MAP_NAME: <optional; key in supported type map dictionaries>
    #     TARGET_DICT: {
    #         <target_type_1>: {
    #             VALID: [(in_val, out_val), (in_val, out_val)],
    #             INVALID: [in_val, in_val]
    #         },
    #         <target_type_2>: {
    #             INVALID: [(in_val, out_val), (in_val, out_val)]
    #             INVALID: [in_val, in_val]
    #         },
    #     }
    # }
    #
    # The TARGET_DICT is a dict with keys giving a valid target type for
    # alteration of a column of the given type, and values giving a dict
    # of valid and invalid casting values.  VALID value list is a list of
    # tuples representing the input and expected output, whereas INVALID
    # value list only needs input (since it should break, giving no output)
    BIGINT: {
        ISCHEMA_NAME: PostgresType.BIGINT.value,
        REFLECTED_NAME: BIGINT,
        TARGET_DICT: {
            BIGINT: {VALID: [(500, 500), (500000000000, 500000000000)]},
            BOOLEAN: {VALID: [(1, True), (0, False)], INVALID: [3]},
            DECIMAL: {VALID: [(1, Decimal('1.0'))]},
            DOUBLE: {VALID: [(3, 3.0)]},
            FLOAT: {VALID: [(4, 4.0)]},
            INTEGER: {VALID: [(500, 500)]},
            NUMERIC: {VALID: [(1, Decimal('1.0'))]},
            REAL: {VALID: [(5, 5.0)]},
            SMALLINT: {VALID: [(500, 500)]},
            VARCHAR: {VALID: [(3, "3")]},
        }
    },
    BOOLEAN: {
        ISCHEMA_NAME: PostgresType.BOOLEAN.value,
        REFLECTED_NAME: BOOLEAN,
        TARGET_DICT: {
            BIGINT: {VALID: [(True, 1), (False, 0)]},
            BOOLEAN: {VALID: [(True, True), (False, False)]},
            DECIMAL: {VALID: [(True, Decimal('1.0')), (False, Decimal('0'))]},
            DOUBLE: {VALID: [(True, 1.0), (False, 0.0)]},
            FLOAT: {VALID: [(True, 1.0), (False, 0.0)]},
            INTEGER: {VALID: [(True, 1), (False, 0)]},
            NUMERIC: {VALID: [(True, Decimal('1.0')), (False, Decimal('0'))]},
            REAL: {VALID: [(True, 1.0), (False, 0.0)]},
            SMALLINT: {VALID: [(True, 1), (False, 0)]},
            VARCHAR: {VALID: [(True, 'true'), (False, 'false')]},
        }
    },
    DECIMAL: {
        ISCHEMA_NAME: PostgresType.DECIMAL.value,
        REFLECTED_NAME: NUMERIC,
        TARGET_DICT: {
            BIGINT: {VALID: [(500, 500), (1234123412341234, 1234123412341234)]},
            BOOLEAN: {
                VALID: [(1, True), (0, False), (1.0, True), (0.0, False)],
                INVALID: [Decimal('1.3')]
            },
            DECIMAL: {VALID: [(1, 1.0)]},
            DOUBLE: {VALID: [(1, 1.0), (1.5, 1.5)]},
            FLOAT: {VALID: [(1, 1.0), (1.5, 1.5)]},
            INTEGER: {
                VALID: [(500, 500)],
                INVALID: [1234123412341234]
            },
            NUMERIC: {VALID: [(1, 1.0)]},
            REAL: {VALID: [(1, 1.0), (1.5, 1.5)]},
            SMALLINT: {
                VALID: [(500, 500)],
                INVALID: [12341234]
            },
            VARCHAR: {VALID: [(3, "3")]},
        }
    },
    DOUBLE: {
        ISCHEMA_NAME: PostgresType.DOUBLE_PRECISION.value,
        REFLECTED_NAME: DOUBLE,
        TARGET_DICT: {
            BIGINT: {VALID: [(500, 500)]},
            BOOLEAN: {VALID: [(1.0, True), (0.0, False)]},
            DECIMAL: {VALID: [(1, 1.0)]},
            DOUBLE: {VALID: [(1, 1.0), (1.5, 1.5)]},
            FLOAT: {VALID: [(1, 1.0), (1.5, 1.5)]},
            INTEGER: {VALID: [(500, 500)]},
            NUMERIC: {VALID: [(1, 1.0)]},
            REAL: {VALID: [(1, 1.0), (1.5, 1.5)]},
            SMALLINT: {VALID: [(500, 500)]},
            VARCHAR: {VALID: [(3, "3")]},
        }
    },
    EMAIL: {
        ISCHEMA_NAME: get_qualified_name(MathesarCustomType.EMAIL.value),
        SUPPORTED_MAP_NAME: MathesarCustomType.EMAIL.value,
        REFLECTED_NAME: EMAIL,
        TARGET_DICT: {
            EMAIL: {VALID: [("alice@example.com", "alice@example.com")]},
            VARCHAR: {VALID: [("bob@example.com", "bob@example.com")]},
        }
    },
    FLOAT: {
        ISCHEMA_NAME: PostgresType.FLOAT.value,
        REFLECTED_NAME: DOUBLE,
        TARGET_DICT: {
            BIGINT: {VALID: [(500, 500)]},
            BOOLEAN: {VALID: [(1.0, True), (0.0, False)], INVALID: [1.234]},
            DECIMAL: {VALID: [(1, 1.0)]},
            DOUBLE: {VALID: [(1, 1.0), (1.5, 1.5)]},
            FLOAT: {VALID: [(1, 1.0), (1.5, 1.5)]},
            INTEGER: {VALID: [(500, 500), (-5, -5)], INVALID: [-3.234, 234.34]},
            NUMERIC: {VALID: [(1, 1.0)]},
            REAL: {VALID: [(1, 1.0), (1.5, 1.5)]},
            SMALLINT: {VALID: [(500, 500), (-5, -5)], INVALID: [-3.234, 234.34]},
            VARCHAR: {VALID: [(3, "3")]},
        }
    },
    INTEGER: {
        ISCHEMA_NAME: PostgresType.INTEGER.value,
        REFLECTED_NAME: INTEGER,
        TARGET_DICT: {
            BIGINT: {VALID: [(500, 500)]},
            BOOLEAN: {VALID: [(1, True), (0, False)], INVALID: [3]},
            DECIMAL: {VALID: [(1, Decimal('1.0'))]},
            DOUBLE: {VALID: [(3, 3.0)]},
            FLOAT: {VALID: [(4, 4.0)]},
            INTEGER: {VALID: [(500, 500)]},
            NUMERIC: {VALID: [(1, Decimal('1.0'))]},
            REAL: {VALID: [(5, 5.0)]},
            SMALLINT: {VALID: [(500, 500)]},
            VARCHAR: {VALID: [(3, "3")]},
        }
    },
    INTERVAL: {
        ISCHEMA_NAME: PostgresType.INTERVAL.value,
        REFLECTED_NAME: INTERVAL,
        TARGET_DICT: {
            INTERVAL: {
                VALID: [
                    (
                        timedelta(days=3, hours=3, minutes=5, seconds=30),
                        timedelta(days=3, hours=3, minutes=5, seconds=30),
                    )
                ]
            },
            VARCHAR: {
                VALID: [
                    (
                        timedelta(days=3, hours=3, minutes=5, seconds=30),
                        '3 days 03:05:30'
                    )
                ]
            },
        }
    },
    NUMERIC: {
        ISCHEMA_NAME: PostgresType.NUMERIC.value,
        REFLECTED_NAME: NUMERIC,
        TARGET_DICT: {
            BIGINT: {VALID: [(500, 500)]},
            BOOLEAN: {
                VALID: [(1, True), (0, False), (1.0, True), (0.0, False)],
                INVALID: [42, -1]
            },
            DECIMAL: {VALID: [(1, 1.0)]},
            DOUBLE: {VALID: [(1, 1.0), (1.5, 1.5)]},
            FLOAT: {VALID: [(1, 1.0), (1.5, 1.5)]},
            INTEGER: {
                VALID: [(500, 500)],
                INVALID: [1.234, 1234123412341234]
            },
            NUMERIC: {VALID: [(1, 1.0)]},
            REAL: {VALID: [(1, 1.0), (1.5, 1.5)]},
            SMALLINT: {
                VALID: [(500, 500)],
                INVALID: [1.234, 12341234]
            },
            VARCHAR: {VALID: [(3, "3")]},
        }
    },
    REAL: {
        ISCHEMA_NAME: PostgresType.REAL.value,
        REFLECTED_NAME: REAL,
        TARGET_DICT: {
            BIGINT: {VALID: [(500, 500)]},
            BOOLEAN: {
                VALID: [(1.0, True), (0.0, False)],
                INVALID: [42, -1]
            },
            DECIMAL: {VALID: [(1, 1.0)]},
            DOUBLE: {VALID: [(1, 1.0), (1.5, 1.5)]},
            FLOAT: {VALID: [(1, 1.0), (1.5, 1.5)]},
            INTEGER: {
                VALID: [(500, 500)],
                INVALID: [3.345]
            },
            NUMERIC: {VALID: [(1, 1.0)]},
            REAL: {VALID: [(1, 1.0), (1.5, 1.5)]},
            SMALLINT: {
                VALID: [(500, 500)],
                INVALID: [3.345]
            },
            VARCHAR: {VALID: [(3, "3")]},
        }
    },
    SMALLINT: {
        ISCHEMA_NAME: PostgresType.SMALLINT.value,
        REFLECTED_NAME: SMALLINT,
        TARGET_DICT: {
            BIGINT: {VALID: [(500, 500)]},
            BOOLEAN: {VALID: [(1, True), (0, False)], INVALID: [3]},
            DECIMAL: {VALID: [(1, Decimal('1.0'))]},
            DOUBLE: {VALID: [(3, 3.0)]},
            FLOAT: {VALID: [(4, 4.0)]},
            INTEGER: {VALID: [(500, 500)]},
            NUMERIC: {VALID: [(1, Decimal('1.0'))]},
            REAL: {VALID: [(5, 5.0)]},
            SMALLINT: {VALID: [(500, 500)]},
            VARCHAR: {VALID: [(3, "3")]},
        }
    },
    DATE: {
        ISCHEMA_NAME: PostgresType.DATE.value,
        REFLECTED_NAME: DATE,
        TARGET_DICT: {
            DATE: {VALID: [(date(1999, 1, 18), date(1999, 1, 18))]},
            VARCHAR: {VALID: [(date(1999, 1, 18), "1999-01-18")]},
        },
    },
    VARCHAR: {
        ISCHEMA_NAME: PostgresType.CHARACTER_VARYING.value,
        SUPPORTED_MAP_NAME: "varchar",
        REFLECTED_NAME: VARCHAR,
        TARGET_DICT: {
            BIGINT: {
                VALID: [("432", 432), ("1234123412341234", 1234123412341234)],
                INVALID: ["1.2234"]
            },
            BOOLEAN: {
                VALID: [
                    ("true", True), ("false", False), ("t", True), ("f", False)
                ],
                INVALID: ["cat"],
            },
            DECIMAL: {
                VALID: [("1.2", Decimal("1.2")), ("1", Decimal("1"))],
                INVALID: ["abc"],
            },
            DOUBLE: {
                VALID: [("1.234", 1.234)],
                INVALID: ["bat"],
            },
            EMAIL: {
                VALID: [("alice@example.com", "alice@example.com")],
                INVALID: ["alice-example.com"]
            },
            FLOAT: {
                VALID: [("1.234", 1.234)],
                INVALID: ["bat"],
            },
            INTEGER: {
                VALID: [("432", 432)],
                INVALID: ["1.2234"]
            },
            INTERVAL: {
                VALID: [
                    ("1 day", timedelta(days=1)),
                    ("1 week", timedelta(days=7)),
                    ("3:30", timedelta(hours=3, minutes=30)),
                    ("00:03:30", timedelta(minutes=3, seconds=30)),
                ],
                INVALID: ["1 potato", "3"],
            },
            NUMERIC: {
                VALID: [
                    ("1.2", Decimal("1.2")),
                    ("1", Decimal("1")),
                ],
                INVALID: ["not a number"],
            },
            REAL: {
                VALID: [("1.234", 1.234)],
                INVALID: ["real"]
            },
            SMALLINT: {
                VALID: [("432", 432)],
                INVALID: ["1.2234"]
            },
            DATE: {
                VALID: [
                    ("1999-01-18", date(1999, 1, 18)),
                    ("1/18/1999", date(1999, 1, 18)),
                    ("jan-1999-18", date(1999, 1, 18)),
                    ("19990118", date(1999, 1, 18)),
                ],
                INVALID: [
                    "18/1/1999",
                    "not a date",
                    "1234",
                ]
            },
            VARCHAR: {VALID: [("a string", "a string")]},
        }
    }
}


def test_get_alter_column_types_with_custom_engine(engine_with_types):
    type_dict = alteration.get_supported_alter_column_types(engine_with_types)
    assert all(
        [
            type_ in type_dict.values()
            for type_ in types.CUSTOM_TYPE_DICT.values()
        ]
    )


def test_get_alter_column_types_with_unfriendly_names(engine_with_types):
    type_dict = alteration.get_supported_alter_column_types(
        engine_with_types, friendly_names=False
    )
    assert all(
        [
            type_dict[type_]().compile(dialect=engine_with_types.dialect) == type_
            for type_ in type_dict
        ]
    )


type_test_list = [
    (
        val[ISCHEMA_NAME],
        MASTER_DB_TYPE_MAP_SPEC[target].get(
            SUPPORTED_MAP_NAME, MASTER_DB_TYPE_MAP_SPEC[target][ISCHEMA_NAME]
        ),
        {},
        MASTER_DB_TYPE_MAP_SPEC[target][REFLECTED_NAME]
    )
    for val in MASTER_DB_TYPE_MAP_SPEC.values()
    for target in val[TARGET_DICT]
] + [
    (val[ISCHEMA_NAME], "numeric", {"precision": 5}, "NUMERIC(5, 0)")
    for val in MASTER_DB_TYPE_MAP_SPEC.values() if NUMERIC in val[TARGET_DICT]
] + [
    (val[ISCHEMA_NAME], "numeric", {"precision": 5, "scale": 3}, "NUMERIC(5, 3)")
    for val in MASTER_DB_TYPE_MAP_SPEC.values() if NUMERIC in val[TARGET_DICT]
] + [
    (val[ISCHEMA_NAME], "decimal", {"precision": 5}, "NUMERIC(5, 0)")
    for val in MASTER_DB_TYPE_MAP_SPEC.values() if DECIMAL in val[TARGET_DICT]
] + [
    (val[ISCHEMA_NAME], "decimal", {"precision": 5, "scale": 3}, "NUMERIC(5, 3)")
    for val in MASTER_DB_TYPE_MAP_SPEC.values() if DECIMAL in val[TARGET_DICT]
]


@pytest.mark.parametrize(
    "type_,target_type,options,expect_type", type_test_list
)
def test_alter_column_type_alters_column_type(
        engine_email_type, type_, target_type, options, expect_type
):
    """
    The massive number of cases make sure all type casting functions at
    least pass a smoke test for each type mapping defined in
    MASTER_DB_TYPE_MAP_SPEC above.
    """
    engine, schema = engine_email_type
    available_types = get_available_types(engine)
    TABLE_NAME = "testtable"
    COLUMN_NAME = "testcol"
    metadata = MetaData(bind=engine)
    input_table = Table(
        TABLE_NAME,
        metadata,
        Column(COLUMN_NAME, available_types[type_]),
        schema=schema
    )
    input_table.create()
    with engine.begin() as conn:
        alteration.alter_column_type(
            input_table,
            COLUMN_NAME,
            engine,
            conn,
            target_type,
            options
        )
    metadata = MetaData(bind=engine)
    metadata.reflect()
    actual_column = Table(
        TABLE_NAME,
        metadata,
        schema=schema,
        autoload_with=engine
    ).columns[COLUMN_NAME]
    actual_type = actual_column.type.compile(dialect=engine.dialect)
    assert actual_type == expect_type


type_test_data_args_list = [
    (Numeric(precision=5), "numeric", {}, 1, 1.0),
    (Numeric(precision=5, scale=2), "numeric", {}, 1, 1.0),
    (Numeric, "numeric", {"precision": 5, "scale": 2}, 1.234, Decimal("1.23")),
    # test that rounding is as intended
    (Numeric, "numeric", {"precision": 5, "scale": 2}, 1.235, Decimal("1.24")),
    (String, "numeric", {"precision": 5, "scale": 2}, "500.134", Decimal("500.13")),
]


@pytest.mark.parametrize(
    "type_,target_type,options,value,expect_value", type_test_data_args_list
)
def test_alter_column_type_casts_column_data_args(
        engine_email_type, type_, target_type, options, value, expect_value,
):
    engine, schema = engine_email_type
    TABLE_NAME = "testtable"
    COLUMN_NAME = "testcol"
    metadata = MetaData(bind=engine)
    input_table = Table(
        TABLE_NAME,
        metadata,
        Column(COLUMN_NAME, type_),
        schema=schema
    )
    input_table.create()
    ins = input_table.insert(values=(value,))
    with engine.begin() as conn:
        conn.execute(ins)
        alteration.alter_column_type(
            input_table,
            COLUMN_NAME,
            engine,
            conn,
            target_type,
            options
        )
    metadata = MetaData(bind=engine)
    metadata.reflect()
    actual_table = Table(
        TABLE_NAME,
        metadata,
        schema=schema,
        autoload_with=engine
    )
    sel = actual_table.select()
    with engine.connect() as conn:
        res = conn.execute(sel).fetchall()
    actual_value = res[0][0]
    assert actual_value == expect_value


type_test_data_gen_list = [
    (
        val[ISCHEMA_NAME],
        MASTER_DB_TYPE_MAP_SPEC[target].get(
            SUPPORTED_MAP_NAME, MASTER_DB_TYPE_MAP_SPEC[target][ISCHEMA_NAME]
        ),
        in_val,
        out_val,
    )
    for val in MASTER_DB_TYPE_MAP_SPEC.values()
    for target in val[TARGET_DICT]
    for in_val, out_val in val[TARGET_DICT][target].get(VALID, [])
]


@pytest.mark.parametrize(
    "source_type,target_type,in_val,out_val", type_test_data_gen_list
)
def test_alter_column_casts_data_gen(
        engine_email_type, source_type, target_type, in_val, out_val
):
    engine, schema = engine_email_type
    available_types = get_available_types(engine)
    TABLE_NAME = "testtable"
    COLUMN_NAME = "testcol"
    metadata = MetaData(bind=engine)
    input_table = Table(
        TABLE_NAME,
        metadata,
        Column(COLUMN_NAME, available_types[source_type], server_default=str(in_val)),
        schema=schema
    )
    input_table.create()
    ins = input_table.insert(values=(in_val,))
    with engine.begin() as conn:
        conn.execute(ins)
        alteration.alter_column_type(
            input_table,
            COLUMN_NAME,
            engine,
            conn,
            target_type
        )
    metadata = MetaData(bind=engine)
    metadata.reflect()
    actual_table = Table(TABLE_NAME, metadata, schema=schema, autoload_with=engine)
    sel = actual_table.select()
    with engine.connect() as conn:
        res = conn.execute(sel).fetchall()
    actual_value = res[0][0]
    assert actual_value == out_val
    table_oid = tables.get_oid_from_table(TABLE_NAME, schema, engine)
    actual_default = columns.get_column_default(table_oid, 0, engine)
    assert actual_default == out_val


type_test_bad_data_gen_list = [
    (
        val[ISCHEMA_NAME],
        MASTER_DB_TYPE_MAP_SPEC[target].get(
            SUPPORTED_MAP_NAME, MASTER_DB_TYPE_MAP_SPEC[target][ISCHEMA_NAME]
        ),
        data,
    )
    for val in MASTER_DB_TYPE_MAP_SPEC.values()
    for target in val[TARGET_DICT]
    for data in val[TARGET_DICT][target].get(INVALID, [])
]


@pytest.mark.parametrize(
    "type_,target_type,value", type_test_bad_data_gen_list
)
def test_alter_column_type_raises_on_bad_column_data(
        engine_email_type, type_, target_type, value,
):
    engine, schema = engine_email_type
    available_types = get_available_types(engine)
    TABLE_NAME = "testtable"
    COLUMN_NAME = "testcol"
    metadata = MetaData(bind=engine)
    input_table = Table(
        TABLE_NAME,
        metadata,
        Column(COLUMN_NAME, available_types[type_]),
        schema=schema
    )
    input_table.create()
    ins = input_table.insert(values=(value,))
    with engine.begin() as conn:
        conn.execute(ins)
        with pytest.raises(Exception):
            alteration.alter_column_type(
                input_table,
                COLUMN_NAME,
                engine,
                conn,
                target_type
            )


def test_alter_column_type_raises_on_bad_parameters(
        engine_email_type,
):
    engine, schema = engine_email_type
    TABLE_NAME = "testtable"
    COLUMN_NAME = "testcol"
    metadata = MetaData(bind=engine)
    input_table = Table(
        TABLE_NAME,
        metadata,
        Column(COLUMN_NAME, Numeric),
        schema=schema
    )
    input_table.create()
    ins = input_table.insert(values=(5.3,))
    bad_options = {"precision": 3, "scale": 4}  # scale must be smaller than precision
    with engine.begin() as conn:
        conn.execute(ins)
        with pytest.raises(DataError) as e:
            alteration.alter_column_type(
                input_table,
                COLUMN_NAME,
                engine,
                conn,
                "numeric",
                bad_options
            )
            assert e.orig == InvalidParameterValue


def test_get_column_cast_expression_unchanged(engine_with_types):
    target_type = "numeric"
    col_name = "my_column"
    column = Column(col_name, Numeric)
    cast_expr = alteration.get_column_cast_expression(
        column, target_type, engine_with_types
    )
    assert cast_expr == column


def test_get_column_cast_expression_change(engine_with_types):
    target_type = "boolean"
    col_name = "my_column"
    column = Column(col_name, Numeric)
    cast_expr = alteration.get_column_cast_expression(
        column, target_type, engine_with_types
    )
    assert str(cast_expr) == f"mathesar_types.cast_to_boolean({col_name})"


def test_get_column_cast_expression_change_quotes(engine_with_types):
    target_type = "boolean"
    col_name = "A Column Needing Quotes"
    column = Column(col_name, Numeric)
    cast_expr = alteration.get_column_cast_expression(
        column, target_type, engine_with_types
    )
    assert str(cast_expr) == f'mathesar_types.cast_to_boolean("{col_name}")'


def test_get_column_cast_expression_unsupported(engine_with_types):
    target_type = "this_type_does_not_exist"
    column = Column("colname", Numeric)
    with pytest.raises(alteration.UnsupportedTypeException):
        alteration.get_column_cast_expression(
            column, target_type, engine_with_types
        )


cast_expr_numeric_option_list = [
    (Numeric, {"precision": 3}, 'CAST(colname AS NUMERIC(3))'),
    (Numeric, {"precision": 3, "scale": 2}, 'CAST(colname AS NUMERIC(3, 2))'),
    (Numeric, {"precision": 3, "scale": 2}, 'CAST(colname AS NUMERIC(3, 2))'),
    (
        String,
        {"precision": 3, "scale": 2},
        'CAST(mathesar_types.cast_to_numeric(colname) AS NUMERIC(3, 2))'
    )
]


@pytest.mark.parametrize("type_,options,expect_cast_expr", cast_expr_numeric_option_list)
def test_get_column_cast_expression_numeric_options(
        engine_with_types, type_, options, expect_cast_expr
):
    target_type = "numeric"
    column = Column("colname", type_)
    cast_expr = alteration.get_column_cast_expression(
        column, target_type, engine_with_types, type_options=options,
    )
    assert str(cast_expr) == expect_cast_expr


expect_cast_tuples = [
    (key, [target for target in val[TARGET_DICT]])
    for key, val in MASTER_DB_TYPE_MAP_SPEC.items()
]


@pytest.mark.parametrize("source_type,expect_target_types", expect_cast_tuples)
def test_get_full_cast_map(engine_with_types, source_type, expect_target_types):
    actual_cast_map = alteration.get_full_cast_map(engine_with_types)
    actual_target_types = actual_cast_map[source_type]
    assert len(actual_target_types) == len(expect_target_types)
    assert sorted(actual_target_types) == sorted(expect_target_types)


def test_get_column_cast_records(engine_email_type):
    COL1 = "col1"
    COL2 = "col2"
    col1 = Column(COL1, String)
    col2 = Column(COL2, String)
    column_list = [col1, col2]
    engine, schema = engine_email_type
    table_name = "table_with_columns"
    table = tables.create_mathesar_table(
        table_name, schema, column_list, engine
    )
    ins = table.insert().values(
        [{COL1: 'one', COL2: 1}, {COL1: 'two', COL2: 2}]
    )
    with engine.begin() as conn:
        conn.execute(ins)
    COL1_MOD = COL1 + "_mod"
    COL2_MOD = COL2 + "_mod"
    column_definitions = [
        {"name": "mathesar_id", "type": "INTEGER"},
        {"name": COL1_MOD, "type": "VARCHAR"},
        {"name": COL2_MOD, "type": "NUMERIC"},
    ]
    records = alteration.get_column_cast_records(engine, table, column_definitions)
    for record in records:
        assert (
            type(record[COL1 + "_mod"]) == str
            and type(record[COL2 + "_mod"]) == Decimal
        )


def test_get_column_cast_records_options(engine_email_type):
    COL1 = "col1"
    COL2 = "col2"
    col1 = Column(COL1, String)
    col2 = Column(COL2, String)
    column_list = [col1, col2]
    engine, schema = engine_email_type
    table_name = "table_with_columns"
    table = tables.create_mathesar_table(
        table_name, schema, column_list, engine
    )
    ins = table.insert().values(
        [{COL1: 'one', COL2: 1}, {COL1: 'two', COL2: 2}]
    )
    with engine.begin() as conn:
        conn.execute(ins)
    COL1_MOD = COL1 + "_mod"
    COL2_MOD = COL2 + "_mod"
    column_definitions = [
        {"name": "mathesar_id", "type": "INTEGER"},
        {"name": COL1_MOD, "type": "VARCHAR"},
        {"name": COL2_MOD, "type": "NUMERIC", "type_options": {"precision": 5, "scale": 2}},
    ]
    records = alteration.get_column_cast_records(engine, table, column_definitions)
    for record in records:
        assert (
            type(record[COL1 + "_mod"]) == str
            and type(record[COL2 + "_mod"]) == Decimal
        )
