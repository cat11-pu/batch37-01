# GSB Bugfix Task
## 题面
登录和短信接口接入限流后，安全测试用边界流量绕过了：窗口刚过一秒整批重置，突发流量能翻倍打进来；不同 key 共用同一份计数；cost 大于上限时还返回允许；时间回拨后窗口算错；负数 cost 反而把额度变大。rate_window.py 的 SlidingWindowLimiter 负责 allow 和 remaining。实现要按 key 保存窗口内事件，精确滑出过期记录，支持每次请求不同 cost，cost 超限直接拒绝，不同 key 隔离，时间不能回拨；limit、window 和 cost 都要校验。 限流器会被多个网关实例共享，计数键要包含租户和接口维度；窗口内的事件不能因为进程重启全部丢失，剩余额度要能跨请求稳定读取。

## 运行方式
```bash
python -m pytest tests -q
```

## 平台字段

所属领域：安全
子方向：系统安全
任务类型：Bugfix
语言 / 框架：Python 3, pytest
环境可复现等级：有外部依赖，未容器化
