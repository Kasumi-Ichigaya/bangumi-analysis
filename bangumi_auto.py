import math,time,os
import requests
import pandas as pd
import plotly.express as px
import plotly.io as pio
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
TYPE_INFO = {
    "Book":  {"key": "Book",  "cn": "书籍"},
    "Anime": {"key": "Anime", "cn": "动画"},
    "Music": {"key": "Music", "cn": "音乐"},
    "Game":  {"key": "Game",  "cn": "游戏"},
}


REQUEST_DELAY = 0.3
MAX_WORKERS = 6   # ✅ 推荐 4~6，别再高

# ==========================================

session = requests.Session()
session.headers.update(HEADERS)


def get_username(user_id):
    url = f"{API_BASE}/v0/users/{user_id}"
    r = session.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()
    return data.get("nickname") or data.get("username")
USERNAME = get_username(USER_ID)

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
    limit = 50

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
        votes = sum(counts.values())  # 总票数

        return {
            "name": name,
            "mean": round(mean, 3),
            "std": round(std, 3),
            "type": {1: "Book", 2: "Anime", 3: "Music", 4: "Game"}[subject_type], 
            "votes": votes,
            "url":f"https://bangumi.tv/subject/{subject_id}"
        }

    except Exception:
        return None

def make_toggle_html(df_map):

    # ===== A 组：Anime + Game（std）=====
    df_std = pd.concat(
        [df_map["Anime"], df_map["Game"]],
        ignore_index=True
    )
    x1_min, x1_max = df_std["std"].min(), df_std["std"].max()
    pad1 = (x1_max - x1_min) * 0.05
    X_RANGE_STD = [x1_min - pad1, x1_max + pad1]

    # ===== B 组：Book + Music（x_alt）=====
    df_alt = pd.concat(
    [df_map["Book"], df_map["Music"]],
    ignore_index=True)

    x2_min, x2_max = df_alt["std"].min(), df_alt["std"].max()
    pad2 = (x2_max - x2_min) * 0.05
    X_RANGE_ALT = [x2_min - pad2, x2_max + pad2]

    # ===== 所有图共用的纵轴（mean）=====
    df_all = pd.concat(df_map.values(), ignore_index=True)
    y_min, y_max = df_all["mean"].min(), df_all["mean"].max()
    pad_y = (y_max - y_min) * 0.05
    Y_RANGE = [y_min - pad_y, y_max + pad_y]
    def create_fig(df, title, X_RANGE, Y_RANGE):
        # 1. 在 px.scatter 中添加 labels 参数，让悬浮框也显示中文
        fig = px.scatter(
            df, x="std", y="mean", 
            hover_name="name", 
            render_mode='svg',
            labels={"std": "标准差 (分歧程度)", "mean": "平均分 (整体评价)"}
        )
        
        count = len(df)
        customdata = list(zip(df["url"], df.get("votes", [0]*count)))
        fig.update_traces(
            marker=dict(
                size=[9] * count,
                color=["#4f7cff"] * count,
                opacity=0.7,
                line=dict(width=0)
            ),
            customdata=customdata,
            hovertemplate="<b>%{hovertext}</b><br>标准差: %{x}<br>平均分: %{y}<br>投票人数: %{customdata[1]}<extra></extra>"
        )
        
        fig.update_layout(
            title=dict(text=title, x=0.5, xanchor='center'), # 标题居中
            width=1150, height=650,
            hovermode='closest',
            dragmode=False,
            # 2. 显式设置坐标轴的中文名称
            xaxis=dict(title="标准差 (分歧程度)", range=X_RANGE, showgrid=True),
            yaxis=dict(title="平均分 (整体评价)", range=Y_RANGE, showgrid=True),
            # 3. 字体与边距优化
            font=dict(family="Microsoft YaHei, SimHei, sans-serif"),
            margin=dict(l=80, r=40, t=80, b=80) 
        )
        return fig

    # 配置保持不变
    config = {
        "responsive": True, 
        "displayModeBar": True, 
        "modeBarButtonsToRemove": ["lasso2d", "select2d"],
        "displaylogo": False, 
    }
    
   
    plot_divs = []
    buttons = []
    first = True
    FIG_CONF = {
    "Anime": {"x_range": X_RANGE_STD,},
    "Game": {"x_range": X_RANGE_STD,},
    "Book": {"x_range": X_RANGE_ALT,},
    "Music": {"x_range": X_RANGE_ALT,},}
    for key, df in df_map.items():
        conf = FIG_CONF[key]

        div_id = f"canvas-{key.lower()}"

        html = pio.to_html(
            create_fig(
                df,
                title = f"{USERNAME} 的Bangumi {TYPE_INFO[key]['cn']}评分分布",
                X_RANGE=conf["x_range"],
                Y_RANGE=Y_RANGE,
            ),
            full_html=False,
            include_plotlyjs="cdn" if first else False,
            div_id=div_id,
            config=config,
        )
        plot_divs.append(
            f'<div class="plot{" active" if first else ""}" '
            f'id="container-{key.lower()}">{html}</div>'
        )

        buttons.append(
            f'<button data-target="{key.lower()}">{TYPE_INFO[key]["cn"]}</button>'
        )

        first = False
    
    def write_to_template(plot_divs, buttons, template_file="template.html", output_file="index.html"):
        with open(template_file, "r", encoding="utf-8") as f:
            template_html = f.read()
        plots_html = ''.join(plot_divs)
        buttons_html = ''.join(buttons)
        html = template_html.replace("<!-- PLOT_DIVS_PLACEHOLDER -->", plots_html)
        html = html.replace("<!-- BUTTONS_PLACEHOLDER -->", buttons_html)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)

    write_to_template(plot_divs, buttons, template_file="template.html", output_file="index.html")

    
def main():
    print("📥 获取收藏列表...")
    collections = get_collections(USER_ID)

    tasks = []
    results = []

    for item in collections:
        subject = item.get("subject", {})
        stype = subject.get("type")
        sid = item.get("subject_id")

        if stype in (1,2,3,4):#Book / Anime / Music / Game 已经都会被抓
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
    df = pd.DataFrame(results)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    make_toggle_html(
        {
            "Anime": df[df["type"] == "Anime"],
            "Game": df[df["type"] == "Game"],
            "Book": df[df["type"] == "Book"],
            "Music": df[df["type"] == "Music"],
        },
    )

    print("✅ 多线程完成，HTML 已生成")


if __name__ == "__main__":
    main()

