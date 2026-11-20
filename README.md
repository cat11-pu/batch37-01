# GSB Bugfix Task
## 题面
比赛观战功能上线后，权限和延迟一起出问题：未开赛的房间也能加入，观众重复点击加入会占两个位置，普通观众拿到的是实时画面，裁判反而被延迟拦住，观众席满了连裁判都进不来，离开房间后延迟接口还能查到数据，管理员踢人接口谁调用都成功。match_spectator.py 的 SpectatorHub 需要实现 open_match、join、leave、visible_time、kick 和 state。实现要求：房间 id 唯一且开赛时间不能为负；角色只能取 viewer、referee、admin，重复加入和被封禁的账号直接拒绝；只有 viewer 占用观众名额，裁判和管理员不占；viewer 看到的是当前时间减去 delay 且不小于 0，裁判和管理员看实时；未加入的账号查询延迟要报错；kick 必须由已加入的管理员发起，不能踢自己。

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
