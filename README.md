# GSB Bugfix Task
## 题面
大世界同屏人数一多，AOI 每帧该发谁、该延谁全乱：格子边界漏人、优先级和距离排序不稳定、预算超发、丢包后不重发、已确认的还在 pending、实体移出视野还占队列、重复 id 和非法坐标不报错。aoi_scheduler.py 的 AoiScheduler 要补齐 add_entity、update_observer、plan、ack、pending，仓库里的用例当前全部失败。需要满足视野半径、优先级/距离/id 稳定排序、每观察者预算、丢包重发、ack 清理、越界清理，非法输入抛 ValueError。

## 运行方式
```bash
python -m pytest tests -q
```

## 平台字段

所属领域：安全
子方向：游戏开发
任务类型：Bugfix
语言 / 框架：Python 3, pytest
环境可复现等级：有外部依赖，未容器化
