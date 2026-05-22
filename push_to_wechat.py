#!/usr/bin/env python3
"""
推送模块
读取 weather_data.json 和 ai_content.json，合成完整消息
通过 Server酱 发送到微信
"""

import json
import os
import sys
import urllib.request
import urllib.parse

def send_via_serverchan(send_key, title, content):
    """通过 Server酱 API 推送到微信"""
    url = f"https://sctapi.ftqq.com/{send_key}.send"
    data = urllib.parse.urlencode({
        "title": title,
        "content": content
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    
    resp = urllib.request.urlopen(req, timeout=15)
    result = resp.read().decode('utf-8')
    return json.loads(result)


def build_md_message(weather, ai_content):
    """构建 Markdown 格式推送消息"""
    
    city = weather["city"]
    date = weather["date"]
    weekday = weather["weekday"]
    today = weather["today"]
    forecast = weather["forecast"]
    
    lines = []
    lines.append(f"# ☀️ 早安！{city}")
    lines.append(f"📅 {date} {weekday}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 🌤 今日天气")
    lines.append("")
    lines.append(f"- **天气：** {today['weather']}")
    lines.append(f"- **温度：** {today['temp']}")
    lines.append("")
    
    if forecast:
        lines.append("---")
        lines.append("")
        lines.append("## 📅 一周预报")
        lines.append("")
        lines.append("| 日期 | 天气 | 温度 |")
        lines.append("|------|------|------|")
        for d in forecast[:5]:
            lines.append(f"| {d['date']} | {d['weather']} | {d['temp']} |")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    lines.append("## 💬 天气点评")
    lines.append("")
    lines.append(f"> {ai_content['comment']}")
    lines.append("")
    lines.append("## 💕 每日情话")
    lines.append("")
    lines.append(f"> {ai_content['love_en']}")
    lines.append("")
    lines.append("## 🌟 每日金句")
    lines.append("")
    lines.append(f"> {ai_content['quote']}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("💌 **祝你今天好心情！**")
    
    return "\n".join(lines)


def build_text_message(weather, ai_content):
    """纯文本格式备份（Server酱也支持）"""
    
    city = weather["city"]
    date = weather["date"]
    weekday = weather["weekday"]
    today = weather["today"]
    
    lines = []
    lines.append(f"☀️ 早安！{city}")
    lines.append(f"📅 {date} {weekday}")
    lines.append("")
    lines.append("━━━ 🌤 今日天气 ━━━")
    lines.append(f"天气：{today['weather']}")
    lines.append(f"温度：{today['temp']}")
    lines.append("")
    lines.append("━━━ 💬 天气点评 ━━━")
    lines.append(ai_content["comment"])
    lines.append("")
    lines.append("━━━ 💕 每日情话 ━━━")
    lines.append(ai_content["love_en"])
    lines.append("")
    lines.append("━━━ 🌟 每日金句 ━━━")
    lines.append(ai_content["quote"])
    lines.append("")
    lines.append("━━━━━━━━━━━━━━")
    lines.append("💌 祝你今天好心情！")
    
    return "\n".join(lines)


def main():
    # 读取天气数据
    with open("weather_data.json", "r", encoding="utf-8") as f:
        weather = json.load(f)
    
    # 读取 AI 内容
    with open("ai_content.json", "r", encoding="utf-8") as f:
        ai_content = json.load(f)
    
    # 获取 SendKey
    send_key = os.environ.get("SEND_KEY")
    if not send_key:
        print("ERROR: 环境变量 SEND_KEY 未设置", file=sys.stderr)
        sys.exit(1)
    
    # 构建消息
    md_message = build_md_message(weather, ai_content)
    
    # 发送
    title = f"☀️ 早安！{weather['city']} {weather['date']}"
    result = send_via_serverchan(send_key, title, md_message)
    
    # 保存结果
    with open("push_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    code = result.get("code", -1)
    if code == 0:
        print(f"✅ 推送成功！消息ID: {result.get('data', {}).get('pushid', 'N/A')}")
    else:
        print(f"❌ 推送失败: {result.get('message', '未知错误')} (code={code})")
        # 尝试用纯文本重试
        print("尝试用纯文本发送...", file=sys.stderr)
        text_message = build_text_message(weather, ai_content)
        result2 = send_via_serverchan(send_key, title, text_message)
        code2 = result2.get("code", -1)
        if code2 == 0:
            print("✅ 纯文本发送成功！")
        else:
            print(f"❌ 纯文本也失败了: {result2.get('message', '未知错误')}")
            sys.exit(1)


if __name__ == "__main__":
    main()
