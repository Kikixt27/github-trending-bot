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