# GSB Bugfix Task
## 题面
用户密码库升级时，安全评审发现同一个密码每次哈希结果一样，盐写死；校验用普通等号比较，时序能摸出前缀；pepper 没参与派生，换了 pepper 旧密码还能过；迭代次数写死，老记录永远不升级；损坏的哈希串直接抛异常而不是拒绝。password_store.py 的 PasswordStore 负责 hash、verify 和 needs_upgrade。实现要用随机盐和 PBKDF2，固定耗时比较，支持 pepper，短密码和非法输入拒绝，老迭代次数记录标记升级，损坏格式返回失败。 同一账户可能在不同时间用不同迭代次数写入，校验时要按记录里的参数重算，不能统一用当前配置；升级要在验证成功后原子替换。

## 运行方式
```bash
python -m pytest tests -q
```

## 平台字段

所属领域：安全
子方向：其他
任务类型：Bugfix
语言 / 框架：Python 3, pytest
环境可复现等级：有外部依赖，未容器化
