# GSB Bugfix Task
## 题面
角色堆叠和箱子互推时，物理求解器开始抖：两个等质量箱子对撞后速度没有交换，弹性系数设了也没生效；静态地板被撞得往后跑；穿透修正只移动一个物体，堆叠越修越深；摩擦力把切向速度削到负数；同一帧多个接触按插入顺序结算，结果和排列顺序有关；质量为零和未知 body 也不报错。constraint_solver.py 的 ConstraintSolver 负责 add_body、add_contact、step 和 state。实现要用顺序冲量按法线消去接近速度、按恢复系数反弹、按逆质量分配冲量和穿透修正、静态体逆质量为零、摩擦冲量受法向冲量限制、多个接触按稳定顺序迭代；非法质量、未知 body 和非法接触抛 ValueError。

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
