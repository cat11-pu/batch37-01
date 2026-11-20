# GSB Bugfix Task
## 题面
战斗一开，脚步、刀光、UI 提示和 Boss 技能音效在同一帧涌进来，音频线程开始丢事件：同一个技能触发两次会排两遍，低优先级的脚步把高优先级的技能挤出预算，暂停菜单打开后队列还在往前推，恢复时一次性把积压事件全放出来，过期事件也照样播。audio_event_queue.py 的 AudioEventQueue 负责 push、drain、pause、resume 和 state。实现要按事件 id 在时间窗内去重、按优先级和 id 稳定排序、每帧只取预算内的事件、过期事件直接丢弃、暂停时不消费但保留队列，恢复后按原顺序继续；非法 id、优先级和音量要报错。

## 运行方式
```bash
python -m pytest tests -q
```

## 平台字段

所属领域：安全
子方向：音视频处理
任务类型：Bugfix
语言 / 框架：Python 3, pytest
环境可复现等级：有外部依赖，未容器化
