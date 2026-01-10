let current = "anime";

function toggleChart() {
    const plotAnime = document.getElementById("plot-anime");
    const plotGame  = document.getElementById("plot-game");
    const btn = document.getElementById("toggleBtn");
    toggleBtn.addEventListener("click", () => {
    if (current === "anime") {
        // 切换到游戏
        animePlot.classList.remove("active");
        gamePlot.classList.add("active");
        toggleBtn.innerText = "切换到动画";
        current = "game";

        // 强制 Plotly 重新计算尺寸
        setTimeout(() => {
            const gd = gamePlot.querySelector(".plotly-graph-div");
            if (gd) Plotly.Plots.resize(gd);
        }, 50);

    } else {
        // 切换到动画
        gamePlot.classList.remove("active");
        animePlot.classList.add("active");
        toggleBtn.innerText = "切换到游戏";
        current = "anime";

        setTimeout(() => {
            const gd = animePlot.querySelector(".plotly-graph-div");
            if (gd) Plotly.Plots.resize(gd);
        }, 50);
    }
});
function bindClick(plotContainerId) {
    const container = document.getElementById(plotContainerId);
    if (!container) return;

    const graphDiv = container.querySelector(".plotly-graph-div");
    if (!graphDiv) return;

    graphDiv.on("plotly_click", function (data) {
        const url = data.points[0].customdata[0];
        if (url) {
            window.open(url, "_blank");
        }
    });

    // 👇 UX：鼠标提示这是可点的
    graphDiv.style.cursor = "pointer";
}

window.addEventListener("load", () => {
    bindClick("plot-anime");
    bindClick("plot-game");
});

