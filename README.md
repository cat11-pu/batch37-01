# GSB Bugfix Task
## 题面
会话管理一上多端就乱：登录后 session id 不换，攻击者预置的 id 直接变成登录态；空闲超时和绝对过期只算一个；touch 活动请求能把绝对过期一起续掉；注销只删本地缓存，服务端还能验过；旧 session 轮换后原 id 仍然有效。session_lifecycle.py 的 SessionStore 要实现 create、validate、touch、revoke 和 rotate。要同时校验空闲和绝对过期、touch 只续空闲、rotate 立即作废旧 id、注销后不可再用；未知 id 和非法时间抛 ValueError。

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
