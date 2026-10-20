#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Job Search Email Sync, Desensitization & 3D Classifier (Direction / Category / Location)
Repository: https://github.com/shukazuaki2025-lang/job_search
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
from typing import Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
EMAILS_DIR = BASE_DIR / "emails"
RAW_DROP_DIR = EMAILS_DIR / "raw_drop"
ARCHIVE_DIR = EMAILS_DIR / "archive"
DATA_FILE = EMAILS_DIR / "emails_metadata.json"

DIRECTIONS: List[Tuple[str, str]] = [
    ("工业自动化 / PLC / 控制", "工业自动化_PLC_控制"),
    ("电力电子 / 电机控制", "电力电子_电机控制"),
    ("机器人 / ROS / 运动控制", "机器人_ROS_运动控制"),
    ("自动驾驶 / 车辆控制", "自动驾驶_车辆控制"),
    ("通用自动化 / 嵌入式及高新制造", "通用自动化_嵌入式及其他"),
]

CATEGORIES: List[Tuple[str, str]] = [
    ("岗位每日精讲（名企岗位深度拆解）", "岗位每日精讲"),
    ("长三角高新企业晨报（实习与宣讲追踪）", "长三角高新企业晨报"),
    ("企业网申与投递确认（Rockwell / xAI 等）", "投递与网申确认"),
    ("南信大课题组科研与实训联系", "南信大课题组科研实训"),
    ("笔试测评 / 面试邀约 / Offer沟通", "面试与测评Offer沟通"),
]

LOCATIONS: List[Tuple[str, str]] = [
    ("江苏·南京（含南信大及周边）", "江苏_南京_含南信大周边"),
    ("江苏·苏锡常及其他（苏州/无锡/常州/昆山等）", "江苏_苏州_无锡_常州等"),
    ("上海", "上海"),
    ("浙江（杭州/宁波等）", "浙江_杭州_宁波等"),
    ("长三角多城综合 / 国际及其他", "其他或待确认地点"),
]


def desensitize_text(text: str) -> str:
    """Redact personal phone numbers, ID cards, verification codes, and private auth tokens."""
    # Redact Chinese mobile phone numbers
    text = re.sub(r"(?<!\d)(1[3-9]\d)\d{4}(\d{4})(?!\d)", r"\1****\2", text)
    # Redact 18-digit ID numbers
    text = re.sub(r"(?<!\d)(\d{6})\d{8}(\d{3}[\dXx])(?!\d)", r"\1********\2", text)
    # Redact sensitive query tokens in URLs
    text = re.sub(
        r"([?&](?:token|access_token|code|auth|key|sign|signature|ticket|passcode|verification_code)=)[^&\s\)\"'>]+",
        r"\1[REDACTED]",
        text,
        flags=re.IGNORECASE,
    )
    # Redact explicit passwords / OTP codes in text
    text = re.sub(
        r"((?:验证码|密码|通行码|口令|授权码|登录密码|Verification\s*Code)\s*[：:is]*\s*)[A-Za-z0-9]{4,16}",
        r"\1[已脱敏]",
        text,
        flags=re.IGNORECASE,
    )
    return text


def normalize_date(raw_date: str, subject: str) -> str:
    # Try to extract explicit YYYY-MM-DD from subject if present alongside time from raw_date
    m_sub = re.search(r"(202\d-\d{2}-\d{2})", subject)
    # Parse Gmail format like "Tue, Oct 20, 2026, 9:23 AM"
    cleaned = raw_date.replace("\u202f", " ").strip()
    for fmt in (
        "%a, %b %d, %Y, %I:%M %p",
        "%b %d, %Y, %I:%M %p",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ):
        try:
            # Strip leading day of week if needed
            dt_obj = dt.datetime.strptime(cleaned, fmt)
            return dt_obj.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            pass
    # Regex fallback for "Oct 20, 2026, 9:23 AM"
    m = re.search(r"([A-Z][a-z]{2})\s+(\d{1,2}),\s+(202\d)(?:,\s+(\d{1,2}:\d{2}\s*[AP]M))?", cleaned)
    if m:
        mon_str, day_str, yr_str, time_str = m.groups()
        time_part = time_str or "09:00 AM"
        try:
            dt_obj = dt.datetime.strptime(f"{mon_str} {day_str} {yr_str} {time_part}", "%b %d %Y %I:%M %p")
            return dt_obj.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            pass
    if m_sub:
        return f"{m_sub.group(1)} 09:00"
    return cleaned[:16]


