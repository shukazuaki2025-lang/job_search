#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Job Search Email Sync, Desensitization & 3D Classifier (Direction / Category / Location)
Repository: https://github.com/shukazuaki2025-lang/job_search

Features:
1. Connects to Gmail / Outlook / Custom IMAP server via .env credentials,
   or reads exported .eml files from emails/raw_drop/.
2. Filters job/internship-related emails (自动化/控制/PLC/机器人/电机/自动驾驶/实习/校招/面试/笔试/Offer等).
3. Redacts sensitive personal data (mobile phone numbers, ID numbers, OTP codes, private token URLs).
4. Organizes and generates Markdown indexes by:
   - 方向 (Direction)
   - 类别 (Category)
   - 工作地点 (Location)
5. Optionally commits and pushes updates to GitHub (--push).
"""

import argparse
import datetime as dt
import email
from email.header import decode_header
from email.message import Message
from email.utils import parsedate_to_datetime
import hashlib
import imaplib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
EMAILS_DIR = BASE_DIR / "emails"
RAW_DROP_DIR = EMAILS_DIR / "raw_drop"
ARCHIVE_DIR = EMAILS_DIR / "archive"
DATA_FILE = EMAILS_DIR / "emails_metadata.json"

IMAP_PRESETS = {
    "gmail": ("imap.gmail.com", 993),
    "outlook": ("outlook.office365.com", 993),
    "hotmail": ("outlook.office365.com", 993),
    "qq": ("imap.qq.com", 993),
    "163": ("imap.163.com", 993),
}

JOB_KEYWORDS = [
    "实习", "招聘", "校招", "秋招", "春招", "寒假", "暑期", "内推", "简历", "网申",
    "面试", "笔试", "测评", "北森", "牛客", "赛码", "录用", "offer", "意向书", "入职",
    "投递", "应聘", "岗位", "职位", "候选人", "自动化", "控制", "plc", "机器人", "电机",
    "嵌入式", "自动驾驶", "算法", "电气", "硬件", "软件", "研发", "工程师",
    "intern", "internship", "interview", "assessment", "application", "recruiting",
    "recruitment", "career", "campus", "engineer",
]

DIRECTION_RULES = [
    ("工业自动化 / PLC / 控制", "工业自动化_PLC_控制", [
        "plc", "工业自动化", "工控", "控制柜", "scada", "dcs", "上位机", "梯形图",
        "ethercat", "modbus", "profinet", "canopen", "汇川", "南瑞", "南自", "西门子",
        "中控", "过程控制", "继电保护", "电力自动化",
    ]),
    ("电力电子 / 电机控制", "电力电子_电机控制", [
        "电机", "电力电子", "foc", "svpwm", "pmsm", "bldc", "逆变", "变流",
        "伺服驱动", "电驱", "电控", "bms", "电源", "功率", "dsp", "ti c2000", "联合动力",
    ]),
    ("机器人 / ROS / 运动控制", "机器人_ROS_运动控制", [
        "机器人", "ros", "ros2", "运动控制", "轨迹规划", "运动学", "动力学", "机械臂",
        "具身智能", "slam", "导航", "力控", "伺服", "埃斯顿", "智元", "追觅", "宇树",
    ]),
    ("自动驾驶 / 车辆控制", "自动驾驶_车辆控制", [
        "自动驾驶", "车辆控制", "规控", "规划控制", "横纵向控制", "mpc", "lqr", "adas",
        "智驾", "智能驾驶", "底盘控制", "线控", "车联网", "中车", "蔚来", "理想",
        "地平线", "momenta", "赛力斯",
    ]),
]

CATEGORY_RULES = [
    ("录用与Offer沟通", "Offer与录用沟通", [
        "offer", "录用", "意向书", "签约", "三方协议", "入职通知", "欢迎加入", "薪酬沟通",
    ]),
    ("面试邀约与通知", "面试邀约与通知", [
        "面试", "初试", "复试", "终面", "技术面", "hr面", "主管面", "腾讯会议", "飞书会议",
        "interview", "预约面试",
    ]),
    ("笔试与在线测评", "笔试与在线测评", [
        "笔试", "测评", "在线考试", "机考", "行测", "性格测试", "北森", "牛客", "赛码",
        "assessment", "online test", "coding test",
    ]),
    ("投递与网申确认", "投递与网申确认", [
        "投递成功", "收到您的简历", "网申确认", "申请已收到", "感谢投递", "简历已进入",
        "application received", "thank you for applying",
    ]),
]

LOCATION_RULES = [
    ("江苏·南京（含南信大周边）", "江苏_南京_含南信大周边", [
        "南京", "江北新区", "浦口", "星火路", "高新开发区", "南信大", "盘城", "大厂",
        "江宁", "雨花", "南瑞", "国电南自", "埃斯顿", "中车浦镇", "中船鹏力", "nanjing",
    ]),
    ("江苏·苏锡常及其他", "江苏_苏州_无锡_常州等", [
        "苏州", "无锡", "常州", "南通", "镇江", "扬州", "徐州", "昆山", "太仓", "吴中",
        "工业园区", "高新区", "suzhou", "wuxi", "changzhou", "江苏",
    ]),
    ("上海", "上海", [
        "上海", "浦东", "闵行", "嘉定", "徐汇", "张江", "临港", "松江", "青浦", "shanghai",
    ]),
    ("浙江（杭州/宁波等）", "浙江_杭州_宁波等", [
        "杭州", "宁波", "嘉兴", "湖州", "绍兴", "温州", "滨江", "余杭", "萧山",
        "hangzhou", "ningbo", "浙江",
    ]),
]


def load_env(env_path: Path) -> Dict[str, str]:
    config: Dict[str, str] = {}
    if env_path.exists():
        for raw_line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            config[k.strip()] = v.strip().strip('"').strip("'")
    for k, v in os.environ.items():
        if k in ("EMAIL_PROVIDER", "EMAIL_ADDRESS", "EMAIL_APP_PASSWORD", "IMAP_SERVER", "IMAP_PORT", "SEARCH_DAYS"):
            config[k] = v
    return config


def decode_mime_words(text: Optional[str]) -> str:
    if not text:
        return ""
    parts = decode_header(text)
    decoded = []
    for content, charset in parts:
        if isinstance(content, bytes):
            enc = charset or "utf-8"
            try:
                decoded.append(content.decode(enc, errors="replace"))
            except LookupError:
                decoded.append(content.decode("utf-8", errors="replace"))
        else:
            decoded.append(str(content))
    return "".join(decoded).strip()


def strip_html(html_text: str) -> str:
    text = re.sub(r"<style[^>]*>.*?</style>", " ", html_text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>|</div>|</tr>|</li>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_body(msg: Message) -> str:
    plain_parts: List[str] = []
    html_parts: List[str] = []
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition") or "")
            if "attachment" in disp.lower():
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            charset = part.get_content_charset() or "utf-8"
            try:
                text = payload.decode(charset, errors="replace")
            except LookupError:
                text = payload.decode("utf-8", errors="replace")
            if ctype == "text/plain":
                plain_parts.append(text)
            elif ctype == "text/html":
                html_parts.append(strip_html(text))
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            try:
                text = payload.decode(charset, errors="replace")
            except LookupError:
                text = payload.decode("utf-8", errors="replace")
            if msg.get_content_type() == "text/html":
                html_parts.append(strip_html(text))
            else:
                plain_parts.append(text)
    return ("\n".join(plain_parts) if plain_parts else "\n".join(html_parts)).strip()


def desensitize_text(text: str) -> str:
    """Redact personal phone numbers, ID cards, verification codes, and private auth tokens."""
    # Redact Chinese mobile phone numbers
    text = re.sub(r"(?<!\d)(1[3-9]\d)\d{4}(\d{4})(?!\d)", r"\1****\2", text)
    # Redact 18-digit ID numbers
    text = re.sub(r"(?<!\d)(\d{6})\d{8}(\d{3}[\dXx])(?!\d)", r"\1********\2", text)
    # Redact sensitive query tokens in URLs (token, code, key, sign, auth, ticket)
    text = re.sub(
        r"([?&](?:token|access_token|code|auth|key|sign|signature|ticket|passcode)=)[^&\s\)\"'>]+",
        r"\1[REDACTED]",
        text,
        flags=re.IGNORECASE,
    )
    # Redact explicit passwords / OTP codes in text
    text = re.sub(
        r"((?:验证码|密码|通行码|口令|授权码|登录密码)\s*[：:]\s*)[A-Za-z0-9]{4,16}",
        r"\1[已脱敏]",
        text,
    )
    return text


def is_job_related(subject: str, sender: str, body: str) -> bool:
    combined = f"{subject}\n{sender}\n{body[:1500]}".lower()
    return any(kw in combined for kw in JOB_KEYWORDS)


def classify_email(subject: str, sender: str, body: str) -> Dict[str, str]:
    combined = f"{subject}\n{sender}\n{body}".lower()

    direction_label, direction_slug = "通用自动化 / 嵌入式及其他", "通用自动化_嵌入式及其他"
    for label, slug, kws in DIRECTION_RULES:
        if any(kw in combined for kw in kws):
            direction_label, direction_slug = label, slug
            break

    category_label, category_slug = "职位推荐与状态更新", "职位推荐与状态更新"
    for label, slug, kws in CATEGORY_RULES:
        if any(kw in combined for kw in kws):
            category_label, category_slug = label, slug
            break

    location_label, location_slug = "其他或待确认地点", "其他或待确认地点"
    for label, slug, kws in LOCATION_RULES:
        if any(kw in combined for kw in kws):
            location_label, location_slug = label, slug
            break

    return {
        "direction_label": direction_label,
        "direction_slug": direction_slug,
        "category_label": category_label,
        "category_slug": category_slug,
        "location_label": location_label,
        "location_slug": location_slug,
    }


def parse_message_object(msg: Message) -> Optional[Dict]:
    subject = decode_mime_words(msg.get("Subject")) or "(无主题)"
    sender = decode_mime_words(msg.get("From")) or "(未知发件人)"
    raw_date = msg.get("Date")
    try:
        dt_obj = parsedate_to_datetime(raw_date) if raw_date else dt.datetime.now(dt.timezone.utc)
        if dt_obj.tzinfo is None:
            dt_obj = dt_obj.replace(tzinfo=dt.timezone.utc)
        date_str = dt_obj.astimezone().strftime("%Y-%m-%d %H:%M")
    except Exception:
        date_str = dt.datetime.now().strftime("%Y-%m-%d %H:%M")

    body = extract_body(msg)
    if not is_job_related(subject, sender, body):
        return None

    clean_subject = desensitize_text(subject)
    clean_sender = desensitize_text(sender)
    clean_body = desensitize_text(body)
    labels = classify_email(clean_subject, clean_sender, clean_body)

    msg_id = msg.get("Message-ID") or f"{subject}-{sender}-{date_str}"
    uid_hash = hashlib.sha1(msg_id.encode("utf-8", errors="ignore")).hexdigest()[:10]
    summary_snippet = re.sub(r"\s+", " ", clean_body)[:180].strip()

    return {
        "id": uid_hash,
        "date": date_str,
        "subject": clean_subject,
        "sender": clean_sender,
        "summary": summary_snippet,
        "body": clean_body[:4000],
        **labels,
    }


def fetch_from_imap(config: Dict[str, str]) -> List[Dict]:
    provider = config.get("EMAIL_PROVIDER", "outlook").lower().strip()
    address = config.get("EMAIL_ADDRESS", "").strip()
    password = config.get("EMAIL_APP_PASSWORD", "").strip()
    if not address or not password or "your_" in address or "your_" in password:
        print("[INFO] 未检测到有效的 .env 邮箱凭据，跳过 IMAP 远程拉取（将检查本地 raw_drop 目录及已有归档）。")
        return []

    server, default_port = IMAP_PRESETS.get(provider, (config.get("IMAP_SERVER", ""), 993))
    server = config.get("IMAP_SERVER", server)
    port = int(config.get("IMAP_PORT", default_port))
    search_days = int(config.get("SEARCH_DAYS", 180))

    print(f"[INFO] 正在连接 IMAP 服务器 {server}:{port} ({address}) ...")
    results: List[Dict] = []
    since_date = (dt.date.today() - dt.timedelta(days=search_days)).strftime("%d-%b-%Y")

    with imaplib.IMAP4_SSL(server, port) as mail:
        mail.login(address, password)
        mail.select("INBOX", readonly=True)
        status, data = mail.search(None, f'(SINCE "{since_date}")')
        if status != "OK" or not data or not data[0]:
            return results
        msg_nums = data[0].split()
        print(f"[INFO] 检索到最近 {search_days} 天内共 {len(msg_nums)} 封邮件，正在筛选求职相关邮件...")
        for num in reversed(msg_nums[-300:]):  # Process up to 300 most recent emails
            res, msg_data = mail.fetch(num, "(RFC822)")
            if res != "OK" or not msg_data:
                continue
            for part in msg_data:
                if isinstance(part, tuple):
                    msg = email.message_from_bytes(part[1])
                    parsed = parse_message_object(msg)
                    if parsed:
                        results.append(parsed)
    print(f"[INFO] 从 IMAP 邮箱成功筛选出 {len(results)} 封求职相关邮件。")
    return results


def fetch_from_local_eml() -> List[Dict]:
    RAW_DROP_DIR.mkdir(parents=True, exist_ok=True)
    results: List[Dict] = []
    for eml_file in sorted(RAW_DROP_DIR.glob("*.eml")):
        raw_bytes = eml_file.read_bytes()
        msg = email.message_from_bytes(raw_bytes)
        parsed = parse_message_object(msg)
        if parsed:
            results.append(parsed)
    if results:
        print(f"[INFO] 从本地 emails/raw_drop/ 解析出 {len(results)} 封求职相关邮件。")
    return results


def render_table(items: List[Dict], rel_prefix: str = "./archive") -> str:
    if not items:
        return "> 当前分类暂无归档邮件。配置 `.env` 或放入 `.eml` 后运行 `python scripts/sync_emails.py` 即可自动生成。\n"
    lines = [
        "| 时间 | 主题 | 发件方 | 方向 | 类别 | 工作地点 | 脱敏详情 |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for item in items:
        safe_subj = item["subject"].replace("|", "｜")
        safe_sender = item["sender"].replace("|", "｜")
        link = f"[查看详情]({rel_prefix}/{item['id']}.md)"
        lines.append(
            f"| {item['date']} | **{safe_subj}** | {safe_sender} | {item['direction_label']} | {item['category_label']} | {item['location_label']} | {link} |"
        )
    return "\n".join(lines) + "\n"


def build_markdown_views(all_items: List[Dict]) -> None:
    EMAILS_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    dir_folder = EMAILS_DIR / "by_direction"
    cat_folder = EMAILS_DIR / "by_category"
    loc_folder = EMAILS_DIR / "by_location"
    for folder in (dir_folder, cat_folder, loc_folder):
        folder.mkdir(parents=True, exist_ok=True)

    # Sort descending by date
    all_items.sort(key=lambda x: x["date"], reverse=True)

    # 1. Write individual archive cards
    for item in all_items:
        card_path = ARCHIVE_DIR / f"{item['id']}.md"
        card_md = f"""# ✉️ {item['subject']}

