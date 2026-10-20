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
| **求职邮件归档策略** | 已绑定 `shukazuaki2025@gmail.com`，自动按 **【方向 × 类别 × 工作地点】** 三维分类归档（共 **65 封**），并对手机号、身份证号、私密测评链接 Token 与验证码执行 **自动脱敏** |

---

## 📅 二、 每周精选实习岗位追踪（Weekly Internships）

👉 **总目录入口**：[`weekly_internships/INDEX.md`](./weekly_internships/INDEX.md)

### 最新一期：`2026-W43`（2026-10-20）
- 📄 **本期完整周报**：[`weekly_internships/2026-W43_2026-10-20.md`](./weekly_internships/2026-W43_2026-10-20.md)
  1. 🎯 **江浙沪高匹配名企岗**：**苏州汇川技术有限公司 / 汇川联合动力 (Inovance)** — **运动控制 / 电机控制算法实习生**（江苏·苏州，含转正留用通道，同时覆盖工业自动化/电机控制/机器人运动控制三大方向）
  2. 🏫 **南信大周边通勤实习岗**：**国电南京自动化股份有限公司（国电南自，600268）** — **工业控制 / 嵌入式软硬件研发实习生**（南京·江北新区星火路 8 号，**距南信大地铁 S8 号线仅 1 站 / 4.5km**，央企华电直属）

---

## 📬 三、 求职邮件三维分类归档中心（已同步 Gmail 共 65 封）

👉 **邮件总控台入口**：[`emails/INDEX.md`](./emails/INDEX.md)

所有从 `shukazuaki2025@gmail.com` 提取的工作、实习、宣讲与课题组实训相关邮件已自动脱敏并按以下三个维度生成分类视图：

1. **按【技术方向 (Direction)】**：
   - [工业自动化 / PLC / 控制](./emails/by_direction/工业自动化_PLC_控制.md)
   - [电力电子 / 电机控制](./emails/by_direction/电力电子_电机控制.md)
   - [机器人 / ROS / 运动控制](./emails/by_direction/机器人_ROS_运动控制.md)
   - [自动驾驶 / 车辆控制](./emails/by_direction/自动驾驶_车辆控制.md)
   - [通用自动化 / 嵌入式及高新制造](./emails/by_direction/通用自动化_嵌入式及其他.md)
2. **按【邮件类别 (Category)】**：
   - [岗位每日精讲（名企岗位深度拆解，21 封）](./emails/by_category/岗位每日精讲.md)
   - [长三角高新企业晨报（实习与宣讲追踪，26 封）](./emails/by_category/长三角高新企业晨报.md)
   - [企业网申与投递确认（Rockwell / xAI 等，6 封）](./emails/by_category/投递与网申确认.md)
   - [南信大课题组科研与实训联系（12 封）](./emails/by_category/南信大课题组科研实训.md)
   - [笔试测评 / 面试邀约 / Offer沟通](./emails/by_category/面试与测评Offer沟通.md)
3. **按【工作地点 (Location)】**：
   - [江苏·南京（含南信大及周边）](./emails/by_location/江苏_南京_含南信大周边.md)
   - [江苏·苏锡常及其他（苏州/无锡/常州/昆山等）](./emails/by_location/江苏_苏州_无锡_常州等.md)
   - [上海](./emails/by_location/上海.md)
   - [浙江（杭州/宁波等）](./emails/by_location/浙江_杭州_宁波等.md)
   - [长三角多城综合 / 国际及其他](./emails/by_location/其他或待确认地点.md)

---

## ⚙️ 四、 自动同步脚本说明

仓库内置 Python 同步与脱敏脚本 [`scripts/sync_emails.py`](./scripts/sync_emails.py)，支持从浏览器提取的 JSON 或 IMAP / `.eml` 增量更新并一键推送到 GitHub：
```bash
py scripts/sync_emails.py --push
```
