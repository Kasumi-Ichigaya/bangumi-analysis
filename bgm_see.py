import csv
import matplotlib.pyplot as plt
import mplcursors
import numpy as np


# ===== 中文字体修复 =====
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False
# =======================

CSV_FILE = r"bangumi_url\bangumi_result_game&anime.csv"

means = []
stds = []
names = []

with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        means.append(float(row["mean"]))
        stds.append(float(row["std"]))
        names.append(row["name"])

means = np.array(means)
stds = np.array(stds)

mean_line = means.mean()
std_line = stds.mean()

# ===== 只创建一次图 =====
fig, ax = plt.subplots(figsize=(9, 7))

# 数据点
sc = ax.scatter(stds, means, alpha=0.75, zorder=5)

# 分界线
ax.axhline(mean_line, linestyle="--", linewidth=1, zorder=2)
ax.axvline(std_line, linestyle="--", linewidth=1, zorder=2)

# 坐标 & 标题
ax.set_xlabel("标准差（分歧程度）")
ax.set_ylabel("平均分（整体评价）")
ax.set_title("Bangumi 动画评分分布（含分界线）")
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


# ===== 四象限说明=====
box = dict(boxstyle="round", fc="white", alpha=0.65, zorder=1)

ax.text(0.02, 0.98, "高分 · 稳定\n（公认佳作）",transform=ax.transAxes, ha="left", va="top",fontsize=10, bbox=box)
ax.text(0.98, 0.98, "高分 · 分歧\n（争议神作）",transform=ax.transAxes, ha="right", va="top",fontsize=10, bbox=box)
ax.text(0.02, 0.02, "低分 · 稳定\n（普遍一般）",transform=ax.transAxes, ha="left", va="bottom",fontsize=10, bbox=box)
ax.text(0.98, 0.02, "低分 · 分歧\n（毁誉参半）",transform=ax.transAxes, ha="right", va="bottom",fontsize=10, bbox=box)

# ===== 悬停显示 =====
cursor = mplcursors.cursor(sc, hover=True)

@cursor.connect("add")
def on_add(sel):
    i = sel.index
    sel.annotation.set_text(
        f"{names[i]}\n平均分: {means[i]:.2f}\n标准差: {stds[i]:.2f}"
    )
    sel.annotation.get_bbox_patch().set(alpha=0.9)

plt.tight_layout()
plt.show()