def extract_sender(body_text: str, subject: str, raw_cat: str) -> str:
    lines = [ln.strip() for ln in body_text.splitlines() if ln.strip()]
    for ln in lines[:12]:
        if "rockwellautomation.com" in ln.lower():
            return "Rockwell Automation <ciam-notify@rockwellautomation.com>"
        if "@x.ai" in ln.lower() or "x.ai" in ln.lower():
            return "xAI Recruiting <no-reply@x.ai>"
        m = re.search(r"([^<>]+<[^<>]+@[^<>]+>)", ln)
        if m and "shukazuaki2025@gmail.com" not in m.group(1):
            return m.group(1).strip()
    if "rockwell" in subject.lower():
        return "Rockwell Automation <ciam-notify@rockwellautomation.com>"
    if "xai" in subject.lower():
        return "xAI Recruiting <no-reply@x.ai>"
    if raw_cat in ("岗位每日精讲", "长三角高新企业晨报"):
        return "NUIST Job Tracker <shukazuaki2025@gmail.com>"
    return "朱逸明 / 南信大课题组导师 <shukazuaki2025@gmail.com>"


def classify_email(subject: str, sender: str, body: str, raw_cat: str = "") -> Dict[str, str]:
    sub_lower = subject.lower()
    combined = f"{subject}\n{sender}\n{body[:2500]}".lower()

    # 1. Category (类别)
    if "岗位每日精讲" in subject or raw_cat == "岗位每日精讲":
        cat_label, cat_slug = CATEGORIES[0]
    elif "晨报" in subject or raw_cat == "长三角高新企业晨报":
        cat_label, cat_slug = CATEGORIES[1]
    elif any(k in sub_lower for k in ("rockwell", "xai", "applying", "application", "registration", "welcome to", "profile update", "location access")):
        cat_label, cat_slug = CATEGORIES[2]
    elif any(k in subject for k in ("自动化4班", "自动化大三", "南信大自动化本科生", "请教进组", "求教")):
        cat_label, cat_slug = CATEGORIES[3]
    elif any(k in sub_lower for k in ("面试", "笔试", "测评", "offer", "录用", "interview", "assessment")):
        cat_label, cat_slug = CATEGORIES[4]
    else:
        cat_label, cat_slug = CATEGORIES[2]

    # 2. Direction (方向)
    # Check subject first for precise per-email direction classification
    if any(k in sub_lower for k in ("电机", "电力电子", "功率半导体", "固态功率", "直流变换", "电能变换", "变换器", "伟创电气", "伺服驱动", "新能源电机")):
        dir_label, dir_slug = DIRECTIONS[1]  # 电力电子 / 电机控制
    elif any(k in sub_lower for k in ("机器人", "埃斯顿", "运动控制", "汇川", "高仙", "天准")):
        dir_label, dir_slug = DIRECTIONS[2]  # 机器人 / ROS / 运动控制
    elif any(k in sub_lower for k in ("自动驾驶", "车辆", "康尼机电", "轨道交通")):
        dir_label, dir_slug = DIRECTIONS[3]  # 自动驾驶 / 车辆控制
    elif any(k in sub_lower for k in ("plc", "rockwell", "舒尔", "智库智能", "中船鹏力", "恒立液压", "中控技术", "南瑞", "国电南自", "精测电子", "福拉特", "信捷电气", "卡特彼勒", "电控", "电气")):
        dir_label, dir_slug = DIRECTIONS[0]  # 工业自动化 / PLC / 控制
    elif "晨报" in subject:
        # Morning briefings primarily focus on PLC / industrial automation / equipment & high-tech manufacturing
        dir_label, dir_slug = DIRECTIONS[0]
    elif any(k in combined for k in ("电机", "电力电子", "foc", "逆变", "变流")):
        dir_label, dir_slug = DIRECTIONS[1]
    elif any(k in combined for k in ("机器人", "ros", "运动控制")):
        dir_label, dir_slug = DIRECTIONS[2]
    elif any(k in combined for k in ("plc", "工业自动化", "工控", "电气控制", "dcs", "scada")):
        dir_label, dir_slug = DIRECTIONS[0]
    else:
        dir_label, dir_slug = DIRECTIONS[4]  # 通用自动化 / 嵌入式及高新制造

    # 3. Location (工作地点)
    if cat_slug == "南信大课题组科研实训" or any(k in subject for k in ("南京", "中船鹏力", "南瑞", "国博电子", "埃斯顿", "国电南自", "康尼机电", "福拉特")):
        loc_label, loc_slug = LOCATIONS[0]  # 江苏·南京（含南信大及周边）
    elif any(k in subject for k in ("杭州", "宁波", "浙江", "中控技术")):
        loc_label, loc_slug = LOCATIONS[3]  # 浙江（杭州/宁波等）
    elif "上海" in subject or any(k in combined for k in ("上海临港", "非夕", "高仙机器人", "rockwellautomation")):
        loc_label, loc_slug = LOCATIONS[2]  # 上海
    elif any(k in subject for k in ("苏州", "张家港", "常州", "无锡", "昆山", "徐州", "德晟达", "智库智能", "舒尔", "是为科技", "恒立液压", "天准", "长光华芯", "精测电子", "信捷", "伟创", "华天", "汇川", "卡特彼勒")):
        loc_label, loc_slug = LOCATIONS[1]  # 江苏·苏锡常及其他
    elif "南信大" in subject:
        loc_label, loc_slug = LOCATIONS[0]  # 江苏·南京（含南信大及周边）
    else:
        loc_label, loc_slug = LOCATIONS[4]

    return {
        "direction_label": dir_label,
        "direction_slug": dir_slug,
        "category_label": cat_label,
        "category_slug": cat_slug,
        "location_label": loc_label,
        "location_slug": loc_slug,
    }


