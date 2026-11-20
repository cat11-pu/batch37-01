# GSB Bugfix Task
## 题面
分服之后运维每次扩缩容都要手工搬分片，搬完不是某个节点超载，就是把绑定了阵营的分片挪走；计划里同一分片被搬两次，容量算错，搬移预算超了也照搬；执行到一半失败留下半套拓扑。shard_rebalancer.py 的 ShardRebalancer 要实现 plan、apply 和 state。计划要按节点负载和容量算出确定性的搬移序列、尊重分片亲和、受搬移预算限制、不改动当前状态；执行要原子生效，非法计划整单拒绝。

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
