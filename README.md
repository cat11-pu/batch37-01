# GSB Bugfix Task
## 题面
配置中心允许业务上传 JSON 补丁做热更新后，合并逻辑开始被原型污染和深度炸弹打穿：补丁里出现 __proto__、constructor、prototype 键时，合并会把危险属性写进共享对象；同一份 JSON 里重复键后写的覆盖先写的，校验读到的和实际生效的不是一个值；嵌套 200 层的对象让递归爆栈；键数量不限制，一次补丁能塞几十万个键；数组和对象类型不一致时静默替换。json_merge_guard.py 的 JsonMergeGuard 负责 merge。实现要解析时检测重复键、拒绝危险键、限制嵌套深度和总键数、对象与对象递归合并、其他类型由补丁替换、非法 JSON 和非法参数抛 ValueError。

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