def load_browser_extracted_json(json_path: Path, drafts_path: Optional[Path] = None) -> List[Dict]:
    if not json_path.exists():
        return []
    raw_data = json.loads(json_path.read_text(encoding="utf-8"))
    emails_list = raw_data.get("emails", [])

    drafts_map: Dict[str, str] = {}
    if drafts_path and drafts_path.exists():
        d_data = json.loads(drafts_path.read_text(encoding="utf-8"))
        for d in d_data.get("drafts", []):
            if d.get("threadId") and d.get("bodyText"):
                drafts_map[d["threadId"]] = d["bodyText"]

    results: List[Dict] = []
    for entry in emails_list:
        tid = entry.get("threadId") or hashlib.sha1(entry.get("subject", "").encode("utf-8")).hexdigest()[:12]
        subject = entry.get("subject", "(无主题)").strip()
        raw_date = entry.get("date", "")
        raw_cat = entry.get("category", "")
        body = entry.get("bodyText", "")
        if tid in drafts_map and len(drafts_map[tid]) > len(body):
            body = drafts_map[tid]

        date_str = normalize_date(raw_date, subject)
        sender = extract_sender(body, subject, raw_cat)

        clean_subject = desensitize_text(subject)
        clean_sender = desensitize_text(sender)
        clean_body = desensitize_text(body)
        labels = classify_email(clean_subject, clean_sender, clean_body, raw_cat)

        summary_snippet = re.sub(r"\s+", " ", clean_body)[:200].strip()
        results.append({
            "id": tid,
            "date": date_str,
            "subject": clean_subject,
            "sender": clean_sender,
            "summary": summary_snippet,
            "body": clean_body,
            **labels,
        })
    return results


