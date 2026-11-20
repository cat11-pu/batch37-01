# GSB Bugfix Task
## 题面
程序化地牢每次改一个房间就整张图重算，增量编辑后房间重叠、越界、走廊断开、地板不连通；批量涂格子中途失败留下半张图；回滚版本对不上；快照被外部改坏。dungeon_edit.py 要实现 DungeonEditor 的 generate、paint、apply、rollback、snapshot、version，随仓库附带的测试现在全部挂在初始状态。实现要满足同种子确定、房间不重叠且在界内、所有地板连通、批量编辑原子、版本历史可回滚、快照隔离，非法操作抛 ValueError。

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
