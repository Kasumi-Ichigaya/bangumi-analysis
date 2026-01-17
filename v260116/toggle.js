window.addEventListener("load",()=>{
// ===== 1️⃣ 收集必要 DOM 元素 =====
const plots=document.querySelectorAll(".plot"),
      buttons=document.querySelectorAll(".side button[data-target]"),
      meanBtn=document.getElementById("toggle-mean-line");

// ===== 全局状态与样式配置 =====
const selectedIdx={},COLORS={DEFAULT:"#4f7cff",HOVER:"#ff4757",SELECT:"#4f7cff"},SIZES={DEFAULT:9,HOVER:16,SELECT:9};
let meanLineVisible=false; // ⭐ 平均线显示状态，全局唯一

// ===== 2️⃣ 分类切换（按钮切换图表，不动平均线逻辑） =====
buttons.forEach(btn=>btn.addEventListener("click",()=>{
    const target=btn.dataset.target;
    buttons.forEach(b=>b.classList.remove("active")),btn.classList.add("active");
    plots.forEach(p=>p.classList.contains("active")&&(p.classList.add("prev-out"),p.classList.remove("active")));
    const next=document.getElementById("container-"+target);if(!next)return;
    next.classList.remove("prev-out"),next.classList.add("next-in","active");
    const gd=next.querySelector(".js-plotly-plot");
    // ⭐ 同步当前平均线状态
    gd&&gd.layout?.shapes&&Plotly.relayout(gd,{shapes:gd.layout.shapes.map(s=>s.name&&s.name.startsWith("mean-")?{...s,visible:meanLineVisible}:s)});
    setTimeout(()=>next.classList.remove("next-in"),800);
    gd&&Plotly.Plots.resize(gd);
}));

// ===== 3️⃣ 平均线按钮（全局只绑定一次） =====
if(meanBtn)meanBtn.addEventListener("click",()=>{
    meanLineVisible=!meanLineVisible;
    meanBtn.classList.toggle("active",meanLineVisible);
    plots.forEach(plot=>{
        const gd=plot.querySelector(".js-plotly-plot");if(!gd)return;
        Plotly.relayout(gd,{
            shapes:(gd.layout.shapes||[]).map(s=>s.name&&s.name.startsWith("mean-")?{...s,visible:meanLineVisible}:s),
            annotations:(gd.layout.annotations||[]).map(a=>a.name&&a.name.startsWith("mean-")?{...a,visible:meanLineVisible}:a)
        });
    });
});

// ===== 4️⃣ 绑定 Plotly hover/click 事件 =====
function bind(gdId,containerId){
    const gd=document.getElementById(gdId),container=document.getElementById(containerId);
    if(!gd||!gd.on)return setTimeout(()=>bind(gdId,containerId),100);
    selectedIdx[gdId]=null;

    // hover 放大 + 变色
    gd.on("plotly_hover",data=>{
        container.classList.add("is-hovering");
        const {pointNumber:pn,curveNumber:tn}=data.points[0];
        gd.data[tn].marker.size[pn]=SIZES.HOVER;
        gd.data[tn].marker.color[pn]=COLORS.HOVER;
        Plotly.restyle(gd,{"marker.size":[gd.data[tn].marker.size],"marker.color":[gd.data[tn].marker.color]},[tn]);
    });

    // unhover 恢复原样
    gd.on("plotly_unhover",data=>{
        container.classList.remove("is-hovering");
        const {pointNumber:pn,curveNumber:tn}=data.points[0];
        const isSel=selectedIdx[gdId]===pn;
        gd.data[tn].marker.size[pn]=isSel?SIZES.SELECT:SIZES.DEFAULT;
        gd.data[tn].marker.color[pn]=isSel?COLORS.SELECT:COLORS.DEFAULT;
        Plotly.restyle(gd,{"marker.size":[gd.data[tn].marker.size],"marker.color":[gd.data[tn].marker.color]},[tn]);
    });

    // click 选中 + 打开链接
    gd.on("plotly_click",data=>{
        const {pointNumber:pn,curveNumber:tn,customdata}=data.points[0];
        if(selectedIdx[gdId]!==null){
            const prev=selectedIdx[gdId];
            gd.data[tn].marker.size[prev]=SIZES.DEFAULT;
            gd.data[tn].marker.color[prev]=COLORS.DEFAULT;
        }
        selectedIdx[gdId]=pn;
        gd.data[tn].marker.size[pn]=SIZES.SELECT;
        gd.data[tn].marker.color[pn]=COLORS.SELECT;
        Plotly.restyle(gd,{"marker.size":[gd.data[tn].marker.size],"marker.color":[gd.data[tn].marker.color]},[tn]);
        customdata&&customdata[0]&&window.open(customdata[0],"_blank");
    });
}

// 自动绑定所有 plot
plots.forEach(plot=>{const canvas=plot.querySelector(".js-plotly-plot");canvas&&bind(canvas.id,plot.id);});

// ===== 5️⃣ 页面首次载入同步平均线 =====
function syncMeanLineToAllPlots(){
    plots.forEach(plot=>{
        const gd=plot.querySelector(".js-plotly-plot");if(!gd||!gd.layout)return;
        Plotly.relayout(gd,{
            shapes:(gd.layout.shapes||[]).map(s=>s.name&&s.name.startsWith("mean-")?{...s,visible:meanLineVisible}:s),
            annotations:(gd.layout.annotations||[]).map(a=>a.name&&a.name.startsWith("mean-")?{...a,visible:meanLineVisible}:a)
        });
    });
    meanBtn?.classList.toggle("active",meanLineVisible);
}
syncMeanLineToAllPlots();

// ===== 6️⃣ 初次载入同步按钮状态 =====
(function initActiveButtonFromPlot(){
    const activePlot=document.querySelector(".plot.active");if(!activePlot)return;
    const target=activePlot.id.replace("container-","");
    buttons.forEach(btn=>btn.classList.toggle("active",btn.dataset.target===target));
})();
});
