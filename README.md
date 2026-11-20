# GSB Bugfix Task
## 题面
渲染管线一改就出黑屏：后处理在颜色缓冲还没写完时就开始读，阴影通道和主通道互相等对方，显式 after 写错顺序，两个独立通道每次编译顺序还不一样。render_graph.py 的 RenderGraph 要实现 compile。要按资源读写关系自动补依赖、处理写后读/读后写/写后写、合并显式 after、检测环和未知依赖、同层按 id 稳定排序，返回可执行的通道顺序。

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
