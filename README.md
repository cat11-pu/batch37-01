# GSB Bugfix Task
## 题面
开放世界一进大场景，纹理流送就开始抖：高优先级贴图被低优先级挤掉，显存超了还继续加载，固定住的关键 UI 图也被清走；同一张图重复请求会重复占预算，切换场景后旧请求一直不移除，预算刚好够时又因为排序不稳来回抖。texture_stream.py 的 TextureStreamer 要实现 request、cancel、tick 和 resident，要求按优先级稳定加载、超预算时先淘汰低优先级未固定项、固定项不淘汰、单张超预算延后、重复请求更新参数；零尺寸和非法优先级要报错。

## 运行方式
```bash
python -m pytest tests -q
```

## 平台字段

所属领域：安全
子方向：图形渲染
任务类型：Bugfix
语言 / 框架：Python 3, pytest
环境可复现等级：有外部依赖，未容器化
