# GSB Bugfix Task
## 题面
狙击怪对移动目标总是打空：准星直接压在目标当前坐标上，子弹飞过去人已经走开；加了重力以后落点又低一截；把空气阻力调大，飞行时间还按直线距离除速度算。projectile_ballistics.py 里的 Ballistics 要按重力、阻力系数构造，solve(shooter, target_pos, target_vel, speed) 用不动点迭代求提前量，返回 aim、flight_time、iterations、converged：先用当前瞄准点算飞行时间，再按目标速度外推、按半个重力乘时间平方抬高落点，反复到时间收敛。flight_time(distance, speed) 在无阻力时是距离除以速度，有阻力时按速度衰减模型算，阻力乘距离超过速度就说明打不到，抛 ValueError。速度不大于零、重力为负、阻力为负、最大迭代次数小于一都要拒绝。目标静止且无重力时瞄准点应等于目标本身，横向移动的目标要往侧面提前。

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
