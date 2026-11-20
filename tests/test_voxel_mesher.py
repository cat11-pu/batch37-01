import pytest

import voxel_mesher as vm


def build(blocks):
    return vm.VoxelMesher(blocks).build()


def test_empty_grid_produces_empty_mesh():
    result = build({})
    assert result["quads"] == []
    assert result["vertices"] == []
    assert result["indices"] == []
    assert result["stats"] == {"quads": 0, "faces": 0, "vertices": 0, "indices": 0}


def test_single_block_has_six_quads():
    result = build({(0, 0, 0): 1})
    assert result["stats"]["quads"] == 6
    assert result["stats"]["faces"] == 6
    assert result["stats"]["vertices"] == 24
    assert result["stats"]["indices"] == 36


def test_single_block_vertices_cover_cube():
    result = build({(0, 0, 0): 1})
    xs = {v[0] for v in result["vertices"]}
    ys = {v[1] for v in result["vertices"]}
    zs = {v[2] for v in result["vertices"]}
    assert xs == {0, 1}
    assert ys == {0, 1}
    assert zs == {0, 1}


def test_indices_wind_each_quad():
    result = build({(0, 0, 0): 1})
    idx = result["indices"]
    assert len(idx) == 36
    for i in range(0, len(idx), 6):
        base = i // 6 * 4
        assert idx[i:i + 6] == [base, base + 1, base + 2, base, base + 2, base + 3]


def test_indices_stay_in_vertex_range():
    result = build({(0, 0, 0): 1, (2, 3, 4): 2})
    n = len(result["vertices"])
    assert all(0 <= i < n for i in result["indices"])


def test_vertex_count_matches_quad_count():
    result = build({(0, 0, 0): 1, (1, 0, 0): 1})
    assert len(result["vertices"]) == 4 * len(result["quads"])
    assert len(result["indices"]) == 6 * len(result["quads"])


def test_adjacent_blocks_cull_inner_faces():
    result = build({(0, 0, 0): 1, (1, 0, 0): 1})
    assert result["stats"]["faces"] == 10
    assert result["stats"]["quads"] == 6
    areas = sorted((q["size"][0] * q["size"][1]) for q in result["quads"])
    assert areas == [1, 1, 1, 1, 2, 2]


def test_different_block_types_still_cull():
    result = build({(0, 0, 0): 1, (1, 0, 0): 2})
    assert result["stats"]["faces"] == 10
    assert result["stats"]["quads"] == 6


def test_face_culling_counts_shared_sides():
    blocks = {(0, 0, 0): 1, (1, 0, 0): 1, (0, 1, 0): 1, (0, 0, 1): 1}
    result = build(blocks)
    assert result["stats"]["faces"] == 18


def test_greedy_merge_keeps_rectangle_shape():
    result = build({(0, 0, 0): 1, (1, 0, 0): 1})
    merged = [q for q in result["quads"] if q["size"][0] * q["size"][1] == 2]
    assert len(merged) == 2
    for q in merged:
        assert sorted(q["size"]) == [1, 2]


def test_winding_normal_matches_direction():
    result = build({(0, 0, 0): 1})
    verts = result["vertices"]
    for n, q in enumerate(result["quads"]):
        a, b, c = verts[4 * n], verts[4 * n + 1], verts[4 * n + 2]
        ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
        nx = uy * vz - uz * vy
        ny = uz * vx - ux * vz
        nz = ux * vy - uy * vx
        normal = (nx, ny, nz)[q["axis"]]
        assert normal * q["direction"] > 0


def test_insertion_order_does_not_change_mesh():
    a = {(0, 0, 0): 1, (1, 0, 0): 2, (0, 1, 0): 1}
    b = {(0, 1, 0): 1, (1, 0, 0): 2, (0, 0, 0): 1}
    first = build(a)
    assert first["stats"]["quads"] > 0
    assert first == build(b)


def test_build_is_repeatable():
    m = vm.VoxelMesher({(0, 0, 0): 1, (1, 0, 0): 1})
    first = m.build()
    assert first["stats"]["quads"] > 0
    assert m.build() == first


def test_zero_id_is_air():
    result = build({(0, 0, 0): 0, (1, 0, 0): 0})
    assert result["stats"]["quads"] == 0
    assert result["vertices"] == []


def test_negative_coordinates_are_supported():
    result = build({(-2, -3, -4): 1})
    assert result["stats"]["quads"] == 6
    assert min(v[0] for v in result["vertices"]) == -2
    assert min(v[1] for v in result["vertices"]) == -3
    assert min(v[2] for v in result["vertices"]) == -4
