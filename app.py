import streamlit as st
from datetime import datetime
from analyzer import run_analysis

st.set_page_config(
    page_title="日本株スイングAI",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
html, body, [class*="css"] { font-family: 'Hiragino Sans', 'Yu Gothic', sans-serif; }
.block-container { padding: 0.5rem 0.75rem 3rem; max-width: 500px; margin: auto; }

/* 地合いカード */
.score-card { border-radius: 14px; padding: 18px; text-align: center; margin-bottom: 14px; }
.score-bull    { background: #0a2318; border: 2px solid #22c55e; }
.score-neutral { background: #16162a; border: 2px solid #6366f1; }
.score-bear    { background: #2a0a0a; border: 2px solid #ef4444; }
.score-num   { font-size: 3.2rem; font-weight: 900; line-height: 1; }
.score-label { font-size: 1rem; opacity: 0.85; margin-top: 6px; }

/* 買い許容バナー */
.banner-ok   { background:#0a3320; border:1px solid #22c55e; color:#86efac; border-radius:8px; padding:8px 14px; font-weight:700; font-size:1rem; text-align:center; margin:8px 0; }
.banner-ng   { background:#3a0a0a; border:2px solid #ef4444; color:#fca5a5; border-radius:8px; padding:10px 14px; font-weight:900; font-size:1.05rem; text-align:center; margin:8px 0; }

/* テーマ */
.theme-pill { display:inline-block; background:#2d1b69; border:1px solid #7c3aed; color:#c4b5fd; border-radius:20px; padding:3px 10px; font-size:0.78rem; margin:2px; }
.theme-hot  { background:#3b0764; border-color:#a855f7; color:#e9d5ff; font-weight:700; }

/* 銘柄カード */
.stock-card { border-radius: 12px; padding: 14px 16px; margin-bottom: 10px; border-left: 4px solid transparent; }
.stock-buy    { background: #0a2318; border-color: #22c55e; }
.stock-watch  { background: #1c1a00; border-color: #eab308; }
.stock-danger { background: #2a0a0a; border-color: #ef4444; }

/* 最重要: 買わない理由ブロック → 最上部・赤背景 */
.avoid-block {
    background: #3d1515;
    border-left: 4px solid #ef4444;
    border-radius: 6px;
    padding: 7px 11px;
    margin-bottom: 8px;
    font-size: 0.82rem;
    color: #fca5a5;
    font-weight: 600;
}
.avoid-item::before { content: "🚫 "; }

/* 買い根拠ブロック */
.signal-block {
    background: #0a2318;
    border-left: 3px solid #22c55e;
    border-radius: 5px;
    padding: 5px 10px;
    margin-bottom: 6px;
    font-size: 0.80rem;
    color: #86efac;
}

/* スコア内訳 */
.score-row { display:flex; justify-content:space-between; font-size:0.79rem; padding:2px 0; border-bottom:1px solid #ffffff10; }
.score-label-c { color:#94a3b8; }
.score-val    { color:#e2e8f0; font-weight:600; }
.score-contrib{ color:#22c55e; font-size:0.75rem; }

.stock-name   { font-size: 1.05rem; font-weight: 800; }
.stock-ticker { font-size: 0.8rem; opacity: 0.55; margin-left: 6px; }
.stock-meta   { font-size: 0.8rem; opacity: 0.72; margin-top: 4px; }
.price-row    { font-size: 0.82rem; margin-top: 5px; opacity: 0.85; }
.rr-ok  { color: #22c55e; font-weight: 700; }
.rr-warn{ color: #eab308; font-weight: 700; }
.rr-ng  { color: #ef4444; font-weight: 700; }
.stars  { color: #facc15; }

.badge-ok   { background:#14532d; color:#bbf7d0; border-radius:5px; padding:1px 8px; font-size:0.79rem; font-weight:700; }
.badge-warn { background:#713f12; color:#fef08a; border-radius:5px; padding:1px 8px; font-size:0.79rem; font-weight:700; }
.badge-ng   { background:#7f1d1d; color:#fecaca; border-radius:5px; padding:1px 8px; font-size:0.79rem; font-weight:700; }

.section-title { font-size:0.85rem; font-weight:700; letter-spacing:0.06em; opacity:0.45; text-transform:uppercase; margin:18px 0 7px; }
.top-bar { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
.top-date{ font-size:0.75rem; opacity:0.45; }
</style>
""", unsafe_allow_html=True)


# ── helpers ───────────────────────────────────────────────────────────────────

def market_class(s):
    return "score-bull" if s >= 65 else "score-neutral" if s >= 45 else "score-bear"

def market_color(s):
    return "#22c55e" if s >= 65 else "#6366f1" if s >= 45 else "#ef4444"

def entry_badge(s):
    if s >= 80:   return f'<span class="badge-ok">◎ {s}</span>'
    if s >= 70:   return f'<span class="badge-warn">△ {s}</span>'
    return f'<span class="badge-ng">✕ {s}</span>'

def stars_html(n):
    return "★" * n + "☆" * (5 - n)

def rr_class(r):
    return "rr-ok" if r >= 3.0 else "rr-warn" if r >= 2.0 else "rr-ng"


# ── section renderers ─────────────────────────────────────────────────────────

def render_market(m: dict):
    score = m.get("score", 0)
    permitted = m.get("new_buy_permission", False)

    st.markdown(f"""
    <div class="score-card {market_class(score)}">
      <div class="score-num" style="color:{market_color(score)}">{score}</div>
      <div class="score-label">{m.get('judgment','')}　{m.get('risk_mode','')}</div>
    </div>
    """, unsafe_allow_html=True)

    if permitted:
        st.markdown('<div class="banner-ok">✅ 新規買い可　地合い良好</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="banner-ng">🚫 新規買い禁止　地合い不良 → 全銘柄スキップ</div>', unsafe_allow_html=True)

    favs  = m.get("favorable_sectors",   [])
    unfavs= m.get("unfavorable_sectors", [])
    cols  = st.columns(2)
    if favs:
        cols[0].markdown("**有利**<br>" + "　".join(f'<span style="color:#22c55e">{s}</span>' for s in favs), unsafe_allow_html=True)
    if unfavs:
        cols[1].markdown("**不利**<br>" + "　".join(f'<span style="color:#ef4444">{s}</span>' for s in unfavs), unsafe_allow_html=True)

    with st.expander("📊 指標詳細"):
        for kp in m.get("key_points", []):
            st.caption(kp)


def render_themes(t: dict):
    top10 = t.get("top10", [])
    watch = t.get("watch_this_week", [])
    rising= t.get("rising", [])
    declining = t.get("declining", [])

    st.markdown('<div class="section-title">🟣 テーマ資金循環</div>', unsafe_allow_html=True)

    pills = ""
    for name in watch:
        hot = any(r.get("name") == name and r.get("heat", 0) >= 70 for r in top10)
        cls = "theme-pill theme-hot" if hot else "theme-pill"
        pills += f'<span class="{cls}">{name}</span>'
    st.markdown(pills, unsafe_allow_html=True)

    if rising:
        st.markdown("↑ " + "　".join(f'<span style="color:#22c55e;font-size:0.8rem">{n}</span>' for n in rising), unsafe_allow_html=True)
    if declining:
        st.markdown("↓ " + "　".join(f'<span style="color:#ef4444;font-size:0.8rem">{n}</span>' for n in declining), unsafe_allow_html=True)

    with st.expander("テーマランキング TOP10"):
        for r in top10:
            heat = r.get("heat", 0)
            fi   = r.get("fund_inflow", 0)
            bar  = "█" * (heat // 10) + "░" * (10 - heat // 10)
            color= "#22c55e" if heat >= 70 else "#eab308" if heat >= 55 else "#ef4444"
            st.markdown(
                f'**{r["rank"]}.{r["name"]}**　'
                f'<span style="color:{color}">熱度{heat}</span>　{bar}　流入{fi}',
                unsafe_allow_html=True
            )
            reason = r.get("reason", "")
            if reason:
                st.caption(reason)


def _score_breakdown(components: dict):
    """スコア内訳テーブル"""
    rows = ""
    total_contrib = 0
    for _, c in components.items():
        sc = c["score"]
        ct = c["contrib"]
        total_contrib += ct
        bar = "▮" * (sc // 20) + "▯" * (5 - sc // 20)
        rows += (
            f'<div class="score-row">'
            f'<span class="score-label-c">{c["label"]}({c["weight"]}%)</span>'
            f'<span>{bar}</span>'
            f'<span class="score-val">{sc}点</span>'
            f'<span class="score-contrib">→ {ct}pt</span>'
            f'</div>'
        )
    rows += (
        f'<div class="score-row" style="margin-top:4px;border-top:1px solid #ffffff30">'
        f'<span style="color:#e2e8f0;font-weight:700">合計</span>'
        f'<span></span><span></span>'
        f'<span style="color:#facc15;font-weight:700">{total_contrib:.1f}pt</span>'
        f'</div>'
    )
    return rows


def render_buy_candidates(stocks: list, market_ok: bool):
    if not stocks:
        if not market_ok:
            st.markdown('<div class="stock-card stock-danger" style="text-align:center">🚫 地合い不良のため買い候補なし</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="stock-card stock-watch" style="text-align:center;opacity:0.6">条件を満たす買い候補なし（無理に買わない）</div>', unsafe_allow_html=True)
        return

    for s in stocks:
        avoid   = s.get("avoid_reasons", [])
        signals = s.get("buy_reasons",   [])
        comps   = s.get("score_components", {})
        rr      = s.get("rr", 0.0)

        # ① 買わない理由（最上部・最優先表示）
        avoid_html = ""
        if avoid:
            items = "".join(f'<div class="avoid-item">{a}</div>' for a in avoid)
            avoid_html = f'<div class="avoid-block">{items}</div>'

        # ② 買い根拠
        signal_html = ""
        if signals:
            items = "　｜　".join(signals)
            signal_html = f'<div class="signal-block">✅ {items}</div>'

        eb = entry_badge(s["entry_score"])
        rc = rr_class(rr)

        st.markdown(f"""
        <div class="stock-card stock-buy">
          {avoid_html}
          {signal_html}
          <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:4px">
            <span class="stars">{stars_html(s['stars'])}</span>
            <span style="font-size:0.82rem;opacity:0.6">総合{s['total_score']}</span>
            {eb}
          </div>
          <div class="stock-name">{s['name']}<span class="stock-ticker">{s['ticker']}</span></div>
          <div class="stock-meta">
            <span class="theme-pill">{s['theme']}</span>
            <span style="margin-left:6px;font-size:0.78rem">{s['trend_stage']}</span>
          </div>
          <div class="price-row">
            現値 <b>{s['current_price']:,}</b>　損切 {s['stop_loss']:,}　T1 {s['target1']:,}　T2 {s['target2']:,}
          </div>
          <div class="price-row">
            <span class="{rc}">RR {rr:.1f}x</span>
            　利確 +{s.get('profit_pct',0)}%　損失 -{s.get('loss_pct',0)}%
            　目安 {s.get('hold_days','')}
          </div>
        </div>
        """, unsafe_allow_html=True)

        if comps:
            with st.expander(f"📊 {s['name']} スコア内訳"):
                st.markdown(
                    f'<div style="background:#0f172a;border-radius:8px;padding:10px">'
                    f'{_score_breakdown(comps)}</div>',
                    unsafe_allow_html=True
                )
                st.caption(f"セクター: {s.get('sector','')}　| 判定: エントリー{s['entry_score']}点 / RR{rr:.2f}x")


def render_watch_stocks(stocks: list):
    if not stocks:
        return
    for s in stocks:
        avoid  = s.get("avoid_reasons", [])
        comps  = s.get("score_components", {})
        rr     = s.get("rr", 0.0)

        avoid_html = ""
        if avoid:
            items = "　".join(f"🚫{a.split('（')[0]}" for a in avoid[:2])
            avoid_html = f'<div style="font-size:0.78rem;color:#fca5a5;margin-bottom:4px">{items}</div>'

        eb = entry_badge(s["entry_score"])
        st.markdown(f"""
        <div class="stock-card stock-watch">
          {avoid_html}
          <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:4px">
            <span style="font-size:0.82rem;opacity:0.6">総合{s['total_score']}</span>
            {eb}
          </div>
          <div class="stock-name">{s['name']}<span class="stock-ticker">{s['ticker']}</span></div>
          <div class="stock-meta">
            <span class="theme-pill">{s['theme']}</span>
            <span style="margin-left:6px;font-size:0.78rem">{s['trend_stage']}</span>
          </div>
          <div class="stock-meta" style="margin-top:5px;opacity:0.7">{s.get('watch_reason','')}</div>
          <div style="color:#eab308;font-size:0.8rem;margin-top:4px">▶ {s.get('entry_trigger','')}</div>
        </div>
        """, unsafe_allow_html=True)

        if comps:
            with st.expander(f"📊 {s['name']} スコア内訳"):
                st.markdown(
                    f'<div style="background:#0f172a;border-radius:8px;padding:10px">'
                    f'{_score_breakdown(comps)}</div>',
                    unsafe_allow_html=True
                )


def render_danger_stocks(stocks: list):
    if not stocks:
        return
    for s in stocks:
        st.markdown(f"""
        <div class="stock-card stock-danger">
          <div class="stock-name">{s['name']}<span class="stock-ticker">{s['ticker']}</span>
            <span style="margin-left:8px;font-size:0.78rem;color:#f87171">[{s.get('danger_type','')}]</span>
          </div>
          <div style="font-size:0.82rem;color:#fca5a5;margin-top:5px">🚫 {s.get('danger_reason','')}</div>
        </div>
        """, unsafe_allow_html=True)


# ── main UI ───────────────────────────────────────────────────────────────────

today_str = datetime.now().strftime("%Y年%m月%d日")
st.markdown(f"""
<div class="top-bar">
  <div style="font-size:1.1rem;font-weight:900">📈 日本株スイングAI</div>
  <div class="top-date">{today_str}</div>
</div>
<div style="font-size:0.72rem;opacity:0.4;margin-bottom:10px">
  機関投資家視点 ｜ 負けないエントリー探し ｜ API不要
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])
with col1:
    run_btn = st.button("🔍 分析開始（約60秒）", use_container_width=True, type="primary")
with col2:
    if st.button("🗑 クリア", use_container_width=True):
        st.session_state.pop("result", None)
        st.rerun()

if run_btn:
    pb  = st.progress(0, text="準備中...")
    txt = st.empty()
    def on_progress(pct, label):
        pb.progress(pct, text=label)
        txt.caption(label)
    try:
        result = run_analysis(progress_callback=on_progress)
        if "error" in result:
            st.error(result["error"])
        else:
            st.session_state["result"] = result
    except Exception as e:
        st.error(f"エラー: {e}")
    finally:
        pb.empty(); txt.empty()
    if "result" in st.session_state:
        st.rerun()


# ── results ───────────────────────────────────────────────────────────────────

if "result" in st.session_state:
    r = st.session_state["result"]
    market = r.get("step1_market", {})
    buy_ok = market.get("new_buy_permission", False)

    # ① 地合い
    st.markdown('<div class="section-title">🔵 地合い (STEP1)</div>', unsafe_allow_html=True)
    render_market(market)

    # ② テーマ
    if "step2_themes" in r:
        render_themes(r["step2_themes"])

    # ③ 買い候補
    buys = r.get("buy_candidates", [])
    st.markdown(
        f'<div class="section-title">🟢 買い候補 {len(buys)}銘柄（エントリー位置70以上・RR2.0以上・地合い確認済）</div>',
        unsafe_allow_html=True
    )
    render_buy_candidates(buys, buy_ok)

    # ④ 監視
    watches = r.get("watch_stocks", [])
    if watches:
        st.markdown(
            f'<div class="section-title">🟡 監視銘柄 {len(watches)}銘柄（条件改善待ち）</div>',
            unsafe_allow_html=True
        )
        render_watch_stocks(watches)

    # ⑤ 危険
    dangers = r.get("danger_stocks", [])
    if dangers:
        st.markdown(
            f'<div class="section-title">🔴 危険銘柄 {len(dangers)}銘柄（エントリー禁止）</div>',
            unsafe_allow_html=True
        )
        render_danger_stocks(dangers)

    # ⑥ 総括
    summary = r.get("market_summary", "")
    if summary:
        with st.expander("📋 本日の総括"):
            st.write(summary)
            st.caption("免責: 本ツールは情報提供のみを目的とします。投資判断はご自身の責任で行ってください。")

    st.caption(f"分析日: {r.get('analysis_date','')}　| データ: yfinance / DDGS")

else:
    st.markdown("""
    <div style="text-align:center;opacity:0.35;padding:50px 0">
      <div style="font-size:2.5rem">📊</div>
      <div style="margin-top:10px;font-size:1rem">「分析開始」を押してください</div>
      <div style="font-size:0.78rem;margin-top:6px">
        市場→テーマ→銘柄→エントリー の順に自動分析します
      </div>
    </div>
    """, unsafe_allow_html=True)
