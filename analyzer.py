import time
import warnings
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

warnings.filterwarnings("ignore")

# ── Watchlist ─────────────────────────────────────────────────────────────────
WATCHLIST = {
    "7011.T": ("三菱重工業",      "防衛",           "重工業"),
    "7013.T": ("IHI",             "防衛",           "重工業"),
    "7012.T": ("川崎重工業",      "防衛",           "重工業"),
    "7014.T": ("名村造船所",      "防衛",           "造船"),
    "8035.T": ("東京エレクトロン","半導体",          "半導体"),
    "6857.T": ("アドバンテスト",  "半導体",          "半導体"),
    "6920.T": ("レーザーテック",  "半導体",          "半導体"),
    "4063.T": ("信越化学工業",    "半導体",          "化学"),
    "6981.T": ("村田製作所",      "半導体",          "電子部品"),
    "6976.T": ("太陽誘電",        "半導体",          "電子部品"),
    "7741.T": ("HOYA",            "半導体",          "精密"),
    "9984.T": ("ソフトバンクG",   "AI",             "通信"),
    "6758.T": ("ソニーグループ",  "AI",             "電機"),
    "6861.T": ("キーエンス",      "DX",             "精密"),
    "6501.T": ("日立製作所",      "DX",             "電機"),
    "6702.T": ("富士通",          "DX",             "IT"),
    "4307.T": ("野村総合研究所",  "DX",             "IT"),
    "3697.T": ("SHIFT",           "DX",             "IT"),
    "9613.T": ("NTTデータG",      "データセンター", "IT"),
    "3626.T": ("TIS",             "データセンター", "IT"),
    "8306.T": ("三菱UFJ FG",      "銀行",           "銀行"),
    "8316.T": ("三井住友FG",      "銀行",           "銀行"),
    "8411.T": ("みずほFG",        "銀行",           "銀行"),
    "8766.T": ("東京海上HD",      "銀行",           "保険"),
    "8591.T": ("オリックス",      "銀行",           "金融"),
    "8031.T": ("三井物産",        "商社",           "商社"),
    "8058.T": ("三菱商事",        "商社",           "商社"),
    "8053.T": ("住友商事",        "商社",           "商社"),
    "8002.T": ("丸紅",            "商社",           "商社"),
    "8001.T": ("伊藤忠商事",      "商社",           "商社"),
    "9432.T": ("NTT",             "通信",           "通信"),
    "9433.T": ("KDDI",            "通信",           "通信"),
    "9434.T": ("ソフトバンク",    "通信",           "通信"),
    "7203.T": ("トヨタ自動車",    "DX",             "自動車"),
    "7267.T": ("本田技研",        "DX",             "自動車"),
    "1801.T": ("大成建設",        "建設",           "建設"),
    "1802.T": ("大林組",          "建設",           "建設"),
    "1803.T": ("清水建設",        "建設",           "建設"),
    "1812.T": ("鹿島建設",        "建設",           "建設"),
    "8801.T": ("三井不動産",      "建設",           "不動産"),
    "5401.T": ("日本製鉄",        "建設",           "鉄鋼"),
    "4502.T": ("武田薬品",        "医薬品",         "医薬品"),
    "4503.T": ("アステラス",      "医薬品",         "医薬品"),
    "4568.T": ("第一三共",        "医薬品",         "医薬品"),
    "4519.T": ("中外製薬",        "医薬品",         "医薬品"),
    "9983.T": ("ファストリ",      "インバウンド",   "小売"),
    "9602.T": ("東宝",            "インバウンド",   "娯楽"),
    "9501.T": ("東京電力HD",      "電力",           "電力"),
    "9502.T": ("中部電力",        "電力",           "電力"),
    "9503.T": ("関西電力",        "原発",           "電力"),
    "9504.T": ("中国電力",        "原発",           "電力"),
    "5020.T": ("ENEOS HD",        "電力",           "石油"),
    "9064.T": ("ヤマトHD",        "物流",           "物流"),
    "9062.T": ("日本通運",        "物流",           "物流"),
    "6367.T": ("ダイキン工業",    "DX",             "機械"),
    "6954.T": ("ファナック",      "DX",             "精密"),
    "6752.T": ("パナソニックHD",  "DX",             "電機"),
    "4188.T": ("三菱ケミカルG",   "DX",             "化学"),
    "6273.T": ("SMC",             "DX",             "機械"),
    "4543.T": ("テルモ",          "医薬品",         "医療機器"),
    "2914.T": ("JT",              "インバウンド",   "食品"),
}

