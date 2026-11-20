# GSB Bugfix Task
## 题面
安全响应头一多，网关合并就开始互相覆盖：CSP 里 script-src 被后配置的 default-src 顶掉，多个中间件各写一份策略；HSTS 的 max-age 被写成字符串，浏览器忽略；COOP 和 COEP 同时出现时取了更宽松的值；重复头只保留最后一个；CRLF 能注入新头；report-only 和强制策略混在同一个响应里。header_merge_policy.py 的 HeaderMergePolicy 负责 set_header、merge_csp 和 render。实现要按头名大小写不敏感合并、CSP 指令取并集且去重、HSTS max-age 校验为整数、COOP/COEP 冲突时取更严格值、重复头稳定合并、拒绝 CRLF 和非法头名，输出排序后的多行头。

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
