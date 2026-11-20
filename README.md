# GSB Bugfix Task
## 题面
角色换武器时上下半身分层混合开始抖：override 和 additive 顺序错、权重不归一、循环片段接缝跳变、LOD 切换丢层、root motion 重复累加、IK 一步冲过目标；非法时长、乱序关键帧、重复时间点也不报错。anim_layers.py 要实现 AnimationGraph 的 add_clip、add_layer、sample、evaluate、root_delta、solve_ik，仓库自带测试目前没有一条通过。行为要求覆盖线性采样与循环包裹、override/additive 混合、权重覆盖、LOD 跳层、root 加权、IK 限步，非法输入抛 ValueError。

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
