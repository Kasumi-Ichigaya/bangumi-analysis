window.addEventListener("load", () => {

    /* ===== 基础元素 ===== */
    const plots = document.querySelectorAll(".plot"),
          buttons = document.querySelectorAll(".menu-items button[data-target]"), 
          meanBtn = document.getElementById("toggle-mean-line"),
          toggleXBtn = document.getElementById("toggle-x-rank");
    let meanLineVisible = false;

    /* ===== 分类切换 ===== */
    buttons.forEach(btn => btn.addEventListener("click", () => {
        const target = btn.dataset.target;
        buttons.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");

        plots.forEach(p => p.classList.replace("active", "prev-out"));
        const next = document.getElementById("container-" + target);
        if (!next) return;

        next.classList.remove("prev-out");
        next.classList.add("next-in", "active");

        const gd = next.querySelector(".js-plotly-plot");
        if (gd && !gd._bound) {
    bind(gd.id, next.id);
    gd._bound = true;
}

        if (gd?.layout)
            Plotly.relayout(gd, {
                shapes: (gd.layout.shapes || []).map(s => s.name?.startsWith("mean-") ? { ...s, visible: meanLineVisible } : s),
                annotations: (gd.layout.annotations || []).map(a => a.name?.startsWith("mean-") ? { ...a, visible: meanLineVisible } : a)
            });

        setTimeout(() => next.classList.remove("next-in"), 800);
        gd && Plotly.Plots.resize(gd);
    }));

    /* ===== 平均线开关 ===== */
    meanBtn?.addEventListener("click", () => {
        meanLineVisible = !meanLineVisible;
        meanBtn.classList.toggle("active", meanLineVisible);

        plots.forEach(p => {
            const gd = p.querySelector(".js-plotly-plot");
            if (!gd?.layout) return;
            Plotly.relayout(gd, {
                shapes: (gd.layout.shapes || []).map(s => s.name?.startsWith("mean-") ? { ...s, visible: meanLineVisible } : s),
                annotations: (gd.layout.annotations || []).map(a => a.name?.startsWith("mean-") ? { ...a, visible: meanLineVisible } : a)
            });
        });
    });

    /* ===== Hover / Click ===== */
    function bind(gdId, cid) {
        const gd = document.getElementById(gdId), c = document.getElementById(cid);
        if (!gd?.on) return setTimeout(() => bind(gdId, cid), 100);
        const dot = c.querySelector(".hover-dot"); if (!dot) return;

        gd.on("plotly_hover", e => {
            const p = e.points[0], l = gd._fullLayout;
            dot.style.left = (l.xaxis.l2p(p.x) + l.xaxis._offset) + "px";
            dot.style.top  = (l.yaxis.l2p(p.y) + l.yaxis._offset) + "px";
            dot.style.display = "block"; c.classList.add("is-hovering");
        });

        gd.on("plotly_unhover", () => {
            dot.style.display = "none"; c.classList.remove("is-hovering");
        });

        gd.on("plotly_click", e => {
            const url = e.points[0].customdata?.[0];
            url && window.open(url, "_blank");
        }); 
    }

    /* ===== 初始化备份 ===== */
plots.forEach(p => {
  const gd = p.querySelector(".js-plotly-plot"); if (!gd) return;
  const saveRange = () =>
    !gd._stdRange && gd.layout?.xaxis?.range
      ? (gd._stdRange = gd.layout.xaxis.range.slice())
      : setTimeout(saveRange, 50);
  saveRange();
});

    /* ===== 排名 / 标准差切换 ===== */
    const syncButtonState = () => {
        const p = document.querySelector(".plot.active .js-plotly-plot");
        const isRank = p?.layout?.xaxis?.title?.text?.includes("榜单排名");
        toggleXBtn?.classList.toggle("active", !!isRank);
        if (toggleXBtn) toggleXBtn.innerText = isRank ? "按标准差显示" : "按排名显示";
    };

    toggleXBtn?.addEventListener("click", () => {
        const plot = document.querySelector(".plot.active .js-plotly-plot");
        if (!plot) return;
        const toRank = plot.layout.xaxis.title.text.includes("标准差");
        let meanX = 0;

        const data = plot.data.map((t, i) => {
            if (!t || t.name === "_hover") return t;
            if (!t._xBackup) {
                const src = plot._fullData?.[i] || t;
                t._xBackup = [...(src.x || [])];
                t._yBackup = [...(src.y || [])];
                t._customBackup = [...(src.customdata || [])];
            }
            const trace = { ...t, x: [], y: [], customdata: [...t._customBackup], marker: { ...(t.marker || {}) } };
            if (t.name === "有榜单排名") {
                const opacity = [];
                t._customBackup.forEach((d, idx) => {
                    const rank = Number(d?.[2]);
                    toRank
                        ? (trace.x.push(rank > 0 ? rank : t._xBackup[idx]), trace.y.push(t._yBackup[idx]), opacity.push(rank > 0 ? 1 : 0))
                        : (trace.x.push(t._xBackup[idx]), trace.y.push(t._yBackup[idx]), opacity.push(1));
                });
                trace.marker.opacity = opacity;
                const valid = trace.x.filter((_, i) => opacity[i]);
                if (valid.length) meanX = valid.reduce((a, b) => a + b, 0) / valid.length;
                return trace;
            }
            trace.x = [...t._xBackup];
            trace.y = [...t._yBackup];
            trace.marker.opacity = 1;
            return trace;
        });

        const layout = {
            ...plot.layout,
            xaxis: {
                ...plot.layout.xaxis,
                title: { text: toRank ? "榜单排名" : "标准差 (分歧程度)" },
                autorange: toRank,
                range: toRank ? undefined : plot._stdRange
            },
            uirevision: toRank ? "rank" : "std"
  };

        if (meanX > 0) {
            layout.annotations = (layout.annotations || []).map(a => a.name === "mean-annotation-x"
                ? { ...a, x: meanX, text: toRank ? `平均排名：${meanX.toFixed(0)}` : `标准差均值：${meanX.toFixed(2)}` }
                : a);
            layout.shapes = (layout.shapes || []).map(s => s.type === "line" && s.xref === "x" ? { ...s, x0: meanX, x1: meanX } : s);
        }

        Plotly.react(plot, data, layout);
        syncButtonState();
});

    /* ===== 状态监听 ===== */
    new MutationObserver(() => setTimeout(syncButtonState, 50))
        .observe(document.querySelector(".main-content") || document.body, { subtree: true, attributes: true, attributeFilter: ["class"] });
    setTimeout(syncButtonState, 100);

    /* ===== 初始默认选中 anime ===== */
    (function initDefaultAnime() {
        const target = "anime";
        const btn = document.querySelector(`.menu-items button[data-target="${target}"]`);
        const plot = document.getElementById(`container-${target}`);
        if (!btn || !plot) return;
        buttons.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        plots.forEach(p => p.classList.remove("active", "next-in", "prev-out"));
        plot.classList.add("active");
       const gd = plot.querySelector(".js-plotly-plot");
        if (gd) {
        Plotly.Plots.resize(gd);
        if (!gd._bound) {
            bind(gd.id, plot.id);
            gd._bound = true;
        }
    }
        setTimeout(syncButtonState, 0);
    })();
});
