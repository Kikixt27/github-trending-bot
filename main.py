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
    """调用 DeepSeek 生成面向 AI PM / Product Builder 的简报式文案"""
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_KEY}"
    }
    prompt = f"""
    你是 Senior AI PM / Product Builder，给同类人写一则「GitHub Trending 简报」：冷静、具体、略带观点，不要喊麦式营销。

    【今日 GitHub 热点（仅允许使用其中事实，勿编造 benchmark/通过率/未出现的功能）】:
    {content}

    【招聘/合作说明（原文照收，可压缩措辞但勿篡改事实与联系方式）】:
    {MY_JD}

    输出结构与顺序（用 --- 分段；全文 emoji 不超过 8 个，可不用）:
    1) 标题：单独一行，可犀利但不堆砌流量词；可含 GitHub / Agent / PM / Builder / 开源 等与读者相关的词之一，勿强制「程序员」「涨薪」「避坑」。
    2) 开场：2–4 句，说明今天为什么值得扫一眼 Trending（基于给定数据，保守推断）。
    3) 对每个热点仓库（按输入顺序，共 3 个），固定三节小标题：
       - 一句话：解决什么问题 / 适合谁
       - Why now：结合 stars_today、语言、描述，说明「为何此刻在榜上」；勿夸大未提供的数据
       - PM / builder 视角：集成或试用成本、合规/维护/风险、建议的下一步（如 clone、先看哪类 issue、和谁对齐）
       每个仓库附上输入中的链接一行。
    4) 招聘节：单独一节「在招 / 合作」，全文不超过 120 字（汉字计），语气像 JD 摘要 + 筛选标准；若需行动指引，仅用招聘原文里已有的方式（如邮箱/链接），勿写「私我抄近道」类话术。
    5) 可选：末尾 3–5 个话题标签，勿超过 5 个，勿重复堆砌。

    禁用套话与表达（出现即改写删除）: 卷麻了、鲤鱼打挺、懂的都懂、兄弟们/姐妹们、神仙岗、划重点、炸裂、被大佬卷、摸鱼刷到、不写 PRD 只写代码还能涨薪 X% 等未在招聘原文出现的具体数字承诺。

    语言：中文。
    """
    payload = {
        "model": "deepseek-chat",  # 生产环境建议用这个，性价比最高
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是资深 AI 产品人兼能落地的 builder：写简报时优先可执行信息与诚实边界，"
                    "拒绝小红书爆款模板与未经验证的性能宣称。"
                ),
            },
            {"role": "user", "content": prompt},
        ],
        # OpenAI 兼容接口常用参数：略降 temperature 可减少套话漂移；max_tokens 防止过长灌水
        "temperature": 0.7,
        "max_tokens": 2500,
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"AI 生成失败: {e}"

def _truncate_utf8_bytes(s: str, max_bytes: int) -> str:
    """企业微信 markdown 的 content 上限为 4096 字节（UTF-8），截断时避免半个汉字。"""
    raw = s.encode("utf-8")
    if len(raw) <= max_bytes:
        return s
    raw = raw[:max_bytes]
    while raw and (raw[-1] & 0xC0) == 0x80:
        raw = raw[:-1]
    return raw.decode("utf-8", errors="ignore")


def send_to_wechat_robot(text):
    """推送到企业微信机器人（使用 json= 发 JSON，避免 errcode 93017 等格式错误）"""
    if not WECHAT_URL:
        print("未配置企业微信 URL，跳过推送")
        return
    header = "### GitHub Trending · AI PM 简报\n\n"
    max_content_bytes = 4096
    room = max_content_bytes - len(header.encode("utf-8"))
    body = _truncate_utf8_bytes(text or "", max(0, room))
    data = {
        "msgtype": "markdown",
        "markdown": {"content": header + body},
    }
    try:
        r = requests.post(WECHAT_URL, json=data, timeout=15)
        r.raise_for_status()
        out = r.json()
        if out.get("errcode", 0) != 0:
            print(f"企业微信返回错误: {out}")
    except Exception as e:
        print(f"推送到企业微信失败: {e}")

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
