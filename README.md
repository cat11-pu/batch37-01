# GSB Bugfix Task
## 题面
后台加 CSRF 防护后，安全测试用几个变体就绕过了：Origin 只比对结尾，evil-app.example 能通过；token 没有和 session 绑定，换一个会话也能复用；token 没有过期时间，旧页面一直有效；GET/HEAD/OPTIONS 被强制要求 token，正常导航反而失败。csrf_origin.py 的 CsrfGuard 负责 issue 和 verify。实现要按白名单精确匹配 Origin，token 绑定 session 并带过期，签名比较固定耗时，安全方法直接放行；空 Origin、过期 token、未知 session 和篡改 token 都要拒绝。 页面会同时开多个标签页，每个标签页拿到的令牌要能独立失效；用户退出登录后，旧标签页的令牌不能再通过校验。

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
