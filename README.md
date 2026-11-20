# GSB Bugfix Task
## 题面
API key 权限一扩就收不住：read:* 匹配不到 read:users，write:user 反而能匹配 write:users；过期 key 还能用；注销只改本地缓存，服务端照样放行；重复 key id 直接覆盖旧 scope。api_key_scope.py 的 ApiKeyStore 要实现 issue、authorize 和 revoke。要支持精确 scope 和通配匹配、过期和注销立即失效、重复 id 和非法 scope 报错、未知 key 拒绝；authorize 只返回布尔值，不能改状态。

## 运行方式
```bash
python -m pytest tests -q
```

## 平台字段

所属领域：安全
子方向：身份认证
任务类型：Bugfix
语言 / 框架：Python 3, pytest
环境可复现等级：有外部依赖，未容器化
