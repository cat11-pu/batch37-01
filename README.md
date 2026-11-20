# GSB Bugfix Task
## 题面
线上回档事故查下来，存档写坏不是断电就是并发写：直接覆盖原文件，进程一挂就剩半截 JSON；旧版本被新文件盖掉，想回滚没有备份；文件被人改了一个字段，校验和居然还能过；备份一直堆着也不清理。save_integrity.py 提供 SaveStore 和 SaveCorrupted：构造时给根目录和备份数量，save(slot, payload) 先序列化再写临时文件、刷盘后用 os.replace 原子换入，旧文件依次转成编号备份，超过上限的最老备份删掉；每条记录带递增序号、前一条的哈希和自身哈希，形成链，自身哈希由 record_hash(seq, payload, prev) 算出。load 读回时重算哈希、核对与前一份备份的链接，JSON 损坏、哈希不符、链断都抛 SaveCorrupted，槽位不存在抛 FileNotFoundError。history 返回当前及备份的序号列表，当前文件是 slot.json，备份是 slot.bak.N。槽位名只允许字母数字下划线横线，出现路径分隔符或点点抛 ValueError；替换失败时原文件必须完好且不留下临时文件。

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
