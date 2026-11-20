# GSB Bugfix Task
## 题面
后台把用户输入直接拼进 SQL 标识符，表名和列名一带引号就注入：空格、分号、注释符都能过，保留字不拦，超长名字照发，schema.table 只校验前半段。sql_ident.py 的 SqlIdentifier 要实现 quote 和 qualified。标识符只允许字母、数字和下划线且不能数字开头，保留字大小写都不许用，内部双引号要按 SQL 规则转义，schema 和 table 分别校验，非法名称和超长名称抛 ValueError。

## 运行方式
```bash
python -m pytest tests -q
```

## 平台字段

所属领域：安全
子方向：Web 安全
任务类型：Bugfix
语言 / 框架：Python 3, pytest
环境可复现等级：有外部依赖，未容器化
