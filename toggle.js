window.addEventListener("load", () => {

    // ===== 1. 收集元素 =====
    const plots = document.querySelectorAll(".plot");
    const buttons = document.querySelectorAll(".side button");

    const selectedIdx = {};

    const COLORS = {
        DEFAULT: "#4f7cff",
        HOVER: "#ff4757",
        SELECT: "#4f7cff"
    };

    const SIZES = {
        DEFAULT: 9,
        HOVER: 16,
        SELECT: 9
    };

    // ===== 2. 按钮切换逻辑（N 分类）=====
    buttons.forEach(btn => {
        btn.addEventListener("click", () => {
            const target = btn.dataset.target;   // ✅ 关键：来源在这

            // 按钮选中态
            buttons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            // 图表切换动画
            plots.forEach(p => {
                if (p.classList.contains("active")) {
                    p.classList.add("prev-out");
                    p.classList.remove("active");
                }
            });

            const next = document.getElementById("container-" + target);
            if (!next) return;

            next.classList.remove("prev-out");
            next.classList.add("next-in", "active");

            setTimeout(() => {
                next.classList.remove("next-in");
            }, 800);

            // resize Plotly（防止显示异常）
            const canvas = next.querySelector(".js-plotly-plot");
            if (canvas) Plotly.Plots.resize(canvas);
        });
    });

    // ===== 3. Plotly 交互绑定 =====
    function bind(gdId, containerId) {
        const gd = document.getElementById(gdId);
        const container = document.getElementById(containerId);

        if (!gd || !gd.on) {
            setTimeout(() => bind(gdId, containerId), 100);
            return;
        }

        selectedIdx[gdId] = null;

        gd.on("plotly_hover", (data) => {
            container.classList.add("is-hovering");
            const { pointNumber: pn, curveNumber: tn } = data.points[0];

            gd.data[tn].marker.size[pn] = SIZES.HOVER;
            gd.data[tn].marker.color[pn] = COLORS.HOVER;

            Plotly.restyle(gd, {
                "marker.size": [gd.data[tn].marker.size],
                "marker.color": [gd.data[tn].marker.color]
            }, [tn]);
        });

        gd.on("plotly_unhover", (data) => {
            container.classList.remove("is-hovering");
            const { pointNumber: pn, curveNumber: tn } = data.points[0];

            const isSel = selectedIdx[gdId] === pn;
            gd.data[tn].marker.size[pn] = isSel ? SIZES.SELECT : SIZES.DEFAULT;
            gd.data[tn].marker.color[pn] = isSel ? COLORS.SELECT : COLORS.DEFAULT;

            Plotly.restyle(gd, {
                "marker.size": [gd.data[tn].marker.size],
                "marker.color": [gd.data[tn].marker.color]
            }, [tn]);
        });

        gd.on("plotly_click", (data) => {
            const { pointNumber: pn, curveNumber: tn, customdata } = data.points[0];

            if (selectedIdx[gdId] !== null) {
                const prev = selectedIdx[gdId];
                gd.data[tn].marker.size[prev] = SIZES.DEFAULT;
                gd.data[tn].marker.color[prev] = COLORS.DEFAULT;
            }

            selectedIdx[gdId] = pn;
            gd.data[tn].marker.size[pn] = SIZES.SELECT;
            gd.data[tn].marker.color[pn] = COLORS.SELECT;

            Plotly.restyle(gd, {
                "marker.size": [gd.data[tn].marker.size],
                "marker.color": [gd.data[tn].marker.color]
            }, [tn]);

            if (customdata && customdata[0]) window.open(customdata[0], "_blank");
        });
    }

    // ===== 4. 自动绑定所有 Plotly =====
    plots.forEach(plot => {
        const canvas = plot.querySelector(".js-plotly-plot");
        if (canvas) {
            bind(canvas.id, plot.id);
        }
    });

});

