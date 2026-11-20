# GSB Bugfix Task
## 题面
登录成功后的回跳参数变成了任意跳转：攻击者塞 //evil、反斜杠、%2f%2f 编码、账号密码前缀、javascript: 或 data:，还能用 CRLF 往响应头里塞东西。redirect_guard.py 的 RedirectGuard 负责 resolve。只放行以单个斜杠开头的站内路径，以及配置里列出的完整站点；双斜杠、反斜杠、控制字符、凭据前缀、脚本或数据伪协议一律拒绝；先解码再判断，非法目标抛 ValueError。

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
