# GSB Bugfix Task
## 题面
数据分析后台允许运营选择表和列，拼接 SQL 时没有限制标识符：表名里出现空格、分号、注释符仍会发到数据库，保留字不拦，名字超过数据库上限也不报错，schema.table 只校验前一半。sql_ident.py 的 SqlIdentifier 负责 quote 和 qualified。实现只接受字母、数字和下划线，首字符不能是数字，保留字大小写都不允许，内部双引号按 SQL 规则转义，schema 和 table 分别校验，非法名称和超长名称抛 ValueError。 同一个查询构造器会服务多个数据库方言，标识符校验不能依赖某个方言的引号规则；校验通过的名称在拼接后仍要保持原样大小写。

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
