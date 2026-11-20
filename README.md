# GSB Bugfix Task
## 题面
后台一加 CSRF 防护就误伤：Origin 只比对结尾，攻击域 evil-example.com 能通过；token 和会话没绑定，换个 session 也能用；token 没有过期时间，旧页面一直有效；GET 请求被强制要求 CSRF，正常导航反而挂掉。csrf_origin.py 的 CsrfGuard 要实现 issue 和 verify。要按白名单精确匹配 Origin、token 绑定 session 并带过期、签名常量时间比较、GET/HEAD/OPTIONS 放行；空 Origin、过期 token 和未知 session 要拒绝。

## 运行方式
```bash
python -m pytest tests -q
```

## 平台字段

所属领域：安全
子方向：Web 安全
任务类型：Bugfix
语言 / 框架：Python 3, pytest
环境可复现等级：有外部依赖，未容器化