def render_table(items: List[Dict], rel_prefix: str = "./archive") -> str:
    if not items:
        return "> 当前分类暂无归档邮件。\n"
    lines = [
        "| 时间 | 主题 | 发件方/来源 | 技术方向 | 邮件类别 | 工作地点 | 脱敏全文 |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for item in items:
        safe_subj = item["subject"].replace("|", "｜")
        safe_sender = item["sender"].replace("|", "｜").replace("<", "&lt;").replace(">", "&gt;")
        link = f"[查看详情]({rel_prefix}/{item['id']}.md)"
        lines.append(
            f"| `{item['date']}` | **{safe_subj}** | {safe_sender} | {item['direction_label']} | {item['category_label']} | {item['location_label']} | {link} |"
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
        # Clean old markdown files so renamed slugs don't leave stale files
        for old_md in folder.glob("*.md"):
            old_md.unlink()

    all_items.sort(key=lambda x: (x["date"], x["id"]), reverse=True)

    # 1. Write individual archive cards
    for item in all_items:
        card_path = ARCHIVE_DIR / f"{item['id']}.md"
        card_md = f"""# ✉️ {item['subject']}

- **邮件 ID**：`{item['id']}`
- **时间**：`{item['date']}`
- **发件人/来源**：`{item['sender']}`
- **技术方向 (Direction)**：**{item['direction_label']}**
- **邮件类别 (Category)**：**{item['category_label']}**
- **工作地点 (Location)**：**{item['location_label']}**
- **隐私状态**：🔒 已自动脱敏（手机号、身份证号、验证码及私密链接 Token 已隐去）

[⬅️ 返回邮件总控台](../INDEX.md)

---

## 邮件正文（脱敏归档）

```text
{item['body']}
```
"""
        card_path.write_text(card_md, encoding="utf-8")

    # 2. Group and write by_direction, by_category, by_location
    for label, slug in DIRECTIONS:
        subset = [x for x in all_items if x["direction_slug"] == slug]
        md = (
            f"# 🧭 按技术方向归档：{label}\n\n"
            f"[⬅️ 返回邮件总控台](../INDEX.md) | 共收录 **{len(subset)}** 封求职/实习/科研相关邮件。\n\n"
            + render_table(subset, "../archive")
        )
        (dir_folder / f"{slug}.md").write_text(md, encoding="utf-8")

    for label, slug in CATEGORIES:
        subset = [x for x in all_items if x["category_slug"] == slug]
        md = (
            f"# 🗂️ 按邮件类别归档：{label}\n\n"
            f"[⬅️ 返回邮件总控台](../INDEX.md) | 共收录 **{len(subset)}** 封求职/实习/科研相关邮件。\n\n"
            + render_table(subset, "../archive")
        )
        (cat_folder / f"{slug}.md").write_text(md, encoding="utf-8")

    for label, slug in LOCATIONS:
        subset = [x for x in all_items if x["location_slug"] == slug]
        md = (
            f"# 📍 按工作地点归档：{label}\n\n"
            f"[⬅️ 返回邮件总控台](../INDEX.md) | 共收录 **{len(subset)}** 封求职/实习/科研相关邮件。\n\n"
            + render_table(subset, "../archive")
        )
        (loc_folder / f"{slug}.md").write_text(md, encoding="utf-8")

    # 3. Write master emails/INDEX.md
    now_str = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    index_lines = [
        "# 📬 求职与实习邮件三维分类归档中心（方向 × 类别 × 工作地点）",
        "",
        f"> **绑定邮箱**：`shukazuaki2025@gmail.com` | **最近同步时间**：`{now_str}` | **已归档邮件总数**：**`{len(all_items)}` 封**",
        "> **隐私保护策略**：所有同步至本仓库的邮件均经过正则自动脱敏（隐去个人手机号、身份证号、验证码及带私密 Token 的链接）。",
        "",
        "---",
        "",
        "## 一、 三维分类统计与快速导航",
        "",
        "### 1️⃣ 按【技术方向 (Direction)】浏览",
        "| 技术方向 | 邮件数量 | 分类汇总页 |",
        "| :--- | :--- | :--- |",
    ]
    for label, slug in DIRECTIONS:
        cnt = sum(1 for x in all_items if x["direction_slug"] == slug)
        index_lines.append(f"| **{label}** | `{cnt}` 封 | [进入查看](./by_direction/{slug}.md) |")

    index_lines.extend([
        "",
        "### 2️⃣ 按【邮件类别 (Category)】浏览",
        "| 邮件类别 | 邮件数量 | 分类汇总页 |",
        "| :--- | :--- | :--- |",
    ])
    for label, slug in CATEGORIES:
        cnt = sum(1 for x in all_items if x["category_slug"] == slug)
        index_lines.append(f"| **{label}** | `{cnt}` 封 | [进入查看](./by_category/{slug}.md) |")

    index_lines.extend([
        "",
        "### 3️⃣ 按【工作地点 (Location)】浏览",
        "| 工作地点 | 邮件数量 | 分类汇总页 |",
        "| :--- | :--- | :--- |",
    ])
    for label, slug in LOCATIONS:
        cnt = sum(1 for x in all_items if x["location_slug"] == slug)
        index_lines.append(f"| **{label}** | `{cnt}` 封 | [进入查看](./by_location/{slug}.md) |")

    index_lines.extend([
        "",
        "---",
        "",
        f"## 二、 全部求职相关邮件总表（共 {len(all_items)} 封，按时间倒序）",
        "",
        render_table(all_items, "./archive"),
    ])

    (EMAILS_DIR / "INDEX.md").write_text("\n".join(index_lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync & classify job search emails into GitHub markdown.")
    parser.add_argument("--import-json", type=str, default="", help="Path to browser-extracted Gmail JSON file.")
    parser.add_argument("--drafts-json", type=str, default="", help="Path to browser-extracted Gmail drafts JSON file.")
    parser.add_argument("--push", action="store_true", help="Commit and push changes to GitHub after syncing.")
    args = parser.parse_args()

    existing: Dict[str, Dict] = {}
    if DATA_FILE.exists():
        try:
            for item in json.loads(DATA_FILE.read_text(encoding="utf-8")):
                existing[item["id"]] = item
        except Exception:
            pass

    if args.import_json:
        j_path = Path(args.import_json)
        d_path = Path(args.drafts_json) if args.drafts_json else None
        imported = load_browser_extracted_json(j_path, d_path)
        print(f"[INFO] 从浏览器提取的 JSON 导入了 {len(imported)} 封求职邮件。")
        for item in imported:
            existing[item["id"]] = item

    all_items = list(existing.values())
    EMAILS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(all_items, ensure_ascii=False, indent=2), encoding="utf-8")
    build_markdown_views(all_items)
    print(f"[OK] 已生成三维分类索引（共 {len(all_items)} 封邮件）-> {EMAILS_DIR / 'INDEX.md'}")

    if args.push:
        subprocess.run(["git", "-C", str(BASE_DIR), "add", "-A"], check=False)
        subprocess.run(
            ["git", "-C", str(BASE_DIR), "commit", "-m", f"feat(emails): sync & classify {len(all_items)} job emails from Gmail by direction, category, and location"],
            check=False,
        )
        subprocess.run(["git", "-C", str(BASE_DIR), "push", "origin", "main"], check=False)


if __name__ == "__main__":
    main()
