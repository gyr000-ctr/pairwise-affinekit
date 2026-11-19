import math

import pytest

import affinekit

def _pop_restores():
    s = affinekit.TransformStack()
    p = s.apply((1, 1))
    s.push(_t(5, 5))
    s.pop()
    return s.apply((1, 1)) == p


def _perspective_divide():
    s = affinekit.TransformStack()
    s.push(_persp(0.5))
    x, y = s.apply((2.0, 0.0))
    return abs(x - 1.0) < 1e-9 and abs(y) < 1e-9


def _inverse_roundtrip():
    s = _stack()
    inv = s.inverse()
    p = (0.37, -1.24)
    q = s.apply(p)
    x = inv[0][0] * q[0] + inv[0][1] * q[1] + inv[0][2]
    y = inv[1][0] * q[0] + inv[1][1] * q[1] + inv[1][2]
    w = inv[2][0] * q[0] + inv[2][1] * q[1] + inv[2][2]
    return abs(x / w - p[0]) < 1e-9 and abs(y / w - p[1]) < 1e-9


def _compose_100():
    s = affinekit.TransformStack(max_depth=256)
    acc = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    for i in range(100):
        m = _rot(0.9) if i % 2 else _t(0.01, -0.02)
        s.push(m)
        acc = _mul(acc, m)
    p = (3.0, 4.0)
    out = s.apply(p)
    x = acc[0][0] * p[0] + acc[0][1] * p[1] + acc[0][2]
    y = acc[1][0] * p[0] + acc[1][1] * p[1] + acc[1][2]
    w = acc[2][0] * p[0] + acc[2][1] * p[1] + acc[2][2]
    return abs(out[0] - x / w) < 1e-9 and abs(out[1] - y / w) < 1e-9


def _mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def _decompose_roundtrip():
    s = affinekit.TransformStack()
    m = [[0, -3, 5], [2, 0, -1], [0, 0, 1]]
    tx, ty, rot, sx, sy = s.decompose(m)
    rebuilt = [[sx * math.cos(rot), -sy * math.sin(rot), tx],
               [sx * math.sin(rot), sy * math.cos(rot), ty],
               [0, 0, 1]]
    return all(abs(rebuilt[i][j] - m[i][j]) < 1e-9 for i in range(2) for j in range(3))


def _normals():
    s = affinekit.TransformStack()
    s.push(_scale(2, 1))
    nx, ny = s.apply_normal((0, 1))
    return abs(nx) < 1e-9 and abs(abs(ny) - 1.0) < 1e-9


def _depth_limit():
    s = affinekit.TransformStack(max_depth=2)
    s.push(_t(1, 1))
    s.push(_t(1, 1))
    return _raises(lambda: s.push(_t(1, 1))) and s.depth() == 2


def _clip():
    s = affinekit.TransformStack()
    return s.clip_line((1, 1), (2, 2), (0, 0, 4, 4)) == ((1, 1), (2, 2)) and s.clip_line((-2, -2), (-1, -1), (0, 0, 4, 4)) is None

CASES = [
    ("identity", lambda: affinekit.TransformStack().apply((2.0, 3.0)) == (2.0, 3.0)),
    ("push_pop", lambda: _pop_restores()),
    ("pop_empty", lambda: _raises(lambda: affinekit.TransformStack().pop())),
    ("perspective_divide", lambda: _perspective_divide()),
    ("w_non_positive", lambda: _raises(lambda: (lambda s: (s.push(_persp(1.0)), s.apply((1.0, 0.0))))(affinekit.TransformStack()))),
    ("inverse_roundtrip", lambda: _inverse_roundtrip()),
    ("compose_100", lambda: _compose_100()),
    ("decompose", lambda: _decompose_roundtrip()),
    ("decompose_perspective", lambda: _raises(lambda: affinekit.TransformStack().decompose(_persp(0.5)))),
    ("singular", lambda: _raises(lambda: affinekit.TransformStack().push([[1, 2, 0], [2, 4, 0], [0, 0, 1]]))),
    ("near_singular", lambda: _raises(lambda: affinekit.TransformStack(eps=1e-6).push([[1, 1, 0], [1, 1 + 1e-9, 0], [0, 0, 1]]))),
    ("normals", lambda: _normals()),
    ("depth_limit", lambda: _depth_limit()),
    ("bad_matrix", lambda: _raises(lambda: affinekit.TransformStack().push([[1, 0], [0, 1]]))),
    ("clip", lambda: _clip()),
]


@pytest.mark.parametrize("name,check", CASES, ids=[c[0] for c in CASES])
def test_spec(name, check):
    assert check() is True
