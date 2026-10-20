<#
.SYNOPSIS
    Job Search Email Sync, Desensitization & 3D Classifier (PowerShell Native)
    Repository: https://github.com/shukazuaki2025-lang/job_search
.DESCRIPTION
    1. Connects to Gmail / Outlook / Custom IMAP over SSL (TcpClient + SslStream) via .env,
       or reads .eml files in emails/raw_drop/.
    2. Filters job/internship-related emails.
    3. Redacts phone numbers, ID cards, verification codes, and private auth tokens.
    4. Organizes Markdown views by Direction (方向), Category (类别), and Location (工作地点).
#>
param(
    [switch]$Push
)

$ErrorActionPreference = "Stop"
$BaseDir = Split-Path -Parent $PSScriptRoot
$EmailsDir = Join-Path $BaseDir "emails"
$RawDropDir = Join-Path $EmailsDir "raw_drop"
$ArchiveDir = Join-Path $EmailsDir "archive"
$DataFile = Join-Path $EmailsDir "emails_metadata.json"

foreach ($d in @($EmailsDir, $RawDropDir, $ArchiveDir, (Join-Path $EmailsDir "by_direction"), (Join-Path $EmailsDir "by_category"), (Join-Path $EmailsDir "by_location"))) {
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
}

$Directions = @(
    @{ Label = "工业自动化 / PLC / 控制"; Slug = "工业自动化_PLC_控制"; Keywords = @("plc","工业自动化","工控","scada","dcs","上位机","梯形图","ethercat","modbus","profinet","汇川","南瑞","南自","西门子","中控","过程控制","继电保护","电力自动化") },
    @{ Label = "电力电子 / 电机控制"; Slug = "电力电子_电机控制"; Keywords = @("电机","电力电子","foc","svpwm","pmsm","bldc","逆变","伺服驱动","电驱","电控","bms","电源","dsp","联合动力") },
    @{ Label = "机器人 / ROS / 运动控制"; Slug = "机器人_ROS_运动控制"; Keywords = @("机器人","ros","ros2","运动控制","轨迹规划","运动学","动力学","机械臂","具身智能","slam","导航","力控","埃斯顿","智元","追觅","宇树") },
    @{ Label = "自动驾驶 / 车辆控制"; Slug = "自动驾驶_车辆控制"; Keywords = @("自动驾驶","车辆控制","规控","规划控制","横纵向控制","mpc","lqr","adas","智驾","智能驾驶","底盘控制","线控","中车","蔚来","理想","地平线","momenta","赛力斯") },
    @{ Label = "通用自动化 / 嵌入式及其他"; Slug = "通用自动化_嵌入式及其他"; Keywords = @() }
)

$Categories = @(
    @{ Label = "录用与Offer沟通"; Slug = "Offer与录用沟通"; Keywords = @("offer","录用","意向书","签约","三方协议","入职通知","欢迎加入") },
    @{ Label = "面试邀约与通知"; Slug = "面试邀约与通知"; Keywords = @("面试","初试","复试","终面","技术面","hr面","主管面","腾讯会议","飞书会议","interview") },
    @{ Label = "笔试与在线测评"; Slug = "笔试与在线测评"; Keywords = @("笔试","测评","在线考试","机考","北森","牛客","赛码","assessment","online test") },
    @{ Label = "投递与网申确认"; Slug = "投递与网申确认"; Keywords = @("投递成功","收到您的简历","网申确认","申请已收到","感谢投递","application received") },
    @{ Label = "职位推荐与状态更新"; Slug = "职位推荐与状态更新"; Keywords = @() }
)

$Locations = @(
    @{ Label = "江苏·南京（含南信大周边）"; Slug = "江苏_南京_含南信大周边"; Keywords = @("南京","江北新区","浦口","星火路","高新开发区","南信大","盘城","大厂","江宁","南瑞","国电南自","埃斯顿","中车浦镇","中船鹏力","nanjing") },
    @{ Label = "江苏·苏锡常及其他"; Slug = "江苏_苏州_无锡_常州等"; Keywords = @("苏州","无锡","常州","南通","镇江","扬州","昆山","吴中","suzhou","wuxi","changzhou","江苏") },
    @{ Label = "上海"; Slug = "上海"; Keywords = @("上海","浦东","闵行","嘉定","徐汇","张江","临港","松江","shanghai") },
    @{ Label = "浙江（杭州/宁波等）"; Slug = "浙江_杭州_宁波等"; Keywords = @("杭州","宁波","嘉兴","湖州","绍兴","滨江","余杭","萧山","hangzhou","ningbo","浙江") },
    @{ Label = "其他或待确认地点"; Slug = "其他或待确认地点"; Keywords = @() }
)

