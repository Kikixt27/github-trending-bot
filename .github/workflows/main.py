import requests
from bs4 import BeautifulSoup
import datetime

def get_github_trending_top3():
    url = "https://github.com/trending"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        # 找到所有的项目卡片
        articles = soup.find_all('article', class_='Box-row', limit=3)
        
        trending_list = []
        
        for index, article in enumerate(articles):
            # 获取项目名
            repo_info = article.h2.a.get_text(strip=True).replace(' ', '')
            link = "https://github.com" + article.h2.a['href']
            
            # 获取项目描述
            p_tag = article.find('p', class_='col-9')
            description = p_tag.get_text(strip=True) if p_tag else "No description"
            
            # 获取编程语言
            lang_tag = article.find('span', itemprop='programmingLanguage')
            language = lang_tag.get_text(strip=True) if lang_tag else "Unknown"
            
            # 获取今日增长的 Star 数
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
        return f"Error: {e}"

if __name__ == "__main__":
    print(f"--- {datetime.date.today()} GitHub Trending Top 3 ---")
    data = get_github_trending_top3()
    for item in data:
        print(f"TOP {item['rank']}: {item['name']} [{item['lang']}]")
        print(f"🔥 {item['stars_today']}")
        print(f"📝 {item['desc']}")
        print(f"🔗 {item['link']}\n")
import datetime

# ... 之前的 get_github_trending_top3 逻辑 ...

if __name__ == "__main__":
    data = get_github_trending_top3()
    
    # 格式化我们要保存的内容
    report_content = f"--- Report Date: {datetime.date.today()} ---\n"
    for item in data:
        report_content += f"TOP {item['rank']}: {item['name']}\n"
        report_content += f"Stars: {item['stars_today']} | Lang: {item['lang']}\n"
        report_content += f"Link: {item['link']}\n"
        report_content += f"Desc: {item['desc']}\n\n"

    # 1. 直接打印到 Log (GitHub Actions 的控制台能直接看到)
    print(report_content)

    # 2. 写入 .txt 文件 (这样脚本运行完，文件会留在仓库里)
    with open("trending_report.txt", "w", encoding="utf-8") as f:
        f.write(report_content)
        import os
import requests
import json

# 从 GitHub Secrets 获取
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY")
SLACK_URL = os.getenv("SLACK_WEBHOOK_URL")
MY_JD = os.getenv("JD_CONTENT")

def call_deepseek(content):
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
    1. 标题要带“程序员”、“避坑”、“涨薪”或“新工具”等关键词。
    2. 使用大量 Emoji，排版清爽。
    3. 语气要像真人在分享，不要有 AI 味。
    4. 结尾自然引导：'我们组也在招这方面的大牛，欢迎私信交流'。
    """

    payload = {
        "model": "deepseek-v4-pro", # 或者使用 deepseek-v4-flash
        "messages": [
            {"role": "system", "content": "你是一个专业且幽默的产研招聘专家。"},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }
    
    response = requests.post(url, headers=headers, json=payload)
    # DeepSeek 的响应结构与 OpenAI 一致
    return response.json()['choices'][0]['message']['content']

# ... 抓取和推送逻辑保持不变 ...
