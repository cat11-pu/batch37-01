# GSB Bugfix Task
## 题面
高速投射物贴墙飞的时候会直接穿过去，斜着撞墙角时又经常判定到错误的法线；同一帧里多个目标重叠，返回顺序每次不一样；开局就卡在墙里的单位没有被识别；负尺寸、重复 id、NaN 位移也都能混进来。hitbox_sweep.py 的 SweepWorld 要补齐 add_box、remove_box 和 sweep，要求扫掠 AABB 连续检测、按时间取最早命中、同时间按 id 稳定排序、支持层过滤、重叠时 time 为 0；负尺寸、重复 id 和 NaN 位移要明确报错。

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
