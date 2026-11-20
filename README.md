# GSB Bugfix Task
## 题面
运营配置了带分叉的任务线，测试时发现两条分支都能接下来，走完一条另一条还挂着；重复点完成按钮时金币会发两次，先接后交的顺序也被绕过。quest_chain.py 中的 QuestChain 用一张任务表描述节点：requires 是进入前必须已获得的标志，grants 是完成时写入的标志，coins 表示奖励金币数，branches 把选项名映射到不同后续任务。玩家注册之后，available 给出当前可接任务，accept 只接收可接任务；complete 要求任务处于进行中，跑完写入标志、结算金币并返回刚刚开放的后续清单；choose 在分叉点定下选项，另一条分支立即永久关闭，再对它调用 accept 必须拒绝。任务不得重复完成，status 返回 locked、available、active、completed、locked_out 之一，快照方法给出可安全修改的副本，未知任务与未知选项一律拒绝。

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
