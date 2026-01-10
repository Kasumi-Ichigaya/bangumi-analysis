let current = "anime";

function toggleChart() {
    const plotAnime = document.getElementById("plot-anime");
    const plotGame  = document.getElementById("plot-game");
    const btn = document.getElementById("toggleBtn");

    if (current === "anime") {
        plotAnime.classList.remove("active");
        plotGame.classList.add("active");
        btn.innerText = "切换到动画";
        current = "game";

        setTimeout(() => {
            Plotly.Plots.resize(
                plotGame.querySelector(".plotly-graph-div")
            );
        }, 50);

    } else {
        plotGame.classList.remove("active");
        plotAnime.classList.add("active");
        btn.innerText = "切换到游戏";
        current = "anime";

        setTimeout(() => {
            Plotly.Plots.resize(
                plotAnime.querySelector(".plotly-graph-div")
            );
        }, 50);
    }
}
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
