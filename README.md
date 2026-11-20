# GSB Bugfix Task
## 题面
支付回调接入签名后，伪造和重放都出现了：摘要只覆盖请求体，时间戳没算进去；旧回调过十分钟还能用；比较用普通字符串相等；同一个摘要重复投递被处理两次；hex 大小写和长度也没归一。webhook_hmac.py 的 WebhookVerifier 要实现 sign 和 verify。摘要要覆盖时间戳和原始请求体，用 HMAC-SHA256，比较必须常量时间，时间窗口限制，重复摘要拒绝，hex 格式和参数类型先校验；密钥、时间戳和摘要非法抛 ValueError。

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
