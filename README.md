# GSB Bugfix Task
## 题面
网关换密钥之后，旧 token 还能混进来：kid 不在 keyring 里也放行，alg 写成 none 直接跳过验签，过期时间和生效时间只看一个，audience 不匹配也认，签名比较还能被时序侧信道摸出来。jwt_keyring.py 的 JwtKeyring 要实现 add_key、remove_key 和 verify。要按 kid 选密钥、只允许 HS256、常量时间比较签名、校验 exp/nbf/iat 和 audience、拒绝缺失字段和畸形 token；重复 kid 和未知 kid 要报错。

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
