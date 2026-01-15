# Bangumi 收藏评分可视化

本项目用于抓取指定 Bangumi 用户的收藏（书籍、动画、音乐、游戏）评分数据，并生成交互式 HTML 可视化图表，展示每个作品的平均评分与分歧程度（标准差）。

---

## 功能特点
- 自动抓取用户收藏列表
- 多线程并发获取每个作品评分数据，加快抓取速度
- 计算每部作品的平均分和评分标准差
- 按类型（书籍 / 动画 / 音乐 / 游戏）生成交互式图表
- 导出 CSV 文件以便后续分析
- 生成可切换类型的 HTML 页面，点击按钮切换显示
- 可生成静态图片以便展示（通过 `bgm_see.py`）

---

## 配置方法

1. **运行脚本并填写参数**  

运行 `bangumi_auto.py` 并填写以下参数：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| USER_ID | 你的 Bangumi 用户 ID（不是用户名） | 必填 |
| ACCESS_TOKEN | Bangumi API 访问令牌，可在 [开发者平台](https://next.bgm.tv/demo/access-token) 自动生成 | 必填 |
| OUTPUT_CSV / OUTPUT_HTML | 输出文件名，可按需修改 | CSV: bangumi_888347.csv / HTML: index.html |
| REQUEST_DELAY | 请求间隔（秒），可调节抓取速度 | 0.3 |
| MAX_WORKERS | 线程数，增加可加快抓取，但过高可能被 API 限流 | 6 |

2. **注意事项**
- 建议将 `MAX_WORKERS` 设置为 4~6  
- `REQUEST_DELAY` 可调整抓取速度  
- 大量收藏可能需要几分钟  
- ACCESS_TOKEN 过期需重新生成

3. **生成图片（可选）**  
运行 `bgm_see.py`，会读取 CSV 文件生成静态图片。

---

## template.html 说明

`template.html` 是生成交互式 HTML 图表的模板，Python 脚本会把 Plotly 图表和类型切换按钮插入模板生成最终 `index.html`。

### 文件结构示意

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Bangumi 收藏评分分布</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <!-- 图表区域 -->
    <div class="chart-area">
        <div class="chart">
            <!-- PLOT_DIVS_PLACEHOLDER -->
        </div>
    </div>

    <!-- 按钮区域 -->
    <div class="side">
        <!-- BUTTONS_PLACEHOLDER -->
    </div>

    <!-- 控制按钮切换图表的 JS -->
    <script src="toggle.js"></script>
</body>
</html>
```
### 页面布局
- `.chart-area`：展示图表区域  
- `.side`：按钮区域，放置类型切换按钮  
- 页面布局可通过 `style.css` 自定义样式，例如宽度、高度、按钮样式、字体等。

### 脚本与交互
#### style.css
- 图表容器 `.chart` 带阴影、圆角和固定宽高
- 图表切换 `.plot` 的过渡动画（透明度、位移、缩放、模糊）
- 按钮 `.side button` 样式和 hover/active 高亮动画
- 响应式布局适配小屏设备

#### toggle.js
- **按钮切换**
  - 点击按钮切换显示对应类型的图表
  - 动画：当前图表向左滑出，下一图表从右滑入
  - 自动 resize Plotly 图表，防止显示异常
- **Hover（悬停）交互**
  - 鼠标悬停点时放大 marker 并变色
  - 鼠标移出恢复默认或选中状态
- **Click（点击）交互**
  - 单点选中，改变 marker 样式
  - 点击打开对应 Bangumi 页面（如 `customdata[0]` 存在）
- 自动绑定页面所有 Plotly 图表
- 支持多图表、多按钮的切换与交互
---

### 使用方法
1. 将 `template.html` 放在项目目录  
2. 确保 `style.css` 和 `toggle.js` 路径正确  
3. 运行 `bangumi_auto.py` 抓取数据  
4. 脚本生成 `index.html`，将图表和按钮插入模板  
5. 打开 `index.html` 交互查看各类型作品评分分布

💡 **提示**：
- 您可以自定义 CSS 样式，使图表和按钮更美观

---

## HTML 图表说明与分析

生成的 `index.html` 图表展示用户收藏作品的评分分布，每个点代表一部作品，鼠标悬停可查看作品名称、平均分、标准差和投票人数。

- 横轴：评分标准差（分歧程度）  
- 纵轴：平均评分（整体评价）  

### 可分析信息
![动画评分分布](examples.PNG "动画评分分布")

1. **作品整体评分水平**  
   - 点在纵轴靠上：平均评分高  
   - 点在纵轴靠下：平均评分低

2. **作品评价一致性（分歧程度）**  
   - 点在横轴靠左（标准差小）：评分集中  
   - 点在横轴靠右（标准差大）：评分分歧明显

3. **受欢迎程度**  
   - 鼠标悬停查看 `votes`（投票人数）  
   - 高票数且评分高 → 公认佳作  
   - 高票数但标准差大 → 讨论热度高，但评价分歧明显

4. **类型对比**  
   - 图表按钮切换类型（动画 / 游戏 / 书籍 / 音乐）  
   - 可直观比较不同类型作品的平均分和分歧程度

💡 **提示**：点击按钮切换类型，鼠标悬停查看详细信息

---

## 依赖
- Python 3.9 及以上版本  
- 第三方库：
  - Requests：访问 Bangumi API  
  - Pandas：数据处理  
  - Plotly：绘制交互式散点图  
  - concurrent.futures：多线程加速抓取


# 更新说明
- 260110更新： 优化CSS，点击散点图可以看到bangumi详细页面。
- 260111更新： 增加鼠标悬浮高亮显示，以及鼠标悬浮手势。
- 260112更新： 重写按钮，重新python和js，支持动画，游戏，书籍，音乐四种散点图，不像是之前版本把元素写死的方法，如果要扩充电视剧也是很方便就能扩充。悬浮窗可以看到投票总人数。
- 260113更新： 散点图标题显示用户昵称，导出python内的模板html作为template.html。
