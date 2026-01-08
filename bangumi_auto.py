import requests
import csv
import math
import time
import pandas as pd
import plotly.express as px
from concurrent.futures import ThreadPoolExecutor, as_completed

USER_ID = 888347
API_BASE = "https://api.bgm.tv"
OUTPUT_CSV = "bangumi_888347.csv"
OUTPUT_HTML_ANIME = "index.html"
OUTPUT_HTML_GAME = "index_game.html"
ACCESS_TOKEN = "kBgUZMutEmPoyYqgOX0zmxSN4qh9Jg3NpgCffc9V"

HEADERS = {
    "User-Agent": "12819/bgm-collection-fetcher (private-script)",
    "Accept": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}



REQUEST_DELAY = 0.3
MAX_WORKERS = 6   # ✅ 推荐 4~6，别再高

# ==========================================

session = requests.Session()
session.headers.update(HEADERS)


def calc_mean_std(counts):
    total = sum(counts.values())
    if total == 0:
        return None, None

    mean = sum(int(k) * v for k, v in counts.items()) / total
    var = sum(v * (int(k) - mean) ** 2 for k, v in counts.items()) / total
    return mean, math.sqrt(var)


def get_collections(user_id):
    items = []
    offset = 0
    limit = 30

    while True:
        url = f"{API_BASE}/v0/users/{user_id}/collections"
        params = {"limit": limit, "offset": offset,'type':2}

        r = session.get(url, params=params, timeout=10)
        if r.status_code == 400:
            break
        r.raise_for_status()

        data = r.json()
        if not data.get("data"):
            break

        items.extend(data["data"])
        offset += limit
        time.sleep(REQUEST_DELAY)

    return items


def fetch_subject(subject_id, subject_type):
    url = f"{API_BASE}/v0/subjects/{subject_id}"

    try:
        r = session.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()

        name = data.get("name_cn") or data.get("name")
        counts = data.get("rating", {}).get("count", {})

        mean, std = calc_mean_std(counts)
        if mean is None:
            return None

        return {
            "name": name,
            "mean": round(mean, 3),
            "std": round(std, 3),
            "type": subject_type
        }

    except Exception:
        return None


def make_html(df, output, title):
    if df.empty:
        return

    fig = px.scatter(
        df,
        x="std",
        y="mean",
        hover_name="name",
        labels={
            "std": "标准差（分歧程度）",
            "mean": "平均分（整体评价）"
        },
        title=title
    )

    fig.update_traces(marker=dict(size=9, opacity=0.75))
    fig.update_layout(font=dict(family="Microsoft YaHei"))
    fig.write_html(output)


def main():
    print("📥 获取收藏列表...")
    collections = get_collections(USER_ID)

    tasks = []
    results = []

    for item in collections:
        subject = item.get("subject", {})
        stype = subject.get("type")
        sid = item.get("subject_id")

        if stype in (2, 4):
            tasks.append((sid, stype))

    print(f"🚀 多线程抓取 {len(tasks)} 个 subject")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [
            pool.submit(fetch_subject, sid, stype)
            for sid, stype in tasks
        ]

        for f in as_completed(futures):
            res = f.result()
            if res:
                results.append(res)

    if not results:
        print("⚠ 无有效数据")
        return

    # ===== 写 CSV =====
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f, fieldnames=["name", "mean", "std", "type"]
        )
        writer.writeheader()
        writer.writerows(results)

    df = pd.read_csv(OUTPUT_CSV, encoding="utf-8-sig")

    make_html(df[df["type"] == 2], OUTPUT_HTML_ANIME, "Bangumi 动画评分分布")
    make_html(df[df["type"] == 4], OUTPUT_HTML_GAME, "Bangumi 游戏评分分布")

    print("✅ 多线程完成，HTML 已生成")


if __name__ == "__main__":
    main()
