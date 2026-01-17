window.addEventListener("load",()=>{
// ===== 1️⃣ 收集 DOM 元素 =====
const plots=document.querySelectorAll(".plot"),buttons=document.querySelectorAll(".side button[data-target]"),meanBtn=document.getElementById("toggle-mean-line");
let meanLineVisible=false;

// ===== 2️⃣ 分类切换按钮 =====
buttons.forEach(btn=>btn.addEventListener("click",()=>{
    const target=btn.dataset.target;
    buttons.forEach(b=>b.classList.remove("active")),btn.classList.add("active");
    plots.forEach(p=>p.classList.contains("active")&&(p.classList.add("prev-out"),p.classList.remove("active")));
    const next=document.getElementById("container-"+target);if(!next)return;
    next.classList.remove("prev-out"),next.classList.add("next-in","active");
    const gd=next.querySelector(".js-plotly-plot");
    gd?.layout?.shapes&&Plotly.relayout(gd,{shapes:gd.layout.shapes.map(s=>s.name?.startsWith("mean-")?{...s,visible:meanLineVisible}:s)});
    setTimeout(()=>next.classList.remove("next-in"),800);gd&&Plotly.Plots.resize(gd);
}));

// ===== 3️⃣ 平均线按钮 =====
meanBtn?.addEventListener("click",()=>{
    meanLineVisible=!meanLineVisible;
    meanBtn.classList.toggle("active",meanLineVisible);
    plots.forEach(plot=>{
        const gd=plot.querySelector(".js-plotly-plot");if(!gd)return;
        Plotly.relayout(gd,{
            shapes:(gd.layout.shapes||[]).map(s=>s.name?.startsWith("mean-")?{...s,visible:meanLineVisible}:s),
            annotations:(gd.layout.annotations||[]).map(a=>a.name?.startsWith("mean-")?{...a,visible:meanLineVisible}:a)
        });
    });
});

// ===== 4️⃣ 绑定 Plotly hover/click（_hover trace） =====
function bind(gdId,containerId){
    const gd=document.getElementById(gdId),container=document.getElementById(containerId);
    if(!gd||!gd.on)return setTimeout(()=>bind(gdId,containerId),100);
    const H=gd.data.length-1;let sel=null;

    gd.on("plotly_hover",e=>{
        container.classList.add("is-hovering");
        const p=e.points[0];
        Plotly.restyle(gd,{x:[[p.x]],y:[[p.y]],"marker.line.color":["rgba(0,0,0,0.9)"]},[H]);
    });
    gd.on("plotly_unhover",()=>{
        container.classList.remove("is-hovering");
        if(!sel)Plotly.restyle(gd,{x:[[]],y:[[]]},[H]);
    });
    gd.on("plotly_click",e=>{
        const p=e.points[0];sel={x:p.x,y:p.y};
        Plotly.restyle(gd,{x:[[p.x]],y:[[p.y]],"marker.line.color":["rgba(0,0,0,1)"]},[H]);
        p.customdata?.[0]&&window.open(p.customdata[0],"_blank");
    });
}

// ===== 5️⃣ 页面首次载入同步平均线 =====
function syncMeanLine(){
    plots.forEach(plot=>{
        const gd=plot.querySelector(".js-plotly-plot");if(!gd||!gd.layout)return;
        Plotly.relayout(gd,{
            shapes:(gd.layout.shapes||[]).map(s=>s.name?.startsWith("mean-")?{...s,visible:meanLineVisible}:s),
            annotations:(gd.layout.annotations||[]).map(a=>a.name?.startsWith("mean-")?{...a,visible:meanLineVisible}:a)
        });
    });
    meanBtn?.classList.toggle("active",meanLineVisible);
}
syncMeanLine();

// ===== 6️⃣ 初次同步按钮状态 =====
(function(){
    const active=document.querySelector(".plot.active");if(!active)return;
    const target=active.id.replace("container-","");
    buttons.forEach(btn=>btn.classList.toggle("active",btn.dataset.target===target));
})();

// ===== 7️⃣ 自动绑定所有 Plotly 图表 =====
plots.forEach(plot=>{
    const gd=plot.querySelector(".js-plotly-plot");
    gd?.id&&bind(gd.id,plot.id);
});
});