INDICES = {
    "nikkei":    "^N225",
    "topix":     "1306.T",
    "growth250": "2516.T",
    "sp500":     "^GSPC",
    "nasdaq":    "^IXIC",
    "sox":       "^SOX",
    "vix":       "^VIX",
    "usdjpy":    "USDJPY=X",
    "us10y":     "^TNX",
    "wti":       "CL=F",
    "btc":       "BTC-USD",
}

# 英語クエリ（news()は英語の方が安定）
THEME_QUERIES_EN = {
    "防衛":           "Japan defense stocks military budget Mitsubishi Heavy",
    "宇宙":           "Japan space industry rocket satellite JAXA stocks",
    "AI":             "Japan AI artificial intelligence stocks semiconductor",
    "半導体":         "Japan semiconductor stocks Tokyo Electron chip",
    "データセンター": "Japan data center power demand stocks cloud",
    "電力":           "Japan electricity power stocks energy demand",
    "原発":           "Japan nuclear power plant reactor stocks",
    "銀行":           "Japan bank stocks interest rate BOJ monetary policy",
    "商社":           "Japan trading company stocks commodity resource",
    "物流":           "Japan logistics stocks e-commerce delivery",
    "インバウンド":   "Japan inbound tourism stocks yen weak visitors",
    "DX":             "Japan digital transformation IT stocks cloud",
    "通信":           "Japan telecom stocks NTT KDDI SoftBank 5G",
    "建設":           "Japan construction infrastructure stocks public works",
    "医薬品":         "Japan pharmaceutical drug stocks biotech approval",
}

POS = ["surge", "rally", "rise", "gain", "buy", "strong", "bullish", "record", "growth",
       "上昇", "買い", "強気", "増益", "好調", "注目", "高騰", "堅調", "急騰"]
NEG = ["fall", "drop", "decline", "sell", "weak", "bearish", "loss", "concern", "risk",
       "下落", "売り", "弱気", "減益", "不調", "警戒", "低迷", "急落"]


# ── Technical helpers ─────────────────────────────────────────────────────────

def _rsi(s: pd.Series, period: int = 14) -> float:
    delta = s.diff().dropna()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_g = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_l = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_g / avg_l.replace(0, np.nan)
    rsi_s = 100 - (100 / (1 + rs))
    return float(rsi_s.iloc[-1]) if not rsi_s.empty else 50.0


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    v = float(atr.iloc[-1])
    return v if not np.isnan(v) else float(high.iloc[-1] - low.iloc[-1])


def _calc_indicators(df: pd.DataFrame) -> dict | None:
    if df is None or len(df) < 30:
        return None
    close  = df["Close"].squeeze()
    high   = df["High"].squeeze()
    low    = df["Low"].squeeze()
    open_p = df["Open"].squeeze()
    vol    = df["Volume"].squeeze()

    ma25 = close.rolling(25).mean()
    ma75 = close.rolling(min(75, len(close))).mean()

    price = float(close.iloc[-1])
    m25   = float(ma25.iloc[-1])
    m75   = float(ma75.iloc[-1]) if not pd.isna(ma75.iloc[-1]) else m25
    dev25 = (price - m25) / m25 * 100
    dev75 = (price - m75) / m75 * 100

    vol_avg20 = float(vol.iloc[-20:].mean()) if len(vol) >= 20 else 1.0
    vol_ratio = float(vol.iloc[-1]) / vol_avg20 if vol_avg20 > 0 else 1.0

    # 連続上昇日数
    up_days = 0
    for i in range(1, min(10, len(close))):
        if float(close.iloc[-i]) > float(close.iloc[-i - 1]):
            up_days += 1
        else:
            break

    # 前日比GU率
    gap_rate = 0.0
    if len(open_p) >= 2:
        pc = float(close.iloc[-2])
        if pc > 0:
            gap_rate = (float(open_p.iloc[-1]) - pc) / pc * 100

    # 上ヒゲ比率
    body = abs(float(close.iloc[-1]) - float(open_p.iloc[-1]))
    upper_wick = float(high.iloc[-1]) - max(float(close.iloc[-1]), float(open_p.iloc[-1]))
    wick_ratio = upper_wick / body if body > 0 else 0.0

    # 直近高値からの距離
    recent_high = float(close.iloc[-60:].max()) if len(close) >= 60 else float(close.max())
    dist_from_high = (price - recent_high) / recent_high * 100  # 負の値 = 高値より下

    # 当日陰陽
    is_bearish = float(close.iloc[-1]) < float(open_p.iloc[-1])

    rsi = _rsi(close)
    atr = _atr(high, low, close)

    return {
        "price":          price,
        "ma25":           m25,
        "ma75":           m75,
        "dev25":          dev25,
        "dev75":          dev75,
        "rsi":            rsi,
        "atr":            atr,
        "vol_ratio":      vol_ratio,
        "up_days":        up_days,
        "gap_rate":       gap_rate,
        "wick_ratio":     wick_ratio,
        "dist_from_high": dist_from_high,
        "is_bearish":     is_bearish,
    }


