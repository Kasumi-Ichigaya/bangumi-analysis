import pandas as pd
import plotly.express as px

CSV_FILE = "bangumi_result.csv"
OUTPUT_HTML = "index_game.html"

# ===== 读取 CSV（自动处理 BOM）=====
df = pd.read_csv(CSV_FILE, encoding="utf-8-sig")

# 基础检查
required_cols = {"name", "mean", "std"}
if not required_cols.issubset(df.columns):
    raise ValueError(f"CSV 列不完整: {df.columns}")

# ===== 画散点图 =====
fig = px.scatter(
    df,
    x="std",
    y="mean",
    hover_name="name",          # 鼠标悬浮标题
    hover_data={
        "mean": ":.2f",
        "std": ":.2f",
    },
    labels={
        "std":"标准差（分歧程度）",
        "mean":"平均分（整体评价）",
    },
    title="Bangumi 游戏收藏评分分析",
)
fig.update_traces(
    marker=dict(size=9,opacity=0.75),
    selector=dict(mode="markers")
)
fig.update_layout(
    title_x=0.5,
    font=dict(size=14),
    hoverlabel=dict(
        bgcolor="white",
        font_size=13,
        font_family="Microsoft YaHei"
    )
)
# ===== 导出 HTML =====
fig.write_html(
    OUTPUT_HTML,
    include_plotlyjs="cdn",
    full_html=True
)

print(f"✅ 已生成 {OUTPUT_HTML}")
