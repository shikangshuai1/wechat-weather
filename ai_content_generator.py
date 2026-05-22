#!/usr/bin/env python3
"""
天气获取 + AI 内容生成模块
从中国天气网获取新乡天气，调用 DeepSeek API 生成天气点评、英语情话、每日金句
输出到 weather_data.json 和 ai_content.json
"""

import json
import os
import sys
import re
import urllib.request
import urllib.error
from datetime import datetime

CITY_NAME = "新乡"
WEATHER_URL = "https://www.weather.com.cn/weather/101180301.shtml"


# ========== 1. 获取天气 ==========
def fetch_weather():
    """从中国天气网获取新乡7天天气预报"""
    req = urllib.request.Request(
        WEATHER_URL,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    )
    resp = urllib.request.urlopen(req, timeout=15)
    content = resp.read().decode('utf-8')
    
    match = re.search(r'<ul class="t clearfix">(.*?)</ul>', content, re.DOTALL)
    if not match:
        raise Exception("无法解析天气数据")
    
    block = match.group(1)
    days = []
    li_pattern = re.compile(r'<li[^>]*>(.*?)</li>', re.DOTALL)
    
    for li in li_pattern.findall(block):
        date_m = re.search(r'<h1>(.*?)</h1>', li)
        weather_m = re.search(r'class="wea">(.*?)</', li)
        temp_m = re.search(r'class="tem">(.*?)</div>', li, re.DOTALL)
        
        date_str = date_m.group(1).strip() if date_m else ""
        weather_str = weather_m.group(1).strip() if weather_m else ""
        
        temp_str = ""
        if temp_m:
            temp_str = re.sub(r'<[^>]+>', ' ', temp_m.group(1))
            temp_str = re.sub(r'\s+', ' ', temp_str).strip()
        
        days.append({
            "date": date_str,
            "weather": weather_str,
            "temp": temp_str
        })
    
    return days


# ========== 2. 调用 DeepSeek API ==========
def call_llm(prompt):
    """调用 DeepSeek API 生成内容"""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise Exception("未设置 DEEPSEEK_API_KEY")
    
    url = "https://api.deepseek.com/chat/completions"
    
    data = json.dumps({
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
        "max_tokens": 500
    }).encode('utf-8')
    
    req = urllib.request.Request(
        url, data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    )
    
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read().decode('utf-8'))
    
    return result["choices"][0]["message"]["content"]


def parse_ai_response(response_text):
    """解析 AI 返回的 JSON"""
    text = response_text.strip()
    
    # 去除 markdown 代码块包裹
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise


def generate_ai_content(weather_data):
    """生成 AI 天气点评、情话、金句"""
    today = weather_data["today"]
    city = weather_data["city"]
    date = weather_data["date"]
    
    prompt = f"""你是一个温暖贴心的每日推送助手。

今天是{date}，{city}的天气情况如下：
- 天气：{today['weather']}
- 温度：{today['temp']}

请用**严格的 JSON 格式**输出以下三个内容（不要任何额外的说明文字）：

1. "comment": 一段温暖的天气点评（中文，2-3句话）。根据天气给出合适的提醒（如下雨带伞、天冷加衣、天热防晒等）。语气要像朋友一样贴心。
2. "love_en": 一句浪漫的英语情话（带中文翻译）。格式如 "You are my everything. 你是我的全部。"
3. "quote": 一句每日金句（中文），可以是名人名言、谚语或正能量语录。

输出格式（严格按照这个 JSON，不要加 markdown 标记）：
{{"comment": "...", "love_en": "...", "quote": "..."}}"""
    
    print("正在生成 AI 内容...", file=sys.stderr)
    
    try:
        response = call_llm(prompt)
        print(f"AI 响应: {response[:200]}...", file=sys.stderr)
        ai_content = parse_ai_response(response)
    except Exception as e:
        print(f"AI 生成失败: {e}，使用备用内容", file=sys.stderr)
        ai_content = {
            "comment": f"今天{city}{today['weather']}，温度{today['temp']}，注意天气变化，照顾好自己哦～",
            "love_en": "Every day with you is a beautiful day. 和你在一起的每一天都很美好。",
            "quote": "千里之行，始于足下。—— 老子"
        }
    
    return ai_content


def main():
    # 获取天气
    print("获取天气数据...", file=sys.stderr)
    days = fetch_weather()
    today = days[0]
    forecast = days[1:] if len(days) > 1 else []
    
    weekday_names = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    weekday = weekday_names[datetime.now().weekday()]
    
    weather_data = {
        "city": CITY_NAME,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "weekday": weekday,
        "today": today,
        "forecast": [{"date": d["date"], "weather": d["weather"], "temp": d["temp"]} for d in forecast]
    }
    
    # 保存天气数据
    with open("weather_data.json", "w", encoding="utf-8") as f:
        json.dump(weather_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 天气获取成功: {today['weather']} {today['temp']}", file=sys.stderr)
    
    # 生成 AI 内容
    ai_content = generate_ai_content(weather_data)
    
    # 保存 AI 内容
    with open("ai_content.json", "w", encoding="utf-8") as f:
        json.dump(ai_content, f, ensure_ascii=False, indent=2)
    
    print(f"✅ AI 内容生成成功", file=sys.stderr)
    
    # 输出 JSON 供后续步骤使用
    print(json.dumps(ai_content, ensure_ascii=False))


if __name__ == "__main__":
    main()