def _trend_stage(ind: dict) -> tuple[str, int]:
    price = ind["price"]
    m25, m75 = ind["ma25"], ind["ma75"]
    rsi     = ind["rsi"]
    dev25   = ind["dev25"]
    vol_r   = ind["vol_ratio"]

    # ステージ4: 過熱
    if rsi > 78 or dev25 > 12:
        return "ステージ4（過熱）", 4

    # ステージ5: 分配（高値圏で失速）
    if price > m25 and ind["is_bearish"] and vol_r > 1.8 and rsi < 55 and dev25 > 5:
        return "ステージ5（分配）", 5

    # ステージ1: 底打ち圏
    if price < m25 and price < m75:
        return "ステージ1（底打ち）", 1

    # ステージ2: 上昇初動（最優先）
    if price > m25 and rsi >= 45 and rsi <= 68 and dev25 < 8:
        if vol_r >= 1.2:
            return "ステージ2（上昇初動）", 2

    # ステージ3: 上昇加速
    if price > m25 and m25 > m75 and rsi > 60 and dev25 < 12:
        return "ステージ3（上昇加速）", 3

    # ステージ2: 条件緩め
    if price > m25 and rsi >= 45:
        return "ステージ2（上昇初動）", 2

    return "ステージ1（底打ち）", 1


