import pytest

import query_plan_guard as qg

TABLES = {
    "users": {"id", "name", "email", "tenant_id"},
    "orders": {"id", "user_id", "total", "tenant_id"},
}


def guard():
    return qg.QueryPlanGuard(TABLES)


def plan(**overrides):
    value = {
        "table": "users",
        "columns": ["id", "name"],
        "filters": [{"column": "id", "op": "=", "value": 1}],
        "order_by": [{"column": "name", "desc": False}],
        "limit": 50,
        "tenant": "t1",
    }
    value.update(overrides)
    return value


def test_valid_plan():
    result = guard().build(plan())
    assert result["table"] == "users"
    assert result["tenant"] == "t1"


def test_unknown_table_raises():
    with pytest.raises(ValueError):
        guard().build(plan(table="ghost"))


def test_unknown_column_raises():
    with pytest.raises(ValueError):
        guard().build(plan(columns=["ghost"]))


def test_invalid_operator_raises():
    with pytest.raises(ValueError):
        guard().build(plan(filters=[{"column": "id", "op": "DROP", "value": 1}]))


def test_missing_tenant_raises():
    with pytest.raises(ValueError):
        guard().build(plan(tenant=""))


def test_limit_zero_raises():
    with pytest.raises(ValueError):
        guard().build(plan(limit=0))


def test_limit_too_large_raises():
    with pytest.raises(ValueError):
        guard().build(plan(limit=1001))


def test_order_by_unknown_column_raises():
    with pytest.raises(ValueError):
        guard().build(plan(order_by=[{"column": "ghost", "desc": False}]))


def test_too_many_order_fields_raises():
    with pytest.raises(ValueError):
        guard().build(plan(order_by=[{"column": "id"}, {"column": "name"}, {"column": "email"}]))


def test_duplicate_columns_are_removed():
    result = guard().build(plan(columns=["id", "id", "name"]))
    assert result["columns"] == ["id", "name"]


def test_filter_column_must_be_allowed():
    with pytest.raises(ValueError):
        guard().build(plan(filters=[{"column": "ghost", "op": "=", "value": 1}]))


def test_non_dict_plan_raises():
    with pytest.raises(ValueError):
        guard().build([])


def test_empty_columns_raises():
    with pytest.raises(ValueError):
        guard().build(plan(columns=[]))


def test_plan_is_not_mutated():
    source = plan()
    result = guard().build(source)
    assert result["columns"] == ["id", "name"]
    assert source["columns"] == ["id", "name"]


def test_tenant_is_preserved():
    assert guard().build(plan(tenant="t2"))["tenant"] == "t2"
