import pytest

import render_graph as rg


def graph(passes):
    return rg.RenderGraph(passes)


def test_single_pass():
    assert graph([{"id": "main", "reads": [], "writes": []}]).compile() == ["main"]


def test_explicit_after_is_respected():
    game = graph([
        {"id": "ui", "after": ["scene"]},
        {"id": "scene"},
    ])
    assert game.compile() == ["scene", "ui"]


def test_write_then_read_dependency():
    game = graph([
        {"id": "read", "reads": ["color"]},
        {"id": "write", "writes": ["color"]},
    ])
    assert game.compile() == ["write", "read"]


def test_read_then_write_dependency():
    game = graph([
        {"id": "write", "writes": ["color"]},
        {"id": "read", "reads": ["color"]},
    ])
    assert game.compile() == ["read", "write"]


def test_write_then_write_dependency():
    game = graph([
        {"id": "second", "writes": ["color"]},
        {"id": "first", "writes": ["color"]},
    ])
    assert game.compile() == ["first", "second"]


def test_cycle_raises():
    game = graph([
        {"id": "a", "after": ["b"]},
        {"id": "b", "after": ["a"]},
    ])
    with pytest.raises(ValueError):
        game.compile()


def test_duplicate_pass_id_raises():
    with pytest.raises(ValueError):
        graph([{"id": "a"}, {"id": "a"}])


def test_unknown_after_raises():
    game = graph([{"id": "a", "after": ["missing"]}])
    with pytest.raises(ValueError):
        game.compile()


def test_independent_passes_sort_by_id():
    game = graph([{"id": "b"}, {"id": "a"}])
    assert game.compile() == ["a", "b"]


def test_multiple_readers_after_writer():
    game = graph([
        {"id": "r2", "reads": ["color"]},
        {"id": "w", "writes": ["color"]},
        {"id": "r1", "reads": ["color"]},
    ])
    order = game.compile()
    assert order[0] == "w"
    assert set(order[1:]) == {"r1", "r2"}


def test_compile_is_idempotent():
    game = graph([{"id": "b"}, {"id": "a"}])
    assert game.compile() == ["a", "b"]
    assert game.compile() == ["a", "b"]


def test_invalid_resource_name_raises():
    with pytest.raises(ValueError):
        graph([{"id": "a", "reads": [""]}])


def test_self_dependency_raises():
    game = graph([{"id": "a", "after": ["a"]}])
    with pytest.raises(ValueError):
        game.compile()


def test_pass_without_resources_is_kept():
    game = graph([{"id": "solo"}])
    assert game.compile() == ["solo"]


def test_writer_before_all_readers_even_if_declared_later():
    game = graph([
        {"id": "r1", "reads": ["x"]},
        {"id": "r2", "reads": ["x"]},
        {"id": "w", "writes": ["x"]},
    ])
    order = game.compile()
    assert order.index("w") < order.index("r1")
    assert order.index("w") < order.index("r2")