def _entry_score(ind: dict, stage_num: int) -> tuple[int, list, list]:
    """Returns (score, avoid_reasons, positive_signals)"""
    score   = 100
    avoid   = []   # 減点理由（買わない理由）
    signals = []   # 加点・ポジティブ要素

    rsi   = ind["rsi"]
    dev25 = ind["dev25"]
    up    = ind["up_days"]
    gap   = ind["gap_rate"]
    wick  = ind["wick_ratio"]
    vol_r = ind["vol_ratio"]

    # ── 強く減点（買わない理由） ──────────────────────────────
    if rsi >= 75:
        score -= 30; avoid.append(f"RSI過熱 {rsi:.0f}（-30pt）")
    elif rsi >= 68:
        score -= 15; avoid.append(f"RSI高め {rsi:.0f}（-15pt）")
    elif rsi >= 62:
        score -= 6;  avoid.append(f"RSIやや高め {rsi:.0f}（-6pt）")

    if dev25 >= 10:
        score -= 25; avoid.append(f"MA25大幅乖離 +{dev25:.1f}%（-25pt）")
    elif dev25 >= 5:
        score -= 12; avoid.append(f"MA25乖離 +{dev25:.1f}%（-12pt）")
    elif dev25 >= 3:
        score -= 4;  avoid.append(f"MA25乖離 +{dev25:.1f}%（-4pt）")

    if up >= 5:
        score -= 20; avoid.append(f"連騰{up}日目（-20pt）急騰後飛び乗り禁止")
    elif up >= 3:
        score -= 12; avoid.append(f"連騰{up}日目（-12pt）")
    elif up >= 2:
        score -= 5;  avoid.append(f"連騰{up}日目（-5pt）")

    if gap >= 3:
        score -= 15; avoid.append(f"GU +{gap:.1f}%（-15pt）大陽線飛び乗り禁止")
    elif gap >= 1.5:
        score -= 7;  avoid.append(f"GU +{gap:.1f}%（-7pt）")

    if wick >= 1.5:
        score -= 15; avoid.append(f"長い上ヒゲ {wick:.1f}倍（-15pt）")
    elif wick >= 1.0:
        score -= 7;  avoid.append(f"上ヒゲ {wick:.1f}倍（-7pt）")

    if vol_r > 2.5 and ind["is_bearish"]:
        score -= 15; avoid.append(f"出来高急増後陰線（-15pt）需給悪化")

    if stage_num == 4:
        score -= 20; avoid.append("過熱ステージ4（-20pt）")
    elif stage_num == 5:
        score -= 35; avoid.append("分配ステージ5（-35pt）機関売り疑い")
    elif stage_num == 1:
        score -= 10; avoid.append("底打ち圏 エントリー早すぎ（-10pt）")

    # ── ポジティブ要素 ────────────────────────────────────────
    if 48 <= rsi <= 60:
        signals.append(f"RSI{rsi:.0f} 理想水準")
    if -1 <= dev25 <= 2:
        signals.append("MA25近辺 押し目圏")
    elif dev25 < -1:
        signals.append(f"MA25下 {dev25:.1f}% 反発期待")
    if up <= 1 and gap < 1:
        signals.append("エントリー直後 連騰なし")
    if vol_r >= 1.5:
        signals.append(f"出来高 {vol_r:.1f}x 増加")
    if stage_num == 2:
        signals.append("ステージ2 上昇初動（最優先）")
    elif stage_num == 3:
        signals.append("ステージ3 上昇加速中")

    return max(0, score), avoid, signals


def _calc_rr(ind: dict) -> dict:
    price = ind["price"]
    atr   = ind["atr"]
    sl    = round(price - 1.5 * atr, 0)
    t1    = round(price + 2.0 * atr, 0)
    t2    = round(price + 3.5 * atr, 0)
    risk  = price - sl
    reward = t1 - price
    rr    = round(reward / risk, 2) if risk > 0 else 0.0
    profit_pct = round(reward / price * 100, 1)
    loss_pct   = round(risk   / price * 100, 1)
    return {
        "stop_loss":   int(sl),
        "target1":     int(t1),
        "target2":     int(t2),
        "rr":          rr,
        "profit_pct":  profit_pct,
        "loss_pct":    loss_pct,
    }


# ── Data fetching ─────────────────────────────────────────────────────────────

def _fetch_one(args):
    ticker, meta = args
    try:
        df = yf.Ticker(ticker).history(period="4mo", interval="1d", auto_adjust=True)
        return ticker, meta, df if df is not None and len(df) >= 20 else None
    except Exception:
        return ticker, meta, None


def fetch_indices() -> dict:
    result = {}
    tickers = list(INDICES.values())
    try:
        raw = yf.download(tickers, period="5d", interval="1d",
                          auto_adjust=True, progress=False, threads=True)
        for key, sym in INDICES.items():
            try:
                s = raw[("Close", sym)].dropna() if isinstance(raw.columns, pd.MultiIndex) else raw["Close"].dropna()
                if len(s) >= 2:
                    cur, prev = float(s.iloc[-1]), float(s.iloc[-2])
                    result[key] = {"current": cur, "change_pct": round((cur - prev) / prev * 100, 2) if prev else 0.0}
                else:
                    result[key] = {"current": 0.0, "change_pct": 0.0}
            except Exception:
                result[key] = {"current": 0.0, "change_pct": 0.0}
    except Exception:
        for key in INDICES:
            result[key] = {"current": 0.0, "change_pct": 0.0}
    return result


def fetch_stock_histories() -> list:
    items = list(WATCHLIST.items())
    results = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(_fetch_one, item): item for item in items}
        for fut in as_completed(futures):
            results.append(fut.result())
    return results


