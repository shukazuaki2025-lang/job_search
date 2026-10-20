# 🤖 NUIST Automation Weekly Internship & Job Email Tracker (`job_search`)

面向 **南京信息工程大学（NUIST）自动化专业（Automation）** 的每周高匹配实习追踪与求职邮件三维归档仓库。

---

## 📌 一、 核心筛选策略与定制偏好

| 维度 | 设定规则 |
| :--- | :--- |
| **目标地区（每周 1+1 双轨制）** | 1. **江浙沪核心产业带（每周 1 席）**：江苏、上海、浙江高匹配名企自动化岗位<br>2. **南信大周边通勤圈（每周 1 席）**：南京江北新区 / 浦口高新开发区（距南信大地铁 1~3 站或 20 分钟车程内）可日常实习岗位 |
| **优先技术方向（多选全覆盖）** | - ⚙️ **工业自动化 / PLC / 控制**（PLCopen、DCS/SCADA、运动控制卡、工业总线 EtherCAT/CANopen）<br>- ⚡ **电力电子 / 电机控制**（PMSM/BLDC、FOC、SVPWM、逆变器与新能源电驱控制）<br>- 🦾 **机器人 / ROS / 运动控制**（正逆运动学、轨迹规划、力控、振动抑制、ROS2/具身智能）<br>- 🚗 **自动驾驶 / 车辆控制**（规划控制 PNC、横纵向控制 MPC/LQR、底盘线控与列车控制） |
| **实习类型偏好** | **寒假 / 暑期实习优先**，重点筛选具备明确 **转正 / 留用（Return Offer）** 机制的岗位 |
| **招聘来源要求** | **公司官方招聘官网 / 校招门户优先**，辅以主流直聘平台验证，严格剔除已过期批次与中介僵尸岗 |
| **求职邮件归档策略** | 自动按 **【方向 × 类别 × 工作地点】** 三维分类归档，并对手机号、身份证号、私密测评链接 Token 与验证码执行 **自动脱敏** |

---

## 📅 二、 每周精选实习岗位追踪（Weekly Internships）

👉 **总目录入口**：[`weekly_internships/INDEX.md`](./weekly_internships/INDEX.md)

### 最新一期：`2026-W43`（2026-10-20）
- 📄 **本期完整周报**：[`weekly_internships/2026-W43_2026-10-20.md`](./weekly_internships/2026-W43_2026-10-20.md)
  1. 🎯 **江浙沪高匹配名企岗**：**苏州汇川技术有限公司 / 汇川联合动力 (Inovance)** — **运动控制 / 电机控制算法实习生**（江苏·苏州，含 27 届/在校生转正留用通道，同时覆盖工业自动化/电机控制/机器人运动控制三大方向）
  2. 🏫 **南信大周边通勤实习岗**：**国电南京自动化股份有限公司（国电南自，600268）** — **工业控制 / 嵌入式软硬件研发实习生**（南京·江北新区星火路 8 号，**距南信大地铁 S8 号线仅 1 站 / 4.5km**，央企华电直属）

---

## 📬 三、 求职邮件三维分类归档中心（Emails）

👉 **邮件总控台入口**：[`emails/INDEX.md`](./emails/INDEX.md)

所有工作/实习相关邮件自动按以下三个维度生成分类视图：
1. **按【方向 (Direction)】**：
   - [工业自动化 / PLC / 控制](./emails/by_direction/工业自动化_PLC_控制.md)
   - [电力电子 / 电机控制](./emails/by_direction/电力电子_电机控制.md)
   - [机器人 / ROS / 运动控制](./emails/by_direction/机器人_ROS_运动控制.md)
   - [自动驾驶 / 车辆控制](./emails/by_direction/自动驾驶_车辆控制.md)
   - [通用自动化 / 嵌入式及其他](./emails/by_direction/通用自动化_嵌入式及其他.md)
2. **按【类别 (Category)】**：
   - [投递与网申确认](./emails/by_category/投递与网申确认.md)
   - [笔试与在线测评](./emails/by_category/笔试与在线测评.md)
   - [面试邀约与通知](./emails/by_category/面试邀约与通知.md)
   - [录用与Offer沟通](./emails/by_category/Offer与录用沟通.md)
   - [职位推荐与状态更新](./emails/by_category/职位推荐与状态更新.md)
3. **按【工作地点 (Location)】**：
   - [江苏·南京（含南信大周边）](./emails/by_location/江苏_南京_含南信大周边.md)
   - [江苏·苏锡常及其他](./emails/by_location/江苏_苏州_无锡_常州等.md)
   - [上海](./emails/by_location/上海.md)
   - [浙江（杭州/宁波等）](./emails/by_location/浙江_杭州_宁波等.md)
   - [其他或待确认地点](./emails/by_location/其他或待确认地点.md)

---

## ⚙️ 四、 邮箱接入与自动同步使用指南（Gmail / Outlook）

本仓库内置零依赖 Python 同步与脱敏脚本 [`scripts/sync_emails.py`](./scripts/sync_emails.py)，支持两种方式导入整理邮件：

### 方式 A：通过 Gmail / Outlook IMAP 自动拉取（推荐）
1. 将仓库根目录下的 [`.env.example`](./.env.example) 复制为 `.env`（`.env` 已加入 `.gitignore`，凭据仅保存在本地，绝不会上传到 GitHub）：
   ```ini
   EMAIL_PROVIDER=outlook          # 可选 gmail | outlook | qq | 163 | custom
   EMAIL_ADDRESS=你的邮箱地址
   EMAIL_APP_PASSWORD=你的应用专用密码
   SEARCH_DAYS=180
   ```
2. 运行同步并推送至 GitHub：
   ```bash
   python scripts/sync_emails.py --push
   ```

### 方式 B：本地邮件文件（`.eml`）离线导入
如果你使用 Windows 新版 Outlook / 网页端导出单封或多封求职邮件（`.eml` 格式），只需将其放入 `emails/raw_drop/` 文件夹（原始文件同样被 `.gitignore` 忽略保护），然后运行：
```bash
python scripts/sync_emails.py --push
```
脚本会自动提取正文、完成隐私脱敏、按【方向/类别/工作地点】三维归类并更新到 GitHub。
