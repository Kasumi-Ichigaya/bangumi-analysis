from flask import Flask
import plotly.graph_objs as go
import plotly.io as pio
import csv



app = Flask(__name__)

# 示例数据（你可以换成 CSV / 爬虫结果）
data = []
with open("bangumi_result.csv", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        name = row.get("name") or row.get("\ufeffname")
        mean = float(row["mean"])
        std = float(row["std"])

@app.route("/")
def index():
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=[d["mean"] for d in data],
        y=[d["std"] for d in data],
        mode="markers",
        marker=dict(size=10),
        text=[
            f"""
<b>{d['name']}</b><br>
平均分：{d['mean']}<br>
标准差：{d['std']}<br>
<a href='{d['url']}' target='_blank'>打开 Bangumi</a>
"""
            for d in data
        ],
        hoverinfo="text"
    ))

    fig.update_layout(
        title="Bangumi 评分分布（鼠标悬浮查看详情）",
        xaxis_title="平均分",
        yaxis_title="标准差",
        hoverlabel=dict(
            bgcolor="white",
            font_size=13
        )
    )

    return pio.to_html(fig, full_html=True)

if __name__ == "__main__":
    app.run(debug=True)