def fetch_theme_scores() -> dict:
    """テーマ資金循環スコアをDDGS text検索で算出"""
    scores = {}
    for theme, query in THEME_QUERIES_EN.items():
        try:
            results = list(DDGS().text(query, max_results=10))
            count = len(results)
            combined = " ".join(r.get("title", "") + " " + r.get("body", "") for r in results)
            pos = sum(1 for w in POS if w.lower() in combined.lower())
            neg = sum(1 for w in NEG if w.lower() in combined.lower())

            # 記事数・センチメント・ポジティブワードを総合
            base       = min(70, 30 + count * 4)
            sentiment  = (pos - neg) * 5
            heat       = min(100, max(20, int(base + sentiment)))
            fund       = min(100, max(20, int(base - 5 + pos * 4)))
            reason     = f"記事{count}件 / ポジ{pos} / ネガ{neg}"
            scores[theme] = {"heat": heat, "fund_inflow": fund, "article_count": count, "reason": reason}
        except Exception:
            scores[theme] = {"heat": 35, "fund_inflow": 30, "article_count": 0, "reason": "取得失敗"}
        time.sleep(0.35)
    return scores


# ── Scoring ───────────────────────────────────────────────────────────────────

def score_market(idx: dict) -> dict:
    score = 50

    nk_chg    = idx.get("nikkei",  {}).get("change_pct", 0)
    vix       = idx.get("vix",     {}).get("current",    20)
    sp_chg    = idx.get("sp500",   {}).get("change_pct", 0)
    nd_chg    = idx.get("nasdaq",  {}).get("change_pct", 0)
    usdjpy_chg= idx.get("usdjpy", {}).get("change_pct",  0)

    score += max(-20, min(20, nk_chg * 8))

    if vix < 15:   score += 15
    elif vix < 18: score += 8
    elif vix < 22: score += 0
    elif vix < 27: score -= 12
    else:          score -= 22

    score += max(-10, min(10, (sp_chg + nd_chg) / 2 * 5))

    if usdjpy_chg > 0.5:    score += 5
    elif usdjpy_chg < -0.5: score -= 5

    score = max(0, min(100, int(score)))

    if score >= 72:   judgment, risk = "強気",     "リスクオン"
    elif score >= 58: judgment, risk = "やや強気", "リスクオン"
    elif score >= 45: judgment, risk = "中立",     "中立"
    elif score >= 35: judgment, risk = "やや弱気", "リスクオフ"
    else:             judgment, risk = "弱気",     "リスクオフ"

    key_points = [
        f"日経: {idx['nikkei']['current']:,.0f} ({nk_chg:+.2f}%)",
        f"VIX: {vix:.1f}",
        f"ドル円: {idx['usdjpy']['current']:.2f} ({usdjpy_chg:+.2f}%)",
        f"S&P500: {idx['sp500']['current']:,.0f} ({sp_chg:+.2f}%)",
        f"NASDAQ: ({nd_chg:+.2f}%)",
        f"米10年債: {idx['us10y']['current']:.2f}%",
    ]

    favorable, unfavorable = [], []
    if score >= 58:
        if vix < 18:       favorable  += ["半導体", "AI", "DX"]
        if usdjpy_chg > 0: favorable  += ["商社", "自動車"]
        if nk_chg > 1:     favorable  += ["防衛", "インバウンド"]
    if score < 50:
        unfavorable += ["グロース株", "小型株", "高PER"]
        favorable   += ["銀行", "通信", "ディフェンシブ"]
    if score < 38:
        unfavorable += ["全般株式", "リスク資産"]

    return {
        "score":               score,
        "judgment":            judgment,
        "risk_mode":           risk,
        "new_buy_permission":  score >= 48,
        "key_points":          key_points,
        "favorable_sectors":   list(dict.fromkeys(favorable))[:5],
        "unfavorable_sectors": list(dict.fromkeys(unfavorable))[:4],
    }


