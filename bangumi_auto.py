import requests
import csv
import math
import time
import os
import pandas as pd
import plotly.io as pio
import plotly.express as px
from concurrent.futures import ThreadPoolExecutor, as_completed

USER_ID = 888347
API_BASE = "https://api.bgm.tv"
OUTPUT_CSV = "bangumi_888347.csv"
OUTPUT_HTML = "index.html"
ACCESS_TOKEN = os.getenv("BGM_TOKEN")

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


def make_toggle_html(df_anime, df_game, output):
    # ===== 统一坐标范围（动画 + 游戏一起算）=====
    df_all = pd.concat([df_anime, df_game], ignore_index=True)

    x_min = df_all["std"].min()
    x_max = df_all["std"].max()
    y_min = df_all["mean"].min()
    y_max = df_all["mean"].max()

    # 留 5% 边距，防止点贴边
    pad_x = (x_max - x_min) * 0.05
    pad_y = (y_max - y_min) * 0.05

    X_RANGE = [x_min - pad_x, x_max + pad_x]
    Y_RANGE = [y_min - pad_y, y_max + pad_y]

    fig_anime = px.scatter(
        df_anime,
        x="std",
        y="mean",
        hover_name="name",
        labels={"std": "标准差（分歧程度）", "mean": "平均分（整体评价）"},
        title="Bangumi 动画评分分布"
    )
    fig_anime.update_traces(marker=dict(size=9, opacity=0.75))

    fig_game = px.scatter(
        df_game,
        x="std",
        y="mean",
        hover_name="name",
        labels={"std": "标准差（分歧程度）", "mean": "平均分（整体评价）"},
        title="Bangumi 游戏评分分布"
    )
    fig_game.update_traces(marker=dict(size=9, opacity=0.75))
    
    COMMON_LAYOUT = dict(
    width=1150,
    height=650,
    margin=dict(l=60, r=40, t=80, b=60),
    font=dict(family="Microsoft YaHei"),

    xaxis=dict(
        range=X_RANGE,
        showgrid=True,
        zeroline=False
    ),
    yaxis=dict(
        range=Y_RANGE,
        showgrid=True,
        zeroline=False
    ),
)


    fig_anime.update_layout(**COMMON_LAYOUT)
    fig_game.update_layout(**COMMON_LAYOUT)


    anime_html = pio.to_html(
    fig_anime,
    full_html=False,
    include_plotlyjs="cdn",
    div_id="anime"
)

    game_html = pio.to_html(
    fig_game,
    full_html=False,
    include_plotlyjs=False,
    div_id="game"
)


    html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Bangumi 评分散点图</title>
    <link rel="stylesheet" href="style.css">
</head>

<body>

<h2 style="text-align:center;">Bangumi 评分分布</h2>

<div class="page">
    <div class="chart-area">
        <div class="chart">
            <div class="plot active" id="plot-anime">
                {anime_html}
            </div>
            <div class="plot" id="plot-game">
                {game_html}
            </div>
        </div>
    </div>

    <div class="side">
        <button id="toggleBtn" onclick="toggleChart()">切换到游戏</button>
    </div>
</div>
<script src="toggle.js"></script>
</body>
</html>
"""


    with open(output, "w", encoding="utf-8") as f:
        f.write(html)



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

    make_toggle_html(
    df[df["type"] == 2],
    df[df["type"] == 4],
    OUTPUT_HTML   # 只生成一个 index.html
)


    print("✅ 多线程完成，HTML 已生成")


if __name__ == "__main__":
    main()

