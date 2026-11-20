# GSB Bugfix Task
## 题面
用户密码库升级后开始出问题：同一个密码每次哈希结果一样，盐写死；校验用普通等号比较，时序能摸出前缀；pepper 没参与派生，换了 pepper 旧密码还能过；迭代次数写死，老记录永远不升级；损坏的哈希串直接抛异常而不是拒绝。password_store.py 的 PasswordStore 要实现 hash、verify 和 needs_upgrade。要用随机盐和 PBKDF2、常量时间比较、支持 pepper、短密码和非法输入拒绝、老迭代次数的记录标记升级、损坏格式返回失败。

## 运行方式
```bash
python -m pytest tests -q
```

## 平台字段

所属领域：安全
子方向：密码学
任务类型：Bugfix
语言 / 框架：Python 3, pytest
环境可复现等级：有外部依赖，未容器化
