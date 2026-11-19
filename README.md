# pairwise-affinekit

## 题面（可直接粘贴）

渲染端接入透视变换后图元漂移：投影矩阵与仿射矩阵混用、w 分量没有做透视除法、w<=0 的点仍被投影、连续 100 次组合后逆变换误差超过 1e-6、分解把透视项当仿射、非均匀缩放下法线方向错误。affinekit/core.py 是核心，tests/test_core.py 15 个红。要修的是：apply 做透视除法且 w<=0 抛 ValueError；inverse 对投影矩阵成立且 100 次组合后误差 ≤1e-9；decompose 只接受仿射矩阵，遇到透视项抛 ValueError；行列式接近 0 抛 ValueError；法线按逆转置变换；深度上限抛 ValueError。

## 运行方式

```bash
python -m pytest tests -q
```

初始结果应为 `15 failed`（全部因 `NotImplementedError` 失败，无 collection error）。

## 字段

- 所属领域：游戏、图形与多媒体
- 子方向：图形渲染
- 任务类型：Bugfix
- 语言/框架：Python 3, pytest
- 环境可复现等级：无外部依赖
