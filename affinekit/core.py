"""affinekit 核心 API（初始未实现）。"""


class TransformStack:
    def __init__(self, max_depth=32, eps=1e-9):
        """构造栈"""
        raise NotImplementedError

    def push(self, matrix):
        """压入 3x3 矩阵（仿射或投影）"""
        raise NotImplementedError

    def pop(self):
        """弹出并返回"""
        raise NotImplementedError

    def depth(self):
        """当前深度"""
        raise NotImplementedError

    def reset(self):
        """清空"""
        raise NotImplementedError

    def apply(self, point):
        """透视除法后返回二维点"""
        raise NotImplementedError

    def apply_normal(self, vector):
        """逆转置变换法线"""
        raise NotImplementedError

    def compose(self):
        """返回合成矩阵"""
        raise NotImplementedError

    def inverse(self):
        """返回合成矩阵的逆"""
        raise NotImplementedError

    def decompose(self, matrix):
        """返回 (tx,ty,rotation,sx,sy)"""
        raise NotImplementedError

    def clip_line(self, p, q, rect):
        """裁剪线段"""
        raise NotImplementedError