- **收到时间**：`{item['date']}`
- **发件人**：`{item['sender']}`
- **所属方向**：`{item['direction_label']}`
- **邮件类别**：`{item['category_label']}`
- **工作地点**：`{item['location_label']}`
- **隐私状态**：🔒 已自动脱敏（个人手机号、身份证号、私密测评链接 Token 及验证码已隐去）

---

## 邮件正文摘要（脱敏后）

```text
{item['body']}
```
"""
        card_path.write_text(card_md, encoding="utf-8")

    # 2. Group and write by_direction, by_category, by_location
    all_directions = [r[0:2] for r in DIRECTION_RULES] + [("通用自动化 / 嵌入式及其他", "通用自动化_嵌入式及其他")]
    for label, slug in all_directions:
        subset = [x for x in all_items if x["direction_slug"] == slug]
        md = f"# 🧭 按方向归档：{label}\n\n共收录 **{len(subset)}** 封求职相关邮件。\n\n" + render_table(subset, "../archive")
        (dir_folder / f"{slug}.md").write_text(md, encoding="utf-8")

    all_categories = [r[0:2] for r in CATEGORY_RULES] + [("职位推荐与状态更新", "职位推荐与状态更新")]
    for label, slug in all_categories:
        subset = [x for x in all_items if x["category_slug"] == slug]
        md = f"# 🗂️ 按类别归档：{label}\n\n共收录 **{len(subset)}** 封求职相关邮件。\n\n" + render_table(subset, "../archive")
        (cat_folder / f"{slug}.md").write_text(md, encoding="utf-8")

    all_locations = [r[0:2] for r in LOCATION_RULES] + [("其他或待确认地点", "其他或待确认地点")]
    for label, slug in all_locations:
        subset = [x for x in all_items if x["location_slug"] == slug]
        md = f"# 📍 按工作地点归档：{label}\n\n共收录 **{len(subset)}** 封求职相关邮件。\n\n" + render_table(subset, "../archive")
        (loc_folder / f"{slug}.md").write_text(md, encoding="utf-8")

    # 3. Write master emails/INDEX.md
    now_str = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    index_lines = [
        "# 📬 求职邮件三维分类归档中心（方向 × 类别 × 工作地点）",
        "",
        f"> **最近同步时间**：`{now_str}` | **已归档求职邮件总数**：`{len(all_items)}` 封",
        "> **隐私保护策略**：所有同步至本仓库的邮件均经过正则自动脱敏（自动隐去个人手机号、身份证号、验证码及带私密 Token 的测评/面试链接）。",
        "",
        "---",
        "",
        "## 一、 三维分类快速导航",
        "",
        "### 1️⃣ 按【专业方向 (Direction)】浏览",
    ]
    for label, slug in all_directions:
        cnt = sum(1 for x in all_items if x["direction_slug"] == slug)
        index_lines.append(f"- [{label}](./by_direction/{slug}.md)（`{cnt}` 封）")

    index_lines.extend(["", "### 2️⃣ 按【邮件类别 (Category)】浏览"])
    for label, slug in all_categories:
        cnt = sum(1 for x in all_items if x["category_slug"] == slug)
        index_lines.append(f"- [{label}](./by_category/{slug}.md)（`{cnt}` 封）")

    index_lines.extend(["", "### 3️⃣ 按【工作地点 (Location)】浏览"])
    for label, slug in all_locations:
        cnt = sum(1 for x in all_items if x["location_slug"] == slug)
        index_lines.append(f"- [{label}](./by_location/{slug}.md)（`{cnt}` 封）")

    index_lines.extend([
        "",
        "---",
        "",
        "## 二、 全部求职邮件总表（按时间倒序）",
        "",
        render_table(all_items, "./archive"),
    ])

    (EMAILS_DIR / "INDEX.md").write_text("\n".join(index_lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync & classify job search emails into GitHub markdown.")
    parser.add_argument("--push", action="store_true", help="Commit and push changes to GitHub after syncing.")
    args = parser.parse_args()

    config = load_env(BASE_DIR / ".env")
    existing: Dict[str, Dict] = {}
    if DATA_FILE.exists():
        try:
            for item in json.loads(DATA_FILE.read_text(encoding="utf-8")):
                existing[item["id"]] = item
        except Exception:
            pass

    for item in fetch_from_imap(config) + fetch_from_local_eml():
        existing[item["id"]] = item

    all_items = list(existing.values())
    EMAILS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(all_items, ensure_ascii=False, indent=2), encoding="utf-8")
    build_markdown_views(all_items)
    print(f"[OK] 已生成三维分类索引（共 {len(all_items)} 封邮件）-> {EMAILS_DIR / 'INDEX.md'}")

    if args.push:
        subprocess.run(["git", "-C", str(BASE_DIR), "add", "emails/", "weekly_internships/", "README.md"], check=False)
        subprocess.run(
            ["git", "-C", str(BASE_DIR), "commit", "-m", f"chore(sync): update job emails & weekly tracker ({dt.date.today()})"],
            check=False,
        )
        subprocess.run(["git", "-C", str(BASE_DIR), "push", "origin", "main"], check=False)


if __name__ == "__main__":
    main()
