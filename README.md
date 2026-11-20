# GSB Bugfix Task
## 题面
延迟补偿模块上线后，玩家投诉命中回放和显示的血量对不上：ping 序号重复采样也收下，RTT 填 0 或负数照样进统计，采样时间倒流没有报错，平滑值每次都被最新一次完全覆盖，抖动被算成了最大值，补偿值一路涨到几千毫秒，输入缓冲里同一个 tick 重复写入，回放时顺序乱掉还把范围外的输入也带出来。ping_compensation.py 的 NetcodeBuffer 需要实现 record、smoothed_rtt、jitter、compensation_ms、push_input、replay 和 state。实现按 alpha 等于 0.25 做指数平滑，抖动取相邻 RTT 差值的平均值，补偿值等于平滑值加两倍抖动并封顶 250 毫秒；采样只保留最近 max_samples 条，序号必须递增且采样时间不能回退；输入 tick 必须为正整数、动作非空、重复 tick 拒绝，replay 按 tick 升序返回闭区间内的输入。

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
