# GSB Bugfix Task
## 题面
存档版本一升，老玩家的角色数据就开始丢字段：改名迁移把旧键删了却没写新键，链式迁移只跑了第一段，版本号停在中间值，未知字段被整份覆盖，批量操作做到一半失败留下半升级存档。save_migration.py 的 SaveMigrator 要处理 migrate，迁移要按 from/to 串成链、版本号自动推进、rename/add/remove/set 操作原子、未知字段保留、输入不被修改；重复 from、环和非法操作都要明确报错。

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
