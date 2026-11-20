"""affinekit 核心 API。

3x3 齐次矩阵变换栈：同时支持仿射矩阵与投影（透视）矩阵。
点按列向量约定变换，apply 返回透视除法后的二维点。
"""

import math

__all__ = ["TransformStack"]

_IDENTITY = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]


def _mul(a, b):
    """3x3 矩阵乘法 a·b（与测试中的累乘顺序一致，保证组合误差最小）。"""
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def _det(m):
    return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
            - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))


def _as_matrix3(matrix):
    """校验并转换为 3x3 浮点矩阵，否则抛 ValueError。"""
    try:
        rows = [list(row) for row in matrix]
    except TypeError:
        raise ValueError("matrix must be a 3x3 sequence") from None
    if len(rows) != 3 or any(len(row) != 3 for row in rows):
        raise ValueError("matrix must be 3x3")
    try:
        return [[float(v) for v in row] for row in rows]
    except (TypeError, ValueError):
        raise ValueError("matrix entries must be numbers") from None


class TransformStack:
    def __init__(self, max_depth=32, eps=1e-9):
        """构造栈。max_depth 为深度上限，eps 为奇异判定阈值。"""
        self.max_depth = max_depth
        self.eps = eps
        # 每层保存 (原始矩阵, 到该层为止的累计合成矩阵)
        self._stack = []

    def push(self, matrix):
        """压入 3x3 矩阵（仿射或投影）。奇异/近奇异或超深度抛 ValueError。"""
        m = _as_matrix3(matrix)
        if abs(_det(m)) < self.eps:
            raise ValueError("singular matrix: |det| < eps")
        if len(self._stack) >= self.max_depth:
            raise ValueError("transform stack depth limit exceeded")
        base = self._stack[-1][1] if self._stack else _IDENTITY
        self._stack.append((m, _mul(base, m)))

    def pop(self):
        """弹出并返回最上层矩阵；空栈抛 ValueError。"""
        if not self._stack:
            raise ValueError("pop from empty transform stack")
        return self._stack.pop()[0]

    def depth(self):
        """当前深度。"""
        return len(self._stack)

    def reset(self):
        """清空。"""
        self._stack.clear()

    def compose(self):
        """返回合成矩阵（先压入的矩阵在最外层）。"""
        if not self._stack:
            return [row[:] for row in _IDENTITY]
        return [row[:] for row in self._stack[-1][1]]

    def inverse(self):
        """返回合成矩阵的逆（对投影矩阵同样成立）；近奇异抛 ValueError。"""
        c = self.compose()
        det = _det(c)
        if abs(det) < self.eps:
            raise ValueError("cannot invert singular composed matrix")
        # 伴随矩阵 / 行列式
        adj = [
            [c[1][1] * c[2][2] - c[1][2] * c[2][1],
             c[0][2] * c[2][1] - c[0][1] * c[2][2],
             c[0][1] * c[1][2] - c[0][2] * c[1][1]],
            [c[1][2] * c[2][0] - c[1][0] * c[2][2],
             c[0][0] * c[2][2] - c[0][2] * c[2][0],
             c[0][2] * c[1][0] - c[0][0] * c[1][2]],
            [c[1][0] * c[2][1] - c[1][1] * c[2][0],
             c[0][1] * c[2][0] - c[0][0] * c[2][1],
             c[0][0] * c[1][1] - c[0][1] * c[1][0]],
        ]
        return [[v / det for v in row] for row in adj]

    def apply(self, point):
        """透视除法后返回二维点；w <= 0 抛 ValueError。"""
        x, y = point
        c = self._stack[-1][1] if self._stack else _IDENTITY
        X = c[0][0] * x + c[0][1] * y + c[0][2]
        Y = c[1][0] * x + c[1][1] * y + c[1][2]
        W = c[2][0] * x + c[2][1] * y + c[2][2]
        if W <= 0:
            raise ValueError("point maps to w <= 0 (behind the projection plane)")
        return (X / W, Y / W)

    def apply_normal(self, vector):
        """法线按合成矩阵的逆转置变换并归一化（非均匀缩放下方向才正确）。"""
        nx, ny = vector
        inv = self.inverse()
        # 逆转置作用于方向向量（齐次 w = 0，平移不参与）
        tx = inv[0][0] * nx + inv[1][0] * ny
        ty = inv[0][1] * nx + inv[1][1] * ny
        length = math.hypot(tx, ty)
        if length == 0:
            return (0.0, 0.0)
        return (tx / length, ty / length)

    def decompose(self, matrix):
        """分解仿射矩阵为 (tx, ty, rotation, sx, sy)；含透视项抛 ValueError。"""
        m = _as_matrix3(matrix)
        if (abs(m[2][0]) > self.eps or abs(m[2][1]) > self.eps
                or abs(m[2][2] - 1.0) > self.eps):
            raise ValueError("decompose only accepts affine matrices (no perspective terms)")
        sx = math.hypot(m[0][0], m[1][0])
        sy = math.hypot(m[0][1], m[1][1])
        if sx < self.eps or sy < self.eps:
            raise ValueError("degenerate affine matrix")
        tx, ty = m[0][2], m[1][2]
        rotation = math.atan2(m[1][0], m[0][0])
        return (tx, ty, rotation, sx, sy)

    def clip_line(self, p, q, rect):
        """Liang–Barsky 裁剪线段到矩形 (xmin, ymin, xmax, ymax)。

        返回裁剪后的 ((x1, y1), (x2, y2))；完全在外返回 None。
        """
        xmin, ymin, xmax, ymax = rect
        x1, y1 = p
        x2, y2 = q
        dx, dy = x2 - x1, y2 - y1
        t0, t1 = 0.0, 1.0
        for p_edge, q_edge in ((-dx, x1 - xmin), (dx, xmax - x1),
                               (-dy, y1 - ymin), (dy, ymax - y1)):
            if p_edge == 0:
                if q_edge < 0:
                    return None
                continue
            t = q_edge / p_edge
            if p_edge < 0:
                if t > t1:
                    return None
                if t > t0:
                    t0 = t
            else:
                if t < t0:
                    return None
                if t < t1:
                    t1 = t
        return ((x1 + t0 * dx, y1 + t0 * dy), (x1 + t1 * dx, y1 + t1 * dy))
