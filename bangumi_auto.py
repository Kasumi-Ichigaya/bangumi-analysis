import os,math,time,requests,pandas as pd
import plotly.express as px,plotly.io as pio
from concurrent.futures import ThreadPoolExecutor,as_completed

USER_ID = 888347
API_BASE = "https://api.bgm.tv"
OUTPUT_CSV = "bangumi_888347.csv"
OUTPUT_HTML = "index.html"
ACCESS_TOKEN = os.getenv("BGM_TOKEN")

HEADERS = {
    "User-Agent": "12819/bgm-collection-fetcher (private-script)",
    "Accept": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

TYPE_INFO={
    "Book":{"cn":"书籍"},
    "Anime":{"cn":"动画"},
    "Music":{"cn":"音乐"},
    "Game":{"cn":"游戏"},
    "Real":{"cn":"三次元"},
}

REQUEST_DELAY=0.3
MAX_WORKERS=6

session=requests.Session()
session.headers.update(HEADERS)

# ================= API =================

def get_username(uid):
    r=session.get(f"{API_BASE}/v0/users/{uid}",timeout=10)
    r.raise_for_status()
    d=r.json()
    return d.get("nickname") or d.get("username")

USERNAME=get_username(USER_ID)

def calc_mean_std(cnt):
    n=sum(cnt.values())
    if not n:return None,None
    m=sum(int(k)*v for k,v in cnt.items())/n
    return m,math.sqrt(sum(v*(int(k)-m)**2 for k,v in cnt.items())/n)

def get_collections(uid):
    res,off=[],0
    while True:
        r=session.get(
            f"{API_BASE}/v0/users/{uid}/collections",
            params={"limit":50,"offset":off,"type":2},
            timeout=10
        )
        if r.status_code==400:break
        r.raise_for_status()
        d=r.json().get("data")
        if not d:break
        res+=d;off+=50;time.sleep(REQUEST_DELAY)
    return res

def fetch_subject(sid,stype):
    try:
        r=session.get(f"{API_BASE}/v0/subjects/{sid}",timeout=10)
        r.raise_for_status()
        d=r.json()

        cnt=d.get("rating",{}).get("count",{})
        mean,std=calc_mean_std(cnt)
        votes = sum(cnt.values())
        if votes <=1: return None#排除掉只有一个点的情况
        if mean is None:return None

        return {
            "name":d.get("name_cn") or d.get("name"),
            "mean":round(mean,3),
            "std":round(std,3),
            "type":{1:"Book",2:"Anime",3:"Music",4:"Game",6:"Real"}[stype],
            "votes":sum(cnt.values()),
            "url":f"https://bangumi.tv/subject/{sid}"
        }
    except Exception:
        return

# ================= PLOT =================

def make_toggle_html(df_map):

    def pad(s):
        return [s.min()-(s.max()-s.min())*.05,
                s.max()+(s.max()-s.min())*.05]

    df_std=pd.concat([df_map["Anime"],df_map["Game"]],ignore_index=True)
    df_alt=pd.concat([df_map["Book"],df_map["Music"]],ignore_index=True)
    df_all=pd.concat(df_map.values(),ignore_index=True)

    X_STD,X_ALT=pad(df_std["std"]),pad(df_alt["std"])
    Y_RANGE=pad(df_all["mean"])
    # --- 调试代码开始 ---
    print(f"【调试】df_all 里的实际最大值: {df_all['mean'].max()}")
    print(f"【调试】df_all 里的实际最小值: {df_all['mean'].min()}")
    print(f"【调试】计算出的 Y_RANGE: {Y_RANGE}")

    # 检查一下 df_map 里到底有哪些 key，防止有隐藏的数据集
    print(f"【调试】df_map 包含的分类: {df_map.keys()}")
    # --- 调试代码结束 ---
    def fig(df, title, xr):
        fig = px.scatter(df, x="std", y="mean", hover_name="name", render_mode="svg",
                        labels={"std":"标准差 (分歧程度)","mean":"平均分 (整体评价)"})
        n = len(df)
        fig.update_traces(marker=dict(size=[9]*n,color=["#4f7cff"]*n,opacity=0.7,line=dict(width=0)),
                        customdata=list(zip(df["url"],df["votes"])),
                        hovertemplate="<b>%{hovertext}</b><br>标准差: %{x}<br>平均分: %{y}<br>投票人数: %{customdata[1]}<extra></extra>")
        if n:
            mean_y, mean_x = df["mean"].mean(), df["std"].mean()
            fig.add_shape(type="line", xref="paper", x0=0, x1=1, yref="y", y0=mean_y, y1=mean_y,
                        name="mean-line-y", visible=False, line=dict(color="rgba(255,71,87,0.8)", dash="dash"))
            fig.add_shape(type="line", xref="x", x0=mean_x, x1=mean_x, yref="y", y0=Y_RANGE[0], y1=Y_RANGE[1],
                        name="mean-line-x", visible=False, line=dict(color="rgba(46,213,115,0.9)", dash="dot"))
            fig.add_annotation(x=1, y=mean_y, xref="paper", yref="y", text=f"平均分均值：{mean_y:.2f}",
                            name="mean-annotation-y", visible=False, showarrow=False,
                            xanchor="right", yanchor="bottom", font=dict(color="#ff4757", size=12),
                            bgcolor="rgba(255,255,255,0.7)")
            fig.add_annotation(x=mean_x, y=Y_RANGE[1], xref="x", yref="y", text=f"标准差均值：{mean_x:.2f}",
                            name="mean-annotation-x", visible=False, showarrow=False,
                            xanchor="left", yanchor="top", font=dict(color="#2ed573", size=12),
                            bgcolor="rgba(255,255,255,0.7)")
        fig.update_layout(title=dict(text=title,x=.5), width=1150, height=650, dragmode=False,
                        xaxis=dict(range=xr), yaxis=dict(range=Y_RANGE),
                        font=dict(family="Microsoft YaHei, SimHei"), margin=dict(l=80,r=40,t=80,b=80))
        return fig
    cfg = {"responsive":True,"displayModeBar":True,"modeBarButtonsToRemove":["lasso2d","select2d"],"displaylogo":False}

    divs,btns,first=[],[],True
    XR={"Anime":X_STD,"Game":X_STD,"Real":X_STD,"Book":X_ALT,"Music":X_ALT}
    BUTTON_ORDER = ["Anime", "Game", "Book", "Music", "Real"]  # <-- 固定顺序
    for k in BUTTON_ORDER:
        df = df_map[k]
        html = pio.to_html(
            fig(df, f"{USERNAME} 的Bangumi {TYPE_INFO[k]['cn']}评分分布", XR[k]),
            full_html=False,
            include_plotlyjs="cdn" if first else False,
            div_id=f"canvas-{k.lower()}",
            config=cfg,
        )
        divs.append(f'<div class="plot{" active" if first else ""}" id="container-{k.lower()}">{html}</div>')
        btns.append(f'<button data-target="{k.lower()}">{TYPE_INFO[k]["cn"]}</button>')
        first = False  

    t=open("template.html","r",encoding="utf-8").read()
    open(OUTPUT_HTML,"w",encoding="utf-8").write(
        t.replace("<!-- PLOT_DIVS_PLACEHOLDER -->","".join(divs))
         .replace("<!-- BUTTONS_PLACEHOLDER -->","".join(btns))
    )

# ================= MAIN =================

def main():
    print("📥 获取收藏列表...")
    cols=get_collections(USER_ID)

    tasks=[(i["subject_id"],i["subject"]["type"])
           for i in cols
           if i.get("subject",{}).get("type") in (1,2,3,4,6)]

    print(f"🚀 多线程抓取 {len(tasks)} 个 subject")

    res=[]
    with ThreadPoolExecutor(MAX_WORKERS) as p:
        for f in as_completed(p.submit(fetch_subject,s,t) for s,t in tasks):
            r=f.result()
            if r:res.append(r)

    if not res:
        print("⚠ 无有效数据");return

    df=pd.DataFrame(res)
    df.to_csv(OUTPUT_CSV,index=False,encoding="utf-8-sig")

    make_toggle_html({k:df[df["type"]==k] for k in TYPE_INFO})
    print("✅ 多线程完成，HTML 已生成")

if __name__=="__main__":
    main()
