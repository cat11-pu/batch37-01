# GSB Bugfix Task
## 题面
关卡节奏一快，刷怪预算就失控：一波里同一个精英被连刷五只，威胁点数早就超了还在继续出，读档重开以后每次刷出来的顺序都不一样，策划没法复现。spawn_director.py 的 SpawnDirector 用种子构造，plan_wave(wave_id, entries, budget, count, duration) 给一波怪排期，entries 每项包含 type、cost、weight 三个字段。实现要维护剩余预算，只在买得起的条目里按 weight 做加权随机，选中的类型扣掉对应 cost，排满 count 只或者预算不够再选时提前结束；每只的出生时刻按 duration 均匀铺开并落在区间内，返回 wave、spawns、spent、remaining、finished 这些字段。同一个种子、同一组参数必须得到完全相同的序列，换种子应当出现不同排列；外部先改 random 的全局状态不能影响结果。预算为负、条目为空、cost 或 weight 不为正、count 或 duration 不为正、种子不是整数都要抛 ValueError。

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