def score_themes_result(theme_data: dict) -> dict:
    ranked = sorted(theme_data.items(), key=lambda x: x[1]["heat"], reverse=True)
    top10 = [
        {
            "rank": i + 1,
            "name": name,
            "heat": v["heat"],
            "fund_inflow": v["fund_inflow"],
            "reason": v.get("reason", ""),
        }
        for i, (name, v) in enumerate(ranked[:10])
    ]
    avg_heat = sum(v["heat"] for v in theme_data.values()) / len(theme_data) if theme_data else 50
    rising   = [n for n, v in ranked if v["heat"] > avg_heat + 8][:5]
    declining= [n for n, v in ranked if v["heat"] < avg_heat - 8][:5]
    watch    = [r["name"] for r in top10[:5]]
    return {"top10": top10, "rising": rising, "declining": declining, "watch_this_week": watch}


def analyze_stocks(histories, market, theme_data, themes_result):
    buy, watch, danger = [], [], []
    m_score      = market["score"]
    watch_themes = set(themes_result.get("watch_this_week", []))
    buy_ok       = market["new_buy_permission"]

    for ticker, meta, df in histories:
        if df is None:
            continue
        name, theme, sector = meta
        ind = _calc_indicators(df)
        if ind is None:
            continue

        price      = ind["price"]
        stage_s, stage_n = _trend_stage(ind)
        entry_s, avoid_reasons, signals = _entry_score(ind, stage_n)
        rr_data    = _calc_rr(ind)
        rr         = rr_data["rr"]

        t_heat = theme_data.get(theme, {}).get("heat",       50)
        t_fi   = theme_data.get(theme, {}).get("fund_inflow",45)

        # ── 各コンポーネントスコア ────────────────────────────
        s_market = m_score
        s_theme  = t_heat
        s_fund   = t_fi
        # 需給: 出来高比 + ステージ補正
        s_demand = min(100, max(20, int(50 + (ind["vol_ratio"] - 1) * 25)))
        if stage_n in [2, 3]: s_demand = min(100, s_demand + 10)
        s_stage  = {1: 40, 2: 90, 3: 80, 4: 25, 5: 10}.get(stage_n, 50)
        s_entry  = entry_s
        s_rr     = min(100, int(rr / 3.0 * 100)) if rr >= 2.0 else 15

        total = int(
            s_market * 0.20 +
            s_theme  * 0.20 +
            s_fund   * 0.15 +
            s_demand * 0.15 +
            s_stage  * 0.10 +
            s_entry  * 0.15 +
            s_rr     * 0.05
        )
        stars = 5 if total >= 90 else 4 if total >= 80 else 3 if total >= 70 else 2 if total >= 60 else 1

        score_components = {
            "market": {"label": "地合い",       "weight": 20, "score": s_market, "contrib": round(s_market * 0.20, 1)},
            "theme":  {"label": "テーマ",       "weight": 20, "score": s_theme,  "contrib": round(s_theme  * 0.20, 1)},
            "fund":   {"label": "資金流入",     "weight": 15, "score": s_fund,   "contrib": round(s_fund   * 0.15, 1)},
            "demand": {"label": "需給",         "weight": 15, "score": s_demand, "contrib": round(s_demand * 0.15, 1)},
            "stage":  {"label": "ステージ",     "weight": 10, "score": s_stage,  "contrib": round(s_stage  * 0.10, 1)},
            "entry":  {"label": "エントリー位置","weight": 15, "score": s_entry,  "contrib": round(s_entry  * 0.15, 1)},
            "rr":     {"label": "RR",           "weight":  5, "score": s_rr,     "contrib": round(s_rr     * 0.05, 1)},
        }

        # テーマ適合ポジティブ追記
        if t_heat >= 75:
            signals.append(f"テーマ熱度{t_heat}（強）")
        elif t_heat >= 60:
            signals.append(f"テーマ熱度{t_heat}（中）")

        base = {
            "ticker":           ticker.replace(".T", ""),
            "name":             name,
            "theme":            theme,
            "sector":           sector,
            "total_score":      total,
            "stars":            stars,
            "entry_score":      entry_s,
            "trend_stage":      stage_s,
            "score_components": score_components,
            "avoid_reasons":    avoid_reasons,
            "buy_reasons":      signals,
        }

        # ─── 危険銘柄 ───────────────────────────────────────────
        if stage_n == 5:
            danger.append({**base, "danger_reason": "分配ステージ・高値圏での出来高急増", "danger_type": "分配疑い"})
            continue
        if entry_s < 50 and ind["rsi"] > 75:
            danger.append({**base, "danger_reason": f"RSI{ind['rsi']:.0f} 過熱・急騰後飛び乗り禁止", "danger_type": "RSI過熱"})
            continue
        if len(avoid_reasons) >= 4:
            danger.append({**base, "danger_reason": avoid_reasons[0], "danger_type": "複合リスク"})
            continue

        # ─── 買い候補（フィルター厳格化） ──────────────────────
        # 哲学: エントリー位置69以下 → 総合点に関係なく禁止
        if (entry_s >= 70          # STEP5: 70以上必須
                and rr >= 2.0      # STEP6: RR2.0以上必須
                and total >= 70    # STEP7: 総合70以上
                and stage_n <= 3   # ステージ4/5は除外
                and t_heat >= 55   # テーマが極端に弱い場合は除外
                and buy_ok):       # 地合い確認
            danger_count = len(avoid_reasons)
            rr_data_full = {**rr_data, "rr": rr}
            buy.append({
                **base,
                "current_price": int(price),
                "stop_loss":     rr_data["stop_loss"],
                "target1":       rr_data["target1"],
                "target2":       rr_data["target2"],
                "rr":            rr,
                "profit_pct":    rr_data["profit_pct"],
                "loss_pct":      rr_data["loss_pct"],
                "hold_days":     "2〜7営業日",
                "risk_count":    danger_count,
            })

        # ─── 監視銘柄 ───────────────────────────────────────────
        elif total >= 63 or (theme in watch_themes and entry_s >= 60 and total >= 58):
            trigger = "押し目・エントリースコア改善待ち"
            if stage_n == 1:         trigger = "MA25上抜けを確認後エントリー"
            elif entry_s < 70:       trigger = "エントリースコア70以上になるまで待機"
            elif rr < 2.0:           trigger = "押し目でRR2.0以上確認後エントリー"
            elif not buy_ok:         trigger = "地合い改善後に再判断"
            watch.append({
                **base,
                "watch_reason":  f"{sector} ｜ テーマ熱度{t_heat} ｜ 出来高比{ind['vol_ratio']:.1f}x",
                "entry_trigger": trigger,
                "rr":            rr,
            })

    buy.sort(key=lambda x: x["total_score"], reverse=True)
    watch.sort(key=lambda x: x["total_score"], reverse=True)
    danger.sort(key=lambda x: x.get("total_score", 0), reverse=True)
    return buy[:10], watch[:20], danger[:20]


