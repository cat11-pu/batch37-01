# GSB Bugfix Task
## 题面
公会权限加委托后，管理层开始互相打脸：副会长把审批权委托给团长，团长又能继续转委托，链一长就不知道谁批的；父角色拒绝的权限被子的允许覆盖；委托没有深度上限，A 委托 B、B 委托 C 再回到 A 也不报错；重复委托同一权限时后写的直接覆盖。delegation_policy.py 的 DelegationPolicy 负责 grant、deny、delegate、can 和 state。实现要沿角色继承链收集允许和拒绝，拒绝优先；委托必须由拥有该权限的角色发起，按深度递减，超过上限或形成环就拒绝；重复委托、未知角色和非法深度要报错。

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
