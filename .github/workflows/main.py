import os
import requests
import json
import datetime
from bs4 import BeautifulSoup

# 1. 从 GitHub Secrets 获取环境变量
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY")
WECHAT_URL = os.getenv("WECHAT_ROBOT_URL")
MY_JD = os.getenv("JD_CONTENT", "我们组正在招聘顶尖产研人才，欢迎私信交流！")

def get_github_trending_top3():
    """抓取 GitHub Trending 前三名"""
    url = "https://github.com/trending"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('article', class_='Box-row', limit=3)
        
        trending_list = []
        for index, article in enumerate(articles):
            repo_info = article.h2.a.get_text(strip=True).replace(' ', '')
            link = "https://github.com" + article.h2.a['href']
            p_tag = article.find('p', class_='col-9')
            description = p_tag.get_text(strip=True) if p_tag else "No description"
            lang_tag = article.find('span', itemprop='programmingLanguage')
            language = lang_tag.get_text(strip=True) if lang_tag else "Unknown"
            stars_today = article.find('span', class_='d-inline-block float-sm-right').get_text(strip=True)

            trending_list.append({
                "rank": index + 1,
                "name": repo_info,
                "link": link,
                "desc": description,
                "lang": language,
                "stars_today": stars_today
            })
        return trending_list
    except Exception as e:
        print(f"抓取失败: {e}")
        return None

def call_deepseek(content):
    """调用 DeepSeek 生成小红书文案"""
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_KEY}"
    }
    prompt = f"""
    你是一个深谙产研圈文化的小红书博主，擅长把硬核 GitHub 项目讲得生动有趣。
    请根据以下热点和我的招聘需求，写一篇小红书笔记。
    
    【今日 GitHub 热点】:
    {content}
    
    【招聘岗位需求】:
    {MY_JD}
    
    要求：
    1. 标题要炸裂，带“程序员”、“避坑”、“涨薪”或“新工具”等关键词。
    2. 使用大量 Emoji，结构化排版。
    3. 语气口语化，像真人在分享，结尾自然引导私信。
    """
    payload = {
        "model": "deepseek-chat", # 生产环境建议用这个，性价比最高
        "messages": [
            {"role": "system", "content": "你是一个专业且幽默的产研招聘专家。"},
            {"role": "user", "content": prompt}
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"AI 生成失败: {e}"

def send_to_wechat_robot(text):
    """推送到企业微信机器人"""
    if not WECHAT_URL:
        print("未配置企业微信 URL，跳过推送")
        return
    headers = {"Content-Type": "application/json"}
    data = {
        "msgtype": "markdown",
        "markdown": {
            "content": f"### 🚀 今日产研获客文案已生成\n\n{text}"
        }
    }
    requests.post(WECHAT_URL, headers=headers, data=json.dumps(data))

if __name__ == "__main__":
    # 1. 抓取数据
    print("正在抓取 GitHub Trending...")
    data = get_github_trending_top3()
    
    if data:
        # 2. 格式化存入本地文件 (留作备份)
        report_content = f"--- Report Date: {datetime.date.today()} ---\n"
        for item in data:
            report_content += f"TOP {item['rank']}: {item['name']} | {item['stars_today']}\n{item['desc']}\n{item['link']}\n\n"
        
        with open("trending_report.txt", "w", encoding="utf-8") as f:
            f.write(report_content)
        
        # 3. 生成 AI 文案
        print("正在调用 DeepSeek 生成文案...")
        xhs_post = call_deepseek(report_content)
        
        # 4. 推送到微信
        print("正在推送到微信...")
        send_to_wechat_robot(xhs_post)
        
        print("全部任务完成！")
    else:
        print("抓取不到数据，任务结束。")
