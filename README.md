# GSB Bugfix Task
## 题面
物理场景里一箱箱子只要有一个被撞醒，整堆应该一起醒，现在却只醒了被撞的那一个；反过来，远处另一堆睡着的箱子会莫名其妙一起醒；移除箱子后旧的接触边还留着，岛的大小算错。physics_island.py 的 IslandManager 要实现 add_body、remove_body、wake、step 和 state。要按接触关系维护连通岛、任意一个 body 被唤醒时整岛传播、移动体只唤醒自己所在的岛、移除 body 时同步清理接触边；重复 id、未知 body 和非法接触要报错。

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
