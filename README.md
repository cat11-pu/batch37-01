# GSB Bugfix Task
## 题面
排位匹配总是先塞满一队再找另一队，结果两边平均分差出两三百分；双排会被拆到对面，等得最久的人反而一直排不到；同一名玩家重复入队也不拦。matchmaker_rating.py 的 Matchmaker 要处理 enqueue、pop 和 state。匹配要保证两队人数正好、同队成员不被拆开、分差超过当前等待窗口就不成局、等待越久窗口越宽、先来先匹配、同时间按 id 稳定排序；重复玩家和超大队列要报错。

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
