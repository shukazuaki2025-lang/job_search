# 南信大自动化求职与实习追踪

面向南京信息工程大学自动化专业 **2028届本科**：2027暑期实习 → 2028校招。优先嵌入式/STM32、电机控制/FOC、电力电子/Buck，PLC、机器人和设备调试可作延伸。

## 优先入口：南信大周边

- **[南信大周边实习专页](./nearby_internships/README.md)**：重点入口，与南京其他区域分开。
- [2026-10-22完整检索与核验](./nearby_internships/2026-10-22.md)：具体岗位、地址证据、学历届别、薪资、截止和排除记录。
- [南京其他区域实习](./nanjing_internships/README.md)：秦淮、栖霞、雨花台及地址待核等单列。
- [周报目录](./weekly_internships/INDEX.md)：历史周报不直接代表当前在招。

**本轮结论**：附近页面仍可申请的设备支持实习1条（丁丁停车，10月24日截止）；泰山片区本科嵌入式实习列表线索1条（铭想芯创）；圭步微电子7类实习方向放在江北扩展区。2028届资格、出勤档期和实际通勤需逐岗确认。未核实到近校FOC研发实习，不能用校招替代。

## 邮件资料库

[邮件总索引](./emails/INDEX.md)保留既有65封邮件的分类入口，本轮未新增同步邮箱。只更新不含正文、主题及联系人信息的索引；原邮件卡片与元数据保留原样，卡片旧地点字段以新分类入口为准。历史邮件是线索，不能替代当日招聘核验。

按地点独立查看：

- [南信大周边企业线索](./emails/by_location/南信大周边_企业实习线索.md)
- [南信大校内科研实训（非企业实习）](./emails/by_location/南信大校内_科研实训.md)
- [江北扩展区（通勤待核）](./emails/by_location/江北扩展区_通勤待核.md)
- [南京其他区域/地址待核](./emails/by_location/江苏_南京_其他区域或地址待核.md)
- [苏锡常及其他江苏地区](./emails/by_location/江苏_苏州_无锡_常州等.md)
- [上海](./emails/by_location/上海.md)
- [浙江](./emails/by_location/浙江_杭州_宁波等.md)
- [多城综合/其他](./emails/by_location/其他或待确认地点.md)

技术方向、邮件类别仍可在总索引浏览。校内导师联系不当作企业岗位；多岗位晨报归综合，避免只因出现“南信大/南京”就混进近校分类。

## 更新与重建

使用UTF-8。重建已有邮件分类：

```powershell
python scripts/sync_emails.py
# 或 PowerShell入口，调用同一Python实现
./scripts/sync_emails.ps1 -Python python
```

如Python不在PATH，把命令中的python换成已安装Python的完整路径。导入明确提供的邮件JSON：

```powershell
python scripts/sync_emails.py --import-json path/to/emails.json
```

脚本当前支持已有JSON重建及指定JSON导入；不据脚本说明推断已建立持续Gmail/IMAP同步。只有加上`--push`或`-Push`才执行提交推送。执行测试：`python -m unittest discover -s tests -v`。

后续每轮保留核验日期与岗位来源，不强行凑每周固定数量。招聘入口存在、接收实习、2028届本科可投、可转正是四个不同结论，分别验证。

