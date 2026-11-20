# GSB Bugfix Task
## 题面
两个玩家交易时，服务端先扣 A 的物品再给 B，进程在中途崩溃后会出现物品复制或直接丢失；同一个幂等键重复确认会二次发货；confirm 和 cancel 并发时一边成功一边还在回滚；超时未确认的托管没有释放；离线玩家重连后看不到待处理交易；WAL 重放顺序错了，恢复后的余额和交易状态对不上。trade_escrow.py 里的 TradeEscrow 需要实现 offer、confirm、cancel、recover 和 state，仓库自带用例目前全部失败。必须保证跨玩家原子性、幂等键、崩溃恢复、并发只有一个提交、超时释放、重连恢复、WAL 重放顺序正确；非法输入统一抛 ValueError。

## 运行方式
```bash
python -m pytest tests -q
```

## 平台字段

所属领域：游戏、图形与多媒体
子方向：游戏开发
任务类型：Bugfix
语言 / 框架：Python 3, pytest
环境可复现等级：有外部依赖，未容器化
