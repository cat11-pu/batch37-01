# GSB Bugfix Task
## 题面
报表查询构造器开放给运营后，审计发现只做标识符白名单不够：列名合法但不在当前表里，照样拼进查询；排序字段没有限制，能按未授权列排序；租户条件可以被 filters 里的 OR 分支绕过；limit 传 0 或负数会跳过上限；重复列让结果集膨胀。query_plan_guard.py 的 QueryPlanGuard 负责 build。实现要校验表和列都在白名单、过滤操作符在白名单、租户条件强制保留、排序字段和数量受限、limit 在 1 到 1000 之间、列去重；未知表、未知列、非法操作符和非法 limit 抛 ValueError。

## 运行方式
```bash
python -m pytest tests -q
```

## 平台字段

所属领域：安全
子方向：漏洞检测与攻防
任务类型：Bugfix
语言 / 框架：Python 3, pytest
环境可复现等级：有外部依赖，未容器化
