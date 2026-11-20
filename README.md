# GSB Bugfix Task
## 题面
移动端登录接完 PKCE，授权码开始被重复消费：同一串 code 第二次还能换出 access_token，回调地址只比对开头就放行，state 留空也照发，challenge 短得离谱不拦，verifier 和 challenge 根本不是一个东西也通过。oauth_pkce.py 的 PkceFlow 负责 authorize 和 exchange。要求 client 与回调地址精确匹配、state 非空、支持 S256 和 plain 两种模式、code 只能换一次且会过期、verifier 长度与摘要都要对；不认识的 client、非法 challenge、重复兑换直接抛 ValueError。

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
