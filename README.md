# GSB Bugfix Task
## 题面
电竞赛事页上线淘汰赛报名后，签表一换人就乱：报名名单里出现重名还能生成对阵，八强只报了三个名字也照样开打，轮空位被当成正常对局要求提交比分，头号种子和末位种子被排在同一侧，下一轮的对阵和上一轮胜负对不上，决赛打完冠军字段还是空的。tournament_bracket.py 的 TournamentBracket 需要实现 seed、report、current_round、champion 和 state。实现要求：签表大小必须是 2 的幂且至少为 2，报名人数必须超过签位一半且名字不能重复；首轮按头号种子对末位种子依次配对，缺人的位置记为轮空并直接晋级；report 只能作用于当前轮尚未结束的真实对局，胜者必须参加该局；某一轮全部对局结束后自动推进，冠军产生后 current_round 返回 None。

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
