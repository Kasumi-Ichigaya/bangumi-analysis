window.addEventListener('load', () => {
    const btn = document.getElementById("toggleBtn");
    let current = "anime";
    let selectedIdx = { "canvas-anime": null, "canvas-game": null };

    const COLORS = { DEFAULT: "#4f7cff", HOVER: "#ff4757", SELECT: "#4f7cff" };
    const SIZES = { DEFAULT: 9, HOVER: 16, SELECT: 9 };

    // 1. 切换逻辑
    btn.addEventListener("click", () => {
        const anime = document.getElementById("container-anime");
        const game = document.getElementById("container-game");
        const isAnime = current === "anime";
        anime.classList.toggle("active", !isAnime);
        game.classList.toggle("active", isAnime);
        btn.innerText = isAnime ? "切换到动画" : "切换到游戏";
        current = isAnime ? "game" : "anime";
        Plotly.Plots.resize(document.getElementById(isAnime ? "canvas-game" : "canvas-anime"));
    });

    // 2. 绑定交互
    function bind(gdId, containerId) {
        const gd = document.getElementById(gdId);
        const container = document.getElementById(containerId);
        if (!gd || !gd.on) { setTimeout(() => bind(gdId, containerId), 100); return; }

        gd.on("plotly_hover", (data) => {
            container.classList.add("is-hovering");
            const pn = data.points[0].pointNumber;
            const tn = data.points[0].curveNumber;

            // 直接操作内存数组
            gd.data[tn].marker.size[pn] = SIZES.HOVER;
            gd.data[tn].marker.color[pn] = COLORS.HOVER;
            
            Plotly.restyle(gd, {
                'marker.size': [gd.data[tn].marker.size],
                'marker.color': [gd.data[tn].marker.color]
            }, [tn]);
        });

        gd.on("plotly_unhover", (data) => {
            container.classList.remove("is-hovering");
            const pn = data.points[0].pointNumber;
            const tn = data.points[0].curveNumber;

            // 还原逻辑：如果是选中的，保持选中色，否则恢复默认
            const isSel = (selectedIdx[gdId] === pn);
            gd.data[tn].marker.size[pn] = isSel ? SIZES.SELECT : SIZES.DEFAULT;
            gd.data[tn].marker.color[pn] = isSel ? COLORS.SELECT : COLORS.DEFAULT;

            Plotly.restyle(gd, {
                'marker.size': [gd.data[tn].marker.size],
                'marker.color': [gd.data[tn].marker.color]
            }, [tn]);
        });

        gd.on("plotly_click", (data) => {
            const pn = data.points[0].pointNumber;
            const tn = data.points[0].curveNumber;
            
            // 还原之前的选中点
            if (selectedIdx[gdId] !== null) {
                gd.data[tn].marker.size[selectedIdx[gdId]] = SIZES.DEFAULT;
                gd.data[tn].marker.color[selectedIdx[gdId]] = COLORS.DEFAULT;
            }

            // 设置新选中点
            selectedIdx[gdId] = pn;
            gd.data[tn].marker.size[pn] = SIZES.SELECT;
            gd.data[tn].marker.color[pn] = COLORS.SELECT;

            Plotly.restyle(gd, {
                'marker.size': [gd.data[tn].marker.size],
                'marker.color': [gd.data[tn].marker.color]
            }, [tn]);

            if (data.points[0].customdata) window.open(data.points[0].customdata, "_blank");
        });
    }

    bind("canvas-anime", "container-anime");
    bind("canvas-game", "container-game");
});
