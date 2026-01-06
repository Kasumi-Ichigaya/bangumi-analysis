import requests
import csv
import math
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# ================= 配置 =================

USER_ID = 888347
API_BASE = "https://api.bgm.tv"
OUTPUT_CSV = "bangumi_result.csv"
ACCESS_TOKEN = "kBgUZMutEmPoyYqgOX0zmxSN4qh9Jg3NpgCffc9V"

HEADERS = {
    "User-Agent": "12819/bgm-collection-fetcher (private-script)",
    "Accept": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

MAX_WORKERS = 9   # 并发数，6~10 比较安全
REQUEST_DELAY = 0.1  # 防止过快（秒）

# ========================================

session = requests.Session()
session.headers.update(HEADERS)


def get_all_subject_ids(user_id):
    """通过 API 获取用户所有收藏的 subject_id"""
    subject_ids = []
    offset = 0
    limit = 30

    while True:
        url = f"{API_BASE}/v0/users/{user_id}/collections"
        params = {
            "type": 2,
            "limit": limit,
            "offset": offset
        }

        r = session.get(url, params=params, timeout=10)
        if r.status_code == 400:
            print("📌 offset 到头，收藏列表获取完毕")
            break
        r.raise_for_status()
        data = r.json()

        if not data.get("data"):
            break

        for item in data["data"]:
            subject = item.get("subject", {})
            if subject.get("type") == 2: #1 为 书籍,2 为 动画,3 为 音乐,4 为 游戏,6 为 三次元
                subject_ids.append(item["subject_id"])

        offset += limit
        time.sleep(REQUEST_DELAY)

    return subject_ids


def calc_mean_std(counts: dict):
    """
    根据评分分布计算平均分和标准差
    counts: {"1": 12, "2": 34, ..., "10": 56}
    """
    total = sum(counts.values())
    if total == 0:
        return None, None

    mean = sum(int(k) * v for k, v in counts.items()) / total
    var = sum(v * (int(k) - mean) ** 2 for k, v in counts.items()) / total
    std = math.sqrt(var)

    return mean, std


def fetch_subject(subject_id):
    """获取单个 subject 的信息并计算"""
    url = f"{API_BASE}/v0/subjects/{subject_id}"

    try:
        r = session.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()

        name = data.get("name_cn") or data.get("name")
        rating = data.get("rating", {})
        counts = rating.get("count", {})

        mean, std = calc_mean_std(counts)
        if mean is None:
            return None

        return {
            "name": name,
            "mean": round(mean, 3),
            "std": round(std, 3),
            "subject_id": subject_id
        }

    except Exception as e:
        print(f"❌ subject {subject_id} 失败：{e}")
        return None


def main():
    print("📥 获取收藏列表中...")
    subject_ids = get_all_subject_ids(USER_ID)
    print(f"✔ 共找到 {len(subject_ids)} 个 subject")

    results = []

    print("🚀 并发计算中...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(fetch_subject, sid) for sid in subject_ids]

        for f in as_completed(futures):
            res = f.result()
            if res:
                results.append(res)

    if not results:
        print("⚠ 无成功数据，未生成 CSV")
        return

    print(f"💾 写入 CSV：{OUTPUT_CSV}")
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["name", "mean", "std", "subject_id"]
        )
        writer.writeheader()
        writer.writerows(results)

    print("✅ 完成！")


if __name__ == "__main__":
    main()