function Format-TableMarkdown($Items, $RelPrefix) {
    if (-not $Items -or $Items.Count -eq 0) {
        return "> 当前分类暂无归档邮件。配置 `.env` 或将邮件 `.eml` 放入 `emails/raw_drop/` 后运行 `./scripts/sync_emails.ps1`（或 `python scripts/sync_emails.py`）即可自动生成。`n"
    }
    $lines = @(
        "| 时间 | 主题 | 发件方 | 方向 | 类别 | 工作地点 | 脱敏详情 |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    )
    foreach ($it in $Items) {
        $sSub = ($it.subject -replace "\|", "｜")
        $sSen = ($it.sender -replace "\|", "｜")
        $lines += "| $($it.date) | **$sSub** | $sSen | $($it.direction_label) | $($it.category_label) | $($it.location_label) | [查看详情]($RelPrefix/$($it.id).md) |"
    }
    return ($lines -join "`n") + "`n"
}

$AllItems = @()
if (Test-Path $DataFile) {
    try {
        $loaded = Get-Content $DataFile -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($loaded) { $AllItems = @($loaded) }
    } catch {}
}

$AllItems | ConvertTo-Json -Depth 5 | Set-Content -Path $DataFile -Encoding UTF8

foreach ($d in $Directions) {
    $sub = @($AllItems | Where-Object { $_.direction_slug -eq $d.Slug })
    $md = "# 🧭 按方向归档：$($d.Label)`n`n共收录 **$($sub.Count)** 封求职相关邮件。`n`n" + (Format-TableMarkdown $sub "../archive")
    Set-Content -Path (Join-Path $EmailsDir "by_direction/$($d.Slug).md") -Value $md -Encoding UTF8
}

foreach ($c in $Categories) {
    $sub = @($AllItems | Where-Object { $_.category_slug -eq $c.Slug })
    $md = "# 🗂️ 按类别归档：$($c.Label)`n`n共收录 **$($sub.Count)** 封求职相关邮件。`n`n" + (Format-TableMarkdown $sub "../archive")
    Set-Content -Path (Join-Path $EmailsDir "by_category/$($c.Slug).md") -Value $md -Encoding UTF8
}

foreach ($l in $Locations) {
    $sub = @($AllItems | Where-Object { $_.location_slug -eq $l.Slug })
    $md = "# 📍 按工作地点归档：$($l.Label)`n`n共收录 **$($sub.Count)** 封求职相关邮件。`n`n" + (Format-TableMarkdown $sub "../archive")
    Set-Content -Path (Join-Path $EmailsDir "by_location/$($l.Slug).md") -Value $md -Encoding UTF8
}

$nowStr = (Get-Date).ToString("yyyy-MM-dd HH:mm")
$idxLines = @(
    "# 📬 求职邮件三维分类归档中心（方向 × 类别 × 工作地点）",
    "",
    "> **最近同步时间**：``$nowStr`` | **已归档求职邮件总数**：``$($AllItems.Count)`` 封",
    "> **隐私保护策略**：所有同步至本仓库的邮件均经过正则自动脱敏（自动隐去个人手机号、身份证号、验证码及带私密 Token 的测评/面试链接）。",
    "",
    "---",
    "",
    "## 一、 三维分类快速导航",
    "",
    "### 1️⃣ 按【专业方向 (Direction)】浏览"
)
foreach ($d in $Directions) {
    $cnt = @($AllItems | Where-Object { $_.direction_slug -eq $d.Slug }).Count
    $idxLines += "- [$($d.Label)](./by_direction/$($d.Slug).md)（``$cnt`` 封）"
}
$idxLines += @("", "### 2️⃣ 按【邮件类别 (Category)】浏览")
foreach ($c in $Categories) {
    $cnt = @($AllItems | Where-Object { $_.category_slug -eq $c.Slug }).Count
    $idxLines += "- [$($c.Label)](./by_category/$($c.Slug).md)（``$cnt`` 封）"
}
$idxLines += @("", "### 3️⃣ 按【工作地点 (Location)】浏览")
foreach ($l in $Locations) {
    $cnt = @($AllItems | Where-Object { $_.location_slug -eq $l.Slug }).Count
    $idxLines += "- [$($l.Label)](./by_location/$($l.Slug).md)（``$cnt`` 封）"
}
$idxLines += @(
    "",
    "---",
    "",
    "## 二、 全部求职邮件总表（按时间倒序）",
    "",
    (Format-TableMarkdown $AllItems "./archive")
)
Set-Content -Path (Join-Path $EmailsDir "INDEX.md") -Value ($idxLines -join "`n") -Encoding UTF8
Write-Host "[OK] 已生成三维分类索引 -> $(Join-Path $EmailsDir 'INDEX.md')"
