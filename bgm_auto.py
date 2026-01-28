import os,math,time,requests,pandas as pd
import plotly.graph_objects as go,plotly.io as pio
from concurrent.futures import ThreadPoolExecutor,as_completed

USER_ID=888347
API_BASE="https://api.bgm.tv"
OUTPUT_CSV="bangumi_888347.csv"
OUTPUT_HTML="index.html"
ACCESS_TOKEN=os.getenv("BGM_TOKEN")

HEADERS={
    "User-Agent":"12819/bgm-collection-fetcher (private-script)",
    "Accept":"application/json",
    "Authorization":f"Bearer {ACCESS_TOKEN}"
}

TYPE_INFO={
    "Book":{"cn":"书籍"},"Anime":{"cn":"动画"},"Music":{"cn":"音乐"},"Game":{"cn":"游戏"},"Real":{"cn":"三次元"},
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
        if votes <=1 or mean is None:return None#排除掉只有一个点的情况

        return {
            "name":d.get("name_cn") or d.get("name"),
            "mean":round(mean,3),
            "std":round(std,3),
            "rank":d["rating"]["rank"],
            "type":{1:"Book",2:"Anime",3:"Music",4:"Game",6:"Real"}[stype],
            "votes":sum(cnt.values()),
            "url":f"https://bangumi.tv/subject/{sid}"
        }
    except Exception:
        return

# ================= PLOT =================
def make_toggle_html(df_map):
    pad=lambda s:[s.min()-(s.max()-s.min())*.05,s.max()+(s.max()-s.min())*.05]

    df_std=pd.concat([df_map["Anime"],df_map["Game"]],ignore_index=True)
    df_alt=pd.concat([df_map["Book"],df_map["Music"]],ignore_index=True)
    df_all=pd.concat(df_map.values(),ignore_index=True)
    X_STD,X_ALT=pad(df_std["std"]),pad(df_alt["std"])
    Y_RANGE=pad(df_all["mean"])

    def fig(df,title,xr):
        fig=go.Figure();eps=1e-6
        df_ranked=df[df["rank"]>0].copy(); df_unranked=df[df["rank"]==0]

        for d, name, color, size, line in [
            (df_ranked, "有榜单排名", -(df_ranked["rank"]**0.25), [9]*len(df_ranked), 1),
            (df_unranked, "未上榜作品", "rgba(160,160,160,0.45)", [8]*len(df_unranked), 1)
        ]:
            if not d.empty:
                marker=dict(size=size,color=color,colorscale="Magma" if name=="有榜单排名" else None,
                            reversescale=False,opacity=0.75 if name=="有榜单排名" else 0.45,
                            cmin=-(10000**0.25)-eps,cmax=-(1**0.25)+eps if name=="有榜单排名" else None,
                            line=dict(width=line,color="rgba(0,0,0,0.4)"))
                cb=dict(title="榜单排名",tickmode="array",
                        tickvals=[-(v**0.25) for v in [1,10,100,1000,10000]],
                        ticktext=["1","10","100","1000","10000"],len=0.75) if name=="有榜单排名" else None
                fig.add_scatter(
                    x=d["std"],y=d["mean"],mode="markers",hovertext=d["name"],
                    customdata=list(zip(d.get("url",[]),d.get("votes",[]),d.get("rank",[]),d.get("std", []))),
                    marker={**marker,**({"colorbar":cb} if cb else {})},
                    name=name,
                    hovertemplate="<b>%{hovertext}</b><br>标准差: %{customdata[3]:.2f}<br>平均分: %{y}<br>"+("排名: %{customdata[2]}" if name=="有榜单排名" else "Rank: 未上榜")+"<br>投票人数: %{customdata[1]}<extra></extra>"
                )
        # 悬浮高亮点
        fig.add_scatter(x=[],y=[],mode="markers",marker=dict(size=18,color="rgba(255,71,87,0.65)",line=dict(width=0)),
                        hoverinfo="skip",showlegend=False,name="_hover")
        if len(df):
            mean_y,mean_x=df["mean"].mean(),df["std"].mean()
            fig.update_layout(
                shapes=[dict(type="line",xref="paper",x0=0,x1=1,yref="y",y0=mean_y,y1=mean_y,
                             name="mean-line-y",visible=False,line=dict(color="rgba(255,71,87,0.8)",dash="dash")),
                        dict(type="line",xref="x",x0=mean_x,x1=mean_x,yref="y",y0=Y_RANGE[0],y1=Y_RANGE[1],
                             name="mean-line-x",visible=False,line=dict(color="rgba(46,213,115,0.9)",dash="dot"))],
                annotations=[dict(x=1,y=mean_y,xref="paper",yref="y",text=f"平均分均值：{mean_y:.2f}",
                                  name="mean-annotation-y",visible=False,showarrow=False,
                                  xanchor="right",yanchor="bottom",font=dict(color="#ff4757",size=12),
                                  bgcolor="rgba(255,255,255,0.7)"),
                             dict(x=mean_x,y=Y_RANGE[1],xref="x",yref="y",text=f"标准差均值：{mean_x:.2f}",
                                  name="mean-annotation-x",visible=False,showarrow=False,
                                  xanchor="left",yanchor="top",font=dict(color="#2ed573",size=12),
                                  bgcolor="rgba(255,255,255,0.7)")])
        fig.update_layout(title=dict(text=title,x=0.5),width=1150,height=650,dragmode=False,hovermode="closest",
                          xaxis=dict(range=xr,title="标准差 (分歧程度)"),
                          yaxis=dict(range=Y_RANGE,title="平均分 (整体评价)"),
                          font=dict(family="Microsoft YaHei, SimHei"),margin=dict(l=80,r=40,t=80,b=80),uirevision="static")
        return fig

    cfg = {"responsive":True,"displayModeBar":True,"modeBarButtonsToRemove":["lasso2d","select2d"],"displaylogo":False,"doubleClick": False}

    XR = {"Anime": X_STD, "Game": X_STD, "Real": X_STD, "Book": X_ALT, "Music": X_ALT}
    BUTTON_ORDER = ["Anime", "Game", "Book", "Music", "Real"]

    t = open("template.html", "r", encoding="utf-8").read()
    for i, k in enumerate(BUTTON_ORDER):
        html = pio.to_html(fig(df_map[k], f"{USERNAME} 的Bangumi {TYPE_INFO[k]['cn']}评分分布", XR[k]),
                        full_html=False, include_plotlyjs="cdn" if i==0 else False,
                        div_id=f"canvas-{k.lower()}", config=cfg)
        t = t.replace('<!-- Plotly图 -->', html, 1)#注入到模板里对应的div
    open(OUTPUT_HTML, "w", encoding="utf-8").write(t)

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
