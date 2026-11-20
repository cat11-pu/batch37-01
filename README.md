# GSB Bugfix Task
## 题面
出站代理接入多租户后，安全团队发现只按域名黑名单拦不住：租户 A 的规则放行了整个 *.example.com，租户 B 的同名子域也被一起放行；规则里端口和路径写成可选，匹配时被当成任意值；deny 规则排在 allow 后面永远不生效；大小写和末尾点没有归一，绕过规则。egress_policy.py 的 EgressPolicy 负责 check。实现要按 host、port、scheme、path、method 逐项匹配，规则按顺序 first-match，默认拒绝，wildcard 只匹配子域不匹配裸域，host 统一小写并去掉末尾点，非法规则和请求抛 ValueError。

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
