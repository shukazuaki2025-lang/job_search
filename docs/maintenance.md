# 维护说明

## 哪些页面是当前入口

- 根目录README只保留行动判断和导航。
- `nearby_internships/README.md`保留当前周边候选与时间安排。
- 带日期报告保留当轮证据；下轮追加新报告并更新当前入口，不覆盖历史判断。
- `nearby_internships/roles.json`保留岗位级字段；招聘源未写的值用null或“未披露”，不从同页其他岗位补齐。
- 南京扩展备选、历史周报、邮件归档分别浏览。邮件分类中的“周边”是检索标签，不证明满足当前10公里路线。

## 当前计划与字段

用户计划为**2027年寒假开始，持续到2027年暑假**。具体起止日、寒暑假每周出勤和春季固定工作日待定，不默认固定6/8个月。

- `scope.internship_start_window`、`scope.internship_end_window`记录窗口；精确日期未知时保留null。
- `planned_window_fit`评估整个计划；旧字段`winter_fit`只评估单独寒假。
- `updated_on`记录整理日期。`verified_on`与`verification_scope`说明最近公开证据复核的日期和范围；各岗位保留自身证据日期。
- `last_source_check`记录本次读到的列表/详情及访问限制；未重读的地址等字段保留旧依据。
- `planned_window_confirmed`只有取得企业对本人的起止时间及出勤安排的确认后才改为true。
- 仅更新个人计划时，不刷新未重读岗位的证据日期；带日期历史档案保留原文。

## 岗位更新规则

每条至少记录：公司、岗位、岗位直链、证据读取日、岗位发布日期/刷新日期、截止日期、当前招聘状态、学历、毕业年、专业、每周天数、连续月数、技能硬要求、加分项、待遇单位、实际工作地址与证据、通勤核验状态、寒假和下学期适配、下一步、是否投递。

“页面可申请”“HR仍招”“接收2028届”“可到岗”“距离达标”分别核验。搜索抓取时间不等于招聘更新时间；企业联系地址或工商注册地不等于岗位坐班地；未过页面截止也不保证仍有名额。截止过后将状态改为“页面已过截止，需重新核实”。

更新前读原页；读不到就保留缺口。不要为凑岗位数加入正式校招、要求硕士的岗位或明显超出距离的岗位。没有合格记录时允许写0条。

## 邮件索引重建与导入

以下为仓库原有维护入口，本轮仅整理文档，未运行邮箱同步或改动邮件归档。使用UTF-8。

```powershell
python scripts/sync_emails.py
# PowerShell入口调用同一Python实现
./scripts/sync_emails.ps1 -Python python
```

Python不在PATH时换成实际安装路径。导入明确提供的邮件JSON：

```powershell
python scripts/sync_emails.py --import-json path/to/emails.json
```

脚本支持已有JSON重建与指定JSON导入；不能据此认为已建立持续Gmail/IMAP同步。只有添加`--push`或`-Push`才执行提交推送。相关代码检查可运行：

```powershell
python -m unittest discover -s tests -v
```

本轮未修改这些脚本，不把历史运行结果当作本轮邮箱同步成功。
