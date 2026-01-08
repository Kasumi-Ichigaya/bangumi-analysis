import csv
import matplotlib.pyplot as plt
import mplcursors
import numpy as np
from matplotlib.lines import Line2D


# ===== 中文字体修复 =====
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False
# =======================

CSV_FILE = "bangumi_888347.csv"

means = []
stds = []
names = []
types = []

with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        means.append(float(row["mean"]))
        stds.append(float(row["std"]))
        names.append(row["name"])
        types.append(row.get("type"))   # ← 关键：安全读取

means = np.array(means)
stds = np.array(stds)

# ===== 判断是否存在 type =====
has_type = any(t in ("2", "4") for t in types)

# ===== 颜色映射（仅在有 type 时使用）=====
color_map = {
    "2": "#1f77b4",  # 动画
    "4": "#ff7f0e",  # 游戏
}

if has_type:
    colors = [color_map.get(t, "gray") for t in types]
else:
    colors = None   # matplotlib 自动用默认颜色

mean_line = means.mean()
std_line = stds.mean()

# ===== 图 =====
fig, ax = plt.subplots(figsize=(9, 7))

sc = ax.scatter(
    stds,
    means,
    c=colors,
    alpha=0.75,
    zorder=5
)

# ===== 图例（只有有 type 才加）=====
if has_type:
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='动画',
               markerfacecolor=color_map["2"], markersize=8),
        Line2D([0], [0], marker='o', color='w', label='游戏',
               markerfacecolor=color_map["4"], markersize=8),
    ]
    ax.legend(handles=legend_elements, title="类型")

# ===== 分界线 =====
ax.axhline(mean_line, linestyle="--", linewidth=1, zorder=2)
ax.axvline(std_line, linestyle="--", linewidth=1, zorder=2)

# ===== 标题 & 坐标 =====
title = "Bangumi 评分分布（含分界线）"
if has_type:
    title = "Bangumi 动画 / 游戏评分分布（含分界线）"

ax.set_title(title)
ax.set_xlabel("标准差（分歧程度）")
ax.set_ylabel("平均分（整体评价）")
ax.grid(True, zorder=0)

# ===== 分界值标签 =====
ax.text(
    -0.08, mean_line,
    f"平均分均值 = {mean_line:.2f}",
    transform=ax.get_yaxis_transform(),
    ha="right", va="center",
    fontsize=9,
    color="gray"
)

ax.text(
    std_line, -0.08,
    f"标准差均值 = {std_line:.2f}",
    transform=ax.get_xaxis_transform(),
    ha="center", va="top",
    fontsize=9,
    color="gray"
)

# ===== 四象限说明 =====
box = dict(boxstyle="round", fc="white", alpha=0.65, zorder=1)

ax.text(0.02, 0.98, "高分 · 稳定\n（公认佳作）",
        transform=ax.transAxes, ha="left", va="top", fontsize=10, bbox=box)
ax.text(0.98, 0.98, "高分 · 分歧\n（争议神作）",
        transform=ax.transAxes, ha="right", va="top", fontsize=10, bbox=box)
ax.text(0.02, 0.02, "低分 · 稳定\n（普遍一般）",
        transform=ax.transAxes, ha="left", va="bottom", fontsize=10, bbox=box)
ax.text(0.98, 0.02, "低分 · 分歧\n（毁誉参半）",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=10, bbox=box)

# ===== 悬停显示（自动适配）=====
cursor = mplcursors.cursor(sc, hover=True)

@cursor.connect("add")
def on_add(sel):
    i = sel.index
    text = (
        f"{names[i]}\n"
        f"平均分: {means[i]:.2f}\n"
        f"标准差: {stds[i]:.2f}"
    )
    if has_type:
        t = "动画" if str(types[i]) == "2" else "游戏"
        text = f"{names[i]}\n类型: {t}\n平均分: {means[i]:.2f}\n标准差: {stds[i]:.2f}"

    sel.annotation.set_text(text)
    sel.annotation.get_bbox_patch().set(alpha=0.9)

plt.tight_layout()
plt.show()
