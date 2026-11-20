# GSB Bugfix Task
## 题面
联机战斗回放一对比就发现客户端和服务器从某一帧开始分叉，但日志里只看到最终状态不一致：早帧的浮点误差被误报、真正的实体增删被漏掉、同一 tick 重复帧、tick 跳号、NaN 和数字混在一起、修正顺序每次不同。desync_bisect.py 要实现 DesyncBisect 的 first_divergence、diff、reconcile、divergences，现有测试跑起来没有一条能过。验收要覆盖按 tick 对齐、浮点容差、NaN 规则、增删改分类、确定性修正顺序，非法帧序列抛 ValueError。

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
