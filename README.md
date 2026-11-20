# GSB Bugfix Task
## 题面
烟尘和毒雾在 9x9 的小格子里扩散，策划要看到烟从火把位置被风吹走、浓度慢慢变淡；现在采样位置算错，烟团每帧瞬移半格还出现负浓度，边界格子的速度被读成墙外坐标，扩散系数调大后总量直接少了一半，模拟几帧后全是 NaN。fluid_grid.py 的 FluidGrid(width, height, diffusion, viscosity, iterations) 提供 add_density、add_velocity、density_at、velocity_at 和 step：浓度与速度都存在格点上，添加时累加并对浓度做非负截断；step 按 dt 先做隐式扩散，再做半拉格朗日平流，采样点超出网格时夹到边界并用双线性插值；速度场也按同样方式自平流；density_at 返回浮点浓度，velocity_at 返回 (vx, vy) 二元组；扩散系数、粘度不能为负，迭代次数至少为 1，dt 必须为正，违规参数按 ValueError 处理。要求吹风后烟团中心沿风向移动、浓度扩散后相邻格子抬升且总量基本保持、粘度让尖峰速度变缓，任何时刻不产生 NaN 或负浓度。

## 运行方式
```bash
python -m pytest tests -q
```

## 平台字段

所属领域：安全
子方向：游戏开发
任务类型：Bugfix
语言 / 框架：Python 3, pytest
环境可复现等级：有外部依赖，未容器化
