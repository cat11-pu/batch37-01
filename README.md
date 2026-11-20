# GSB Bugfix Task
## 题面
跨域配置一放宽，带 cookie 的接口就开始被任意站读：Origin 只做后缀匹配，evil-app.example 能过；允许携带凭据还返回 *；预检把请求方要的 header 全反射回去；没有 Vary: Origin，缓存把 A 站的响应发给 B 站；null Origin 也放行。cors_policy.py 的 CorsPolicy 要实现 headers。要精确匹配 Origin、带凭据时禁止通配、预检只回允许的方法和 header、响应带 Vary: Origin、拒绝 null 和非法 Origin；配置非法抛 ValueError。

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