# ── Main ──────────────────────────────────────────────────────────────────────

def run_analysis(progress_callback=None) -> dict:
    def cb(pct, msg):
        if progress_callback:
            progress_callback(pct, msg)

    today = datetime.now().strftime("%Y-%m-%d")

    cb(0.05, "市場データ取得中...")
    idx = fetch_indices()

    cb(0.18, "地合い分析中 (STEP1)...")
    market = score_market(idx)

    cb(0.28, "テーマ資金循環分析中 (STEP2) — 約30秒...")
    theme_data = fetch_theme_scores()
    themes = score_themes_result(theme_data)

    cb(0.55, "銘柄データ取得中 (STEP3〜5) — 約20秒...")
    histories = fetch_stock_histories()

    cb(0.82, "スコアリング・RR算出・最終判定中 (STEP6〜7)...")
    buy, watch, danger = analyze_stocks(histories, market, theme_data, themes)

    cb(1.00, "分析完了")

    top_theme = themes["top10"][0]["name"] if themes["top10"] else "なし"
    parts = [
        f"地合いスコア {market['score']}（{market['judgment']}）",
        f"最強テーマ: {top_theme}",
        f"買い候補 {len(buy)}銘柄 ／ 監視 {len(watch)}銘柄 ／ 危険 {len(danger)}銘柄",
    ]
    if not market["new_buy_permission"]:
        parts.append("⚠ 地合い不良 → 新規買い非推奨")

    return {
        "analysis_date":  today,
        "step1_market":   market,
        "step2_themes":   themes,
        "buy_candidates": buy,
        "watch_stocks":   watch,
        "danger_stocks":  danger,
        "market_summary": "　".join(parts),
    }
