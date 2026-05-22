#!/usr/bin/env python3
"""
AI 内容生成模块
读取 weather_data.json，调用 LLM（通过 OpenRouter API）生成：
- 天气点评
- 英语情话（带中文翻译）
- 每日金句
输出到 ai_content.json
"""

import json
import os
import sys
import urllib.request
import urllib.error

def load_weather():
    with open("weather_data.json", "r", encoding="utf-8") as f:
        return json.load(f)

def call_llm(prompt):
    """调用 OpenRouter API"""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        # 如果没有 API key，尝试用 Gemini（原项目方式）
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if gemini_key:
            return call_gemini(prompt, gemini_key)
        raise Exception("未设置 OPENROUTER_API_KEY 或 GEMINI_API_KEY")
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    data = json.dumps({
        "model": "google/gemini-2.0-flash-001",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
        "max_tokens": 500
    }).encode('utf-8')
    
    req = urllib.request.Request(
        url, data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/wechat-weather"
        }
    )
    
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read().decode('utf-8'))
    
    return result["choices"][0]["message"]["content"]


def call_gemini(prompt, api_key):
    """调用 Google Gemini API（备用）"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    data = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 500
        }
    }).encode('utf-8')
    
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"}
    )
    
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read().decode('utf-8'))
    
    try:
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise Exception(f"Gemini API 返回异常: {json.dumps(result, ensure_ascii=False)}")


def parse_ai_response(response_text):
    """解析 AI 返回的 JSON"""
    # 尝试直接从文本中提取 JSON 部分
    text = response_text.strip()
    
    # 如果被 markdown 代码块包裹
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 如果解析失败，尝试从中提取 JSON 对象
        import re
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise


def main():
    weather = load_weather()
    today = weather["today"]
    city = weather["city"]
    date = weather["date"]
    
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
    
    # 保存 AI 内容
    with open("ai_content.json", "w", encoding="utf-8") as f:
        json.dump(ai_content, f, ensure_ascii=False, indent=2)
    
    print(json.dumps(ai_content, ensure_ascii=False))
    
    # 同时输出到 GITHUB_OUTPUT
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"comment={ai_content['comment']}\n")
            f.write(f"love_en={ai_content['love_en']}\n")
            f.write(f"quote={ai_content['quote']}\n")


if __name__ == "__main__":
    main()
