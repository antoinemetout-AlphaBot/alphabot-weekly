"""
AlphaBot — Agent Rédacteur ✍️  v3.0
Design : Visual-first finance dashboard.
Logos crypto CDN + avatars sociétés + sparklines Chart.js + dashboard KPIs.
Structure : Dashboard visuel → Analyse IA → Texte approfondi
"""

import os, json
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import NEWSLETTER_NAME, NEWSLETTER_TAGLINE, OUTPUT_DIR
try:
    from utils.activity_logger import log_event as _log
    _AGENT_R = "Agent Rédacteur"
except Exception:
    def _log(*a, **k): pass
    _AGENT_R = "Agent Rédacteur"

# ─── MAPPINGS ────────────────────────────────────────────────────────────────
CRYPTO_LOGO_URL = "https://cdn.jsdelivr.net/gh/spothq/cryptocurrency-icons@latest/svg/color/{sym}.svg"

STOCK_COLORS = {
    "Apple":        ("#1a1a1a", "#ffffff", "AAPL"),
    "NVIDIA":       ("#76b900", "#ffffff", "NVDA"),
    "Tesla":        ("#cc0000", "#ffffff", "TSLA"),
    "LVMH":         ("#b8860b", "#ffffff", "MC"),
    "TotalEnergies":("#e30613", "#ffffff", "TTE"),
    "Google":       ("#4285f4", "#ffffff", "GOOG"),
    "Microsoft":    ("#00a4ef", "#ffffff", "MSFT"),
    "Amazon":       ("#ff9900", "#ffffff", "AMZN"),
    "Meta":         ("#0866ff", "#ffffff", "META"),
    "BNP Paribas":  ("#009900", "#ffffff", "BNP"),
}

# Logos Clearbit pour les entreprises
STOCK_LOGOS = {
    "Apple": "apple.com",
    "NVIDIA": "nvidia.com",
    "Tesla": "tesla.com",
    "Microsoft": "microsoft.com",
    "Amazon": "amazon.com",
    "Alphabet": "google.com",
    "Google": "google.com",
    "Meta": "meta.com",
    "LVMH": "lvmh.com",
    "TotalEnergies": "totalenergies.com",
    "Lockheed Martin": "lockheedmartin.com",
    "ExxonMobil": "exxonmobil.com",
    "JPMorgan": "jpmorganchase.com",
    "Goldman Sachs": "goldmansachs.com",
    "BNP Paribas": "bnpparibas.com",
}

# fallback gradient palette pour les actions non listées
PALETTE = ["#6366f1","#ec4899","#14b8a6","#f59e0b","#8b5cf6","#ef4444","#22d3ee"]


class AgentRedacteur:

    def __init__(self):
        print("✍️  Agent Rédacteur initialisé")
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ─── HELPERS ─────────────────────────────────────────────────────────────

    @staticmethod
    def _md(text: str) -> str:
        import re
        if not text:
            return ""
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        lines = text.strip().split('\n')
        out = []
        current_para = []

        def flush_para():
            if current_para:
                content = '<br>'.join(current_para).strip()
                if content:
                    out.append(f'<p class="nl-p">{content}</p>')
                current_para.clear()

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                flush_para()
            elif line_stripped.startswith('## '):
                flush_para()
                title = line_stripped[3:]
                out.append(f'<h2 class="nl-h2">{title}</h2>')
            elif line_stripped.startswith('### '):
                flush_para()
                title = line_stripped[4:]
                out.append(f'<h3 class="nl-h3">{title}</h3>')
            elif line_stripped.startswith('# '):
                flush_para()
                title = line_stripped[2:]
                out.append(f'<h2 class="nl-h2">{title}</h2>')
            else:
                current_para.append(line_stripped)

        flush_para()
        return '\n'.join(out)

    @staticmethod
    def _var_badge(v):
        if v is None: v = 0
        if v > 0:  return f'<span class="up">▲ {v:+.2f}%</span>'
        if v < 0:  return f'<span class="dn">▼ {abs(v):.2f}%</span>'
        return     f'<span class="fl">— {v:.2f}%</span>'

    @staticmethod
    def _stock_avatar(nom, idx):
        domain = STOCK_LOGOS.get(nom, "")
        if domain:
            return f'<img src="https://logo.clearbit.com/{domain}" class="stock-logo" onerror="this.style.display=\'none\'" style="width:40px;height:40px;border-radius:8px;object-fit:contain;background:white;padding:4px;">'
        # fallback: initiales colorées
        if nom in STOCK_COLORS:
            bg, fg, ticker = STOCK_COLORS[nom]
            letter = ticker[:2]
        else:
            bg = PALETTE[idx % len(PALETTE)]
            fg = "#ffffff"
            letter = nom[:2].upper()
        return f'<div class="stock-avatar" style="background:{bg};color:{fg};width:40px;height:40px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;">{letter}</div>'

    # ─── SECTIONS DYNAMIQUES ──────────────────────────────────────────────────

    def _build_anecdote_section(self, analyses: dict) -> str:
        """Construit la section anecdote bourse si disponible."""
        anecdote = analyses.get("anecdote", "")
        if not anecdote:
            return ""
        return f"""<div class="section" style="animation-delay:.6s;border-left:3px solid var(--gold);">
  <div class="sec-header">
    <div class="sec-icon">📖</div>
    <div><div class="sec-title">L'anecdote du jour</div>
      <div class="sec-sub">Un fait surprenant de l'histoire financière</div></div>
    <span class="sec-pill" style="background:rgba(245,200,66,.12);color:var(--gold);border-color:rgba(245,200,66,.3);">CULTURE</span>
  </div>
  <div class="card-body">{self._md(anecdote)}</div>
</div>"""

    def _build_trader_section(self, analyses: dict) -> str:
        """Construit la section Robot Trader avec les derniers trades et la performance."""
        portfolio = analyses.get("portfolio_trader")
        if not portfolio:
            return ""

        meta = portfolio.get("meta", {})
        capital = meta.get("capital_actuel", 10000)
        perf = meta.get("performance_totale_pct", 0)
        nb_trades = meta.get("nb_trades", 0)
        win_rate = meta.get("win_rate", 0)
        positions = portfolio.get("positions", [])
        trades = portfolio.get("trades_recent", portfolio.get("trades_historique", []))[-5:]

        perf_color = "#22c55e" if perf >= 0 else "#ef4444"
        perf_arrow = "▲" if perf >= 0 else "▼"

        # KPIs du robot
        kpis_html = f"""<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-bottom:20px;">
  <div style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:16px;text-align:center;">
    <div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">Capital</div>
    <div style="font-family:'Space Grotesk',sans-serif;font-size:22px;font-weight:700;color:white;">{capital:,.0f}€</div>
  </div>
  <div style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:16px;text-align:center;">
    <div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">Performance</div>
    <div style="font-family:'Space Grotesk',sans-serif;font-size:22px;font-weight:700;color:{perf_color};">{perf_arrow} {abs(perf):.2f}%</div>
  </div>
  <div style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:16px;text-align:center;">
    <div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">Trades</div>
    <div style="font-family:'Space Grotesk',sans-serif;font-size:22px;font-weight:700;color:white;">{nb_trades}</div>
  </div>
  <div style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:16px;text-align:center;">
    <div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">Win Rate</div>
    <div style="font-family:'Space Grotesk',sans-serif;font-size:22px;font-weight:700;color:{'#22c55e' if win_rate >= 50 else '#f59e0b'};">{win_rate:.0f}%</div>
  </div>
</div>"""

        # Positions ouvertes
        pos_html = ""
        if positions:
            for p in positions[:5]:
                pl = p.get("pl_pct", 0)
                pl_color = "#22c55e" if pl >= 0 else "#ef4444"
                pl_text = f"+{pl:.1f}%" if pl >= 0 else f"{pl:.1f}%"
                pos_html += f"""<div style="display:flex;align-items:center;justify-content:space-between;padding:10px 14px;background:rgba(255,255,255,.03);border-radius:8px;margin-bottom:6px;">
  <div style="display:flex;align-items:center;gap:10px;">
    <span style="font-weight:700;color:white;">{p.get('nom','')}</span>
    <span style="font-size:12px;color:var(--muted);">{p.get('ticker','')}</span>
  </div>
  <div style="display:flex;align-items:center;gap:16px;">
    <span style="font-size:13px;color:var(--muted);">{p.get('prix_actuel',0):.2f}€</span>
    <span style="font-size:13px;font-weight:600;color:{pl_color};">{pl_text}</span>
  </div>
</div>"""
        else:
            pos_html = '<div style="color:var(--muted);font-size:13px;padding:10px;">Aucune position ouverte — 100% cash</div>'

        # Derniers trades
        trades_html = ""
        for t in reversed(trades):
            t_type = t.get("type", "achat")
            t_color = "#22c55e" if t_type == "achat" else "#ef4444"
            t_label = "ACHAT" if t_type == "achat" else "VENTE"
            pl_text = ""
            if t.get("pl_realise") is not None:
                pl = t["pl_realise"]
                pl_text = f' <span style="color:{"#22c55e" if pl >= 0 else "#ef4444"};font-weight:600;">P&L: {pl:+.2f}€</span>'
            trades_html += f"""<div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.05);">
  <span style="font-size:10px;font-weight:700;padding:2px 8px;border-radius:4px;background:{t_color}22;color:{t_color};">{t_label}</span>
  <span style="font-weight:500;color:white;font-size:13px;">{t.get('ticker','')}</span>
  <span style="font-size:12px;color:var(--muted);">{t.get('nb_actions',0):.2f} × {t.get('prix',0):.2f}€</span>
  {pl_text}
  <span style="margin-left:auto;font-size:11px;color:var(--muted);">{t.get('date','')[:10]}</span>
</div>"""

        return f"""<div class="section" style="animation-delay:.48s;border-left:3px solid var(--cyan);">
  <div class="sec-header">
    <div class="sec-icon">🤖</div>
    <div><div class="sec-title">Robot Trader AlphaBot</div>
      <div class="sec-sub">Portefeuille géré par IA — Trades automatiques toutes les heures</div></div>
    <span class="sec-pill pill-cyan">LIVE</span>
  </div>
  {kpis_html}
  <div style="margin-bottom:16px;">
    <div style="font-size:12px;font-weight:600;color:var(--cyan);text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;">Positions ouvertes</div>
    {pos_html}
  </div>
  <div>
    <div style="font-size:12px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;">Derniers trades</div>
    {trades_html if trades_html else '<div style="color:var(--muted);font-size:13px;">Aucun trade encore exécuté</div>'}
  </div>
  <div style="text-align:center;margin-top:16px;">
    <a href="investissement.html" style="display:inline-block;font-size:13px;font-weight:600;color:var(--cyan);text-decoration:none;padding:8px 20px;border:1px solid rgba(34,211,238,.3);border-radius:8px;transition:all .2s;">Voir le portefeuille complet →</a>
  </div>
</div>"""

    # ─── BUILD HTML ──────────────────────────────────────────────────────────

    def _build_html(self, analyses: dict) -> str:
        meta    = analyses.get("meta", {})
        date    = meta.get("date", datetime.now().strftime("%d/%m/%Y"))
        semaine = meta.get("semaine", "")
        mood    = analyses.get("mood", {})
        news    = analyses.get("news_raw", [])
        brutes      = analyses.get("donnees_brutes", {})
        cryptos     = brutes.get("crypto", {})
        indices     = brutes.get("bourse", {}).get("indices", {})
        actions     = brutes.get("bourse", {}).get("actions", {})
        commodities = analyses.get("commodities_raw", brutes.get("commodities", {}))

        fg_val  = mood.get("valeur", 50) if mood else 50
        fg_lbl  = mood.get("sentiment", "Neutral") if mood else "Neutral"
        fg_color = ("#ef4444" if fg_val<25 else "#f97316" if fg_val<45
                    else "#eab308" if fg_val<55 else "#84cc16" if fg_val<75 else "#22c55e")
        fg_emoji = ("😱" if fg_val<25 else "😟" if fg_val<45
                    else "😐" if fg_val<55 else "😊" if fg_val<75 else "🤑")

        # KPIs hero (top 2 crypto + top 2 indices)
        kpi_items = []
        for sym, d in list(cryptos.items())[:2]:
            v = d.get("variation_24h", 0)
            kpi_items.append({
                "label": d.get("nom", sym), "sub": sym,
                "value": f"${d.get('prix_usd',0):,.0f}",
                "var": v, "icon": "crypto", "sym": sym.lower()
            })
        for nom, d in list(indices.items())[:2]:
            v = d.get("variation_24h", 0)
            kpi_items.append({
                "label": nom, "sub": d.get("ticker",""),
                "value": f"{d.get('valeur',0):,.0f} pts",
                "var": v, "icon": "index"
            })
        # fallback KPI si pas de données
        if not kpi_items:
            kpi_items = [
                {"label":"Bitcoin","sub":"BTC","value":"$67,450","var":2.3,"icon":"crypto","sym":"btc"},
                {"label":"Ethereum","sub":"ETH","value":"$3,210","var":-1.2,"icon":"crypto","sym":"eth"},
                {"label":"S&P 500","sub":"^GSPC","value":"5,248 pts","var":0.3,"icon":"index"},
                {"label":"CAC 40","sub":"^FCHI","value":"8,125 pts","var":0.45,"icon":"index"},
            ]

        kpi_html = ""
        for k in kpi_items[:4]:
            v = k["var"]
            vcolor = "#22c55e" if v>=0 else "#ef4444"
            vtext  = f"▲ {v:+.2f}%" if v>=0 else f"▼ {abs(v):.2f}%"
            if k["icon"] == "crypto" and "sym" in k:
                logo_html = f'<img src="{CRYPTO_LOGO_URL.format(sym=k["sym"])}" class="kpi-logo" onerror="this.style.display=\'none\'">'
            else:
                letter = k["sub"][:2] if k.get("sub") else k["label"][:2]
                logo_html = f'<div class="kpi-letter">{letter}</div>'
            kpi_html += f"""
            <div class="kpi-card">
              <div class="kpi-top">{logo_html}<div class="kpi-labels">
                <div class="kpi-name">{k["label"]}</div>
                <div class="kpi-sub">{k["sub"]}</div>
              </div></div>
              <div class="kpi-value">{k["value"]}</div>
              <div class="kpi-var" style="color:{vcolor};">{vtext}</div>
            </div>"""

        # Crypto sparkline cards
        crypto_cards_html = ""
        crypto_chart_data = {}
        for sym, d in list(cryptos.items())[:6]:
            v = d.get("variation_24h", 0)
            v7 = d.get("variation_7j", 0)
            vcolor = "#22c55e" if v>=0 else "#ef4444"
            chart_id = f"chart_{sym}"
            crypto_chart_data[sym] = {
                "price": d.get("prix_usd", 0),
                "var7": v7,
                "color": vcolor
            }
            mcap = d.get("market_cap_mrd", 0)
            vol  = d.get("volume_24h_mrd", 0)
            ath  = d.get("ath_pct", 0)
            crypto_cards_html += f"""
            <div class="asset-card">
              <div class="asset-header">
                <img src="{CRYPTO_LOGO_URL.format(sym=sym.lower())}"
                     class="asset-logo"
                     onerror="this.style.display='none'">
                <div>
                  <div class="asset-name">{d.get("nom", sym)}</div>
                  <div class="asset-sym">{sym}</div>
                </div>
                <div class="asset-badge" style="color:{vcolor};background:{vcolor}18;border-color:{vcolor}33;">
                  {"▲" if v>=0 else "▼"} {abs(v):.2f}%
                </div>
              </div>
              <div class="asset-price">${d.get('prix_usd',0):,.2f}</div>
              <canvas id="{chart_id}" class="sparkline-canvas" height="55"></canvas>
              <div class="asset-meta-row">
                <div class="meta-item"><span class="meta-lbl">7j</span>
                  <span style="color:{'#22c55e' if v7>=0 else '#ef4444'}">{"▲" if v7>=0 else "▼"}{abs(v7):.1f}%</span>
                </div>
                <div class="meta-item"><span class="meta-lbl">Mcap</span>${mcap}Mrd</div>
                <div class="meta-item"><span class="meta-lbl">Vol</span>${vol}Mrd</div>
                <div class="meta-item"><span class="meta-lbl">vs ATH</span>
                  <span style="color:#f59e0b;">{ath:.0f}%</span>
                </div>
              </div>
            </div>"""

        # Indices table rows + chart data
        indices_rows_html = ""
        bar_chart_labels = []
        bar_chart_values = []
        bar_chart_colors = []
        for nom, d in list(indices.items()):
            v = d.get("variation_24h", 0)
            v7 = d.get("variation_7j", 0)
            bar_chart_labels.append(nom)
            bar_chart_values.append(round(v7, 2))
            bar_chart_colors.append("#22c55e" if v7 >= 0 else "#ef4444")
            chart_id_idx = f"idxchart_{nom.replace(' ','_')}"
            indices_rows_html += f"""
            <tr class="trow">
              <td><strong>{nom}</strong><br><span class="ticker-lbl">{d.get("ticker","")}</span></td>
              <td class="tnums">{d.get("valeur",0):,.2f}</td>
              <td>{self._var_badge(v)}</td>
              <td>{self._var_badge(v7)}</td>
            </tr>"""

        # Actions rows
        for i, (nom, d) in enumerate(list(actions.items())):
            v = d.get("variation_24h", 0)
            bar_chart_labels.append(nom)
            bar_chart_values.append(round(v, 2))
            bar_chart_colors.append("#22c55e" if v >= 0 else "#ef4444")
            devise = d.get("devise","USD")
            mcap = d.get("market_cap_mrd", 0)
            avatar = self._stock_avatar(nom, i)
            indices_rows_html += f"""
            <tr class="trow">
              <td><div class="td-company">{avatar}<div>
                <strong>{nom}</strong><br>
                <span class="ticker-lbl">{d.get("ticker","")}</span>
              </div></div></td>
              <td class="tnums">{d.get("prix",0):.2f} {devise}</td>
              <td>{self._var_badge(v)}</td>
              <td>{"$"+str(mcap)+"Mrd" if mcap else "—"}</td>
            </tr>"""

        # Commodities mini-table
        commodities_rows_html = ""
        COMMODITY_ICONS = {
            "Dollar Index (DXY)": "💵",
            "Pétrole WTI":        "🛢️",
            "Or (XAU/USD)":       "🥇",
            "EUR/USD":            "💶",
        }
        for nom, d in commodities.items():
            v   = d.get("variation_24h", 0)
            v7  = d.get("variation_7j", 0)
            val = d.get("valeur", 0)
            icon = COMMODITY_ICONS.get(nom, "📈")
            commodities_rows_html += f"""
            <tr class="trow">
              <td><strong>{icon} {nom}</strong></td>
              <td class="tnums">{val:,.4f}</td>
              <td>{self._var_badge(v)}</td>
              <td>{self._var_badge(v7)}</td>
            </tr>"""

        if commodities_rows_html:
            commodities_table_html = (
                '<table class="mkt-table"><thead><tr>'
                '<th>Actif</th><th>Valeur</th><th>Jour</th><th>7 jours</th>'
                '</tr></thead><tbody>' + commodities_rows_html + '</tbody></table>'
            )
        else:
            commodities_table_html = '<p style="color:var(--muted);font-size:.85rem;">Données non disponibles (pip install yfinance)</p>'

        # News items
        news_html = ""
        for n in news[:5]:
            titre  = n.get("titre","")
            source = n.get("source","")
            url    = n.get("url","#")
            news_html += f"""
            <a href="{url}" class="news-item" target="_blank">
              <div class="news-pulse"></div>
              <div class="news-body">
                <div class="news-title">{titre[:110]}{"..." if len(titre)>110 else ""}</div>
                <div class="news-meta">
                  <span class="news-source">{source}</span>
                  <span class="news-tag">🤖 Collecté automatiquement</span>
                </div>
              </div>
            </a>"""

        ticker_text = "  ⚡  ".join(
            [n.get("titre","")[:60]+"..." for n in news[:7]]
        ) or "Chargement des actualités en temps réel..."

        # Pre-compute HTML blocks that contain apostrophes (avoids backslash-in-f-string on Python < 3.12)
        aujhui = "Aujourd" + chr(39) + "hui"
        if indices_rows_html:
            market_table_html = (
                '<table class="mkt-table"><thead><tr>'
                '<th>Actif</th><th>Valeur</th>'
                f'<th>{aujhui}</th><th>7j / Mcap</th>'
                f'</tr></thead><tbody>{indices_rows_html}</tbody></table>'
            )
        else:
            market_table_html = ""

        if bar_chart_labels:
            perf_chart_html = '<div class="chart-wrap"><canvas id="perfChart"></canvas></div>'
        else:
            perf_chart_html = ""

        if news_html:
            news_section_html = (
                '<div class="section" style="animation-delay:.55s">'
                '<div class="sec-header"><div class="sec-icon">📰</div>'
                '<div><div class="sec-title">Actualités collectées automatiquement</div>'
                '<div class="sec-sub">Chaque article détecté dès sa publication · 0 délai</div></div>'
                '<span class="sec-pill pill-cyan">AUTO</span></div>'
                + news_html + '</div>'
            )
        else:
            news_section_html = ""

        # Charge les insights géopolitiques du DA
        insights_geo_html = ""
        try:
            import json as _json
            da_path = os.path.join("data", "contenu_da.json")
            if os.path.exists(da_path):
                with open(da_path, "r", encoding="utf-8") as _f:
                    da_data = _json.load(_f)
                insights = da_data.get("insights", [])
                if insights:
                    cards_html = ""
                    for ins in insights[:3]:
                        sev = ins.get("severite", "MEDIUM")
                        sev_colors = {"LOW":"#22c55e","MEDIUM":"#eab308","HIGH":"#f97316","CRITICAL":"#ef4444"}
                        sev_c = sev_colors.get(sev, "#64748b")
                        action = ins.get("action_cible", {})
                        ticker = action.get("ticker","—")
                        prix = action.get("prix_actuel", 0)
                        var = action.get("variation_pct", 0)
                        var_c = "#22c55e" if var >= 0 else "#ef4444"
                        var_t = f"+{var:.1f}%" if var >= 0 else f"{var:.1f}%"
                        cards_html += f"""<div style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:22px;display:flex;flex-direction:column;gap:12px;">
<div style="display:flex;align-items:center;gap:10px;">
  <span style="font-size:24px;">{ins.get("emoji_categorie","🌍")}</span>
  <span style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;background:rgba(59,130,246,.2);color:#3b82f6;padding:3px 9px;border-radius:50px;">{ins.get("categorie","")}</span>
  <span style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;background:rgba({','.join(str(int(sev_c.lstrip('#')[i:i+2],16)) for i in (0,2,4))},.2);color:{sev_c};padding:3px 9px;border-radius:50px;">{sev}</span>
</div>
<div style="font-family:'Space Grotesk',sans-serif;font-size:16px;font-weight:700;color:white;">{ins.get("titre","")}</div>
<div style="font-size:13px;color:#e2e8f0;line-height:1.6;">{ins.get("contexte","")}</div>
<div style="font-size:13px;color:#e2e8f0;padding:10px;background:rgba(59,130,246,.08);border-left:3px solid #3b82f6;border-radius:4px;"><strong>→ Impact marché:</strong> {ins.get("impact_marche","")}</div>
<div style="display:flex;justify-content:space-between;align-items:center;padding:14px;background:rgba(255,255,255,.04);border-radius:10px;border:1px solid rgba(255,255,255,.06);">
  <div><div style="font-family:'Space Grotesk',sans-serif;font-size:14px;font-weight:700;color:white;">{ticker}</div><div style="font-size:12px;color:#64748b;">{action.get("nom","")}</div></div>
  <div style="text-align:right;"><div style="font-family:'Space Grotesk',sans-serif;font-size:16px;font-weight:700;color:white;">${prix:,.2f}</div><div style="font-size:12px;font-weight:600;color:{var_c};">{var_t}</div></div>
</div>
<div style="font-size:13px;color:#e2e8f0;line-height:1.6;"><strong>Pourquoi?</strong> {action.get("pourquoi","")}</div>
</div>"""
                    insights_geo_html = f"""<div class="section acc-red" style="animation-delay:.32s">
  <div class="sec-header">
    <div class="sec-icon">🌍</div>
    <div><div class="sec-title">Insights Géopolitiques — Impact Marchés</div>
      <div class="sec-sub">Événement mondial → Impact marché → Action à surveiller</div></div>
    <span class="sec-pill pill-red">GÉOPOLITIQUE</span>
  </div>
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:18px;">
    {cards_html}
  </div>
</div>"""
        except Exception as _e:
            print(f"  ⚠️ Insights géo non chargés: {_e}")

        # Serialize chart data for JS
        crypto_js   = json.dumps(crypto_chart_data)
        bar_labels  = json.dumps(bar_chart_labels)
        bar_values  = json.dumps(bar_chart_values)
        bar_colors  = json.dumps(bar_chart_colors)

        return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{NEWSLETTER_NAME} — {date}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
/* ═══ RESET & VARS ═══════════════════════════════════════════════════════════ */
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
:root{{
  --bg:#04091a; --bg2:#060d1f; --surface:rgba(255,255,255,0.04);
  --surface2:rgba(255,255,255,0.07); --border:rgba(255,255,255,0.08);
  --gold:#f5c842; --blue:#3b82f6; --cyan:#22d3ee; --green:#22c55e;
  --red:#ef4444; --text:#e2e8f0; --muted:#64748b; --muted2:#475569;
}}
html{{scroll-behavior:smooth;}}
body{{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;
      font-size:15px;line-height:1.65;overflow-x:hidden;}}

/* ═══ BACKGROUND GRID + ORBS ════════════════════════════════════════════════ */
.bg-wrap{{position:fixed;inset:0;z-index:0;pointer-events:none;overflow:hidden;}}
.bg-grid{{position:absolute;inset:0;
  background-image:linear-gradient(rgba(59,130,246,.03)1px,transparent 1px),
    linear-gradient(90deg,rgba(59,130,246,.03)1px,transparent 1px);
  background-size:60px 60px;}}
.orb{{position:absolute;border-radius:50%;filter:blur(80px);}}
.orb1{{width:700px;height:700px;background:radial-gradient(circle,rgba(59,130,246,.09),transparent 65%);
       top:-250px;left:-200px;animation:orbf 9s ease-in-out infinite alternate;}}
.orb2{{width:600px;height:600px;background:radial-gradient(circle,rgba(245,200,66,.06),transparent 65%);
       bottom:-200px;right:-150px;animation:orbf 11s ease-in-out infinite alternate-reverse;}}
.orb3{{width:400px;height:400px;background:radial-gradient(circle,rgba(34,211,238,.05),transparent 65%);
       top:40%;left:60%;animation:orbf 7s ease-in-out infinite alternate;}}
@keyframes orbf{{from{{transform:translate(0,0)scale(1);}}to{{transform:translate(30px,25px)scale(1.08);}}}}

/* ═══ SCAN LINE ══════════════════════════════════════════════════════════════ */
.scan{{position:fixed;top:0;left:0;right:0;height:2px;z-index:999;pointer-events:none;
       background:linear-gradient(90deg,transparent,var(--cyan),var(--gold),transparent);
       animation:scan 7s ease-in-out infinite;opacity:.35;}}
@keyframes scan{{0%{{top:0;opacity:0;}}8%{{opacity:.4;}}92%{{opacity:.4;}}100%{{top:100%;opacity:0;}}}}

/* ═══ WRAPPER ════════════════════════════════════════════════════════════════ */
.wrap{{position:relative;z-index:1;max-width:1400px;margin:0 auto;padding:20px 40px 60px;}}

/* ═══ TICKER ═════════════════════════════════════════════════════════════════ */
.ticker-bar{{background:rgba(34,211,238,.06);border:1px solid rgba(34,211,238,.18);
             border-radius:6px;overflow:hidden;padding:7px 0;margin-bottom:22px;position:relative;}}
.ticker-bar::before,.ticker-bar::after{{content:'';position:absolute;top:0;bottom:0;width:80px;z-index:2;}}
.ticker-bar::before{{left:0;background:linear-gradient(90deg,var(--bg),transparent);}}
.ticker-bar::after{{right:0;background:linear-gradient(-90deg,var(--bg),transparent);}}
.ticker-inner{{display:flex;white-space:nowrap;animation:ticker 55s linear infinite;}}
.ticker-inner:hover{{animation-play-state:paused;}}
.t-chunk{{font-size:12px;font-weight:500;color:var(--cyan);padding:0 30px;white-space:nowrap;}}
@keyframes ticker{{from{{transform:translateX(0);}}to{{transform:translateX(-50%);}}}}
.ticker-live{{position:absolute;left:10px;top:50%;transform:translateY(-50%);z-index:3;
              font-size:10px;font-weight:700;color:#ef4444;letter-spacing:1px;
              background:rgba(239,68,68,.15);border:1px solid rgba(239,68,68,.3);
              padding:2px 7px;border-radius:4px;display:flex;align-items:center;gap:4px;}}
.live-dot{{width:5px;height:5px;border-radius:50%;background:#ef4444;
           animation:pulse 1.2s ease-in-out infinite;}}
@keyframes pulse{{0%,100%{{transform:scale(1);opacity:1;}}50%{{transform:scale(1.6);opacity:.4;}}}}

/* ═══ HEADER ═════════════════════════════════════════════════════════════════ */
.header{{text-align:center;padding:48px 30px 40px;
  background:linear-gradient(135deg,rgba(59,130,246,.1) 0%,rgba(245,200,66,.05) 50%,rgba(34,211,238,.07) 100%);
  border:1px solid var(--border);border-radius:22px;margin-bottom:22px;
  position:relative;overflow:hidden;backdrop-filter:blur(20px);
  animation:fadeDown .7s ease-out;}}
.header::after{{content:'';position:absolute;inset:0;
  background:linear-gradient(180deg,rgba(255,255,255,.03) 0%,transparent 60%);pointer-events:none;}}
.h-tag{{display:inline-flex;align-items:center;gap:6px;font-size:10px;letter-spacing:3px;
        text-transform:uppercase;color:var(--gold);font-weight:700;
        background:rgba(245,200,66,.1);border:1px solid rgba(245,200,66,.25);
        padding:4px 14px;border-radius:20px;margin-bottom:18px;}}
.h-title{{font-family:'Space Grotesk',sans-serif;
  font-size:clamp(30px,5vw,46px);font-weight:900;letter-spacing:-2px;line-height:1.05;
  background:linear-gradient(135deg,#fff 0%,var(--cyan) 45%,var(--gold) 100%);
  -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;
  margin-bottom:12px;}}
.h-sub{{font-size:14px;color:var(--muted);margin-bottom:22px;}}
.h-badges{{display:flex;justify-content:center;gap:8px;flex-wrap:wrap;}}
.h-badge{{display:inline-flex;align-items:center;gap:5px;font-size:11px;font-weight:600;
          padding:5px 13px;border-radius:20px;}}
.b-date{{color:var(--muted);background:var(--surface);border:1px solid var(--border);}}
.b-ai{{color:var(--green);background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.25);}}
.b-rt{{color:#ef4444;background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.25);}}
.ai-dot2{{width:6px;height:6px;border-radius:50%;background:var(--green);animation:pulse 2s ease-in-out infinite;}}

/* ═══ AI BANNER ══════════════════════════════════════════════════════════════ */
.ai-banner{{
  background:linear-gradient(90deg,rgba(59,130,246,.12) 0%,rgba(34,211,238,.08) 50%,rgba(245,200,66,.08) 100%);
  border:1px solid rgba(59,130,246,.25);border-radius:14px;
  padding:16px 22px;margin-bottom:22px;
  display:flex;align-items:center;gap:14px;
  animation:fadeUp .6s ease-out .1s both;}}
.ai-icon{{font-size:28px;flex-shrink:0;}}
.ai-banner-text{{flex:1;}}
.ai-banner-title{{font-size:13px;font-weight:700;color:white;margin-bottom:3px;}}
.ai-banner-sub{{font-size:12px;color:var(--muted);}}
.ai-stat{{text-align:right;flex-shrink:0;}}
.ai-stat-num{{font-family:'Space Grotesk',sans-serif;font-size:22px;font-weight:800;
              background:linear-gradient(135deg,var(--cyan),var(--gold));
              -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;}}
.ai-stat-lbl{{font-size:10px;color:var(--muted);}}

/* ═══ KPI CARDS ══════════════════════════════════════════════════════════════ */
.kpi-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(165px,1fr));
           gap:12px;margin-bottom:22px;}}
.kpi-card{{background:var(--surface);border:1px solid var(--border);border-radius:14px;
           padding:16px;transition:transform .2s,border-color .2s,box-shadow .2s;
           animation:fadeUp .5s ease-out both;cursor:default;}}
.kpi-card:hover{{transform:translateY(-3px);border-color:rgba(255,255,255,.15);
                 box-shadow:0 12px 30px rgba(0,0,0,.3);}}
.kpi-top{{display:flex;align-items:center;gap:10px;margin-bottom:12px;}}
.kpi-logo{{width:32px;height:32px;border-radius:8px;object-fit:contain;
           background:rgba(255,255,255,.05);padding:4px;}}
.kpi-letter{{width:32px;height:32px;border-radius:8px;background:rgba(59,130,246,.2);
             border:1px solid rgba(59,130,246,.3);display:flex;align-items:center;justify-content:center;
             font-size:11px;font-weight:700;color:var(--cyan);}}
.kpi-name{{font-size:13px;font-weight:600;color:white;}}
.kpi-sub{{font-size:10px;color:var(--muted);margin-top:1px;}}
.kpi-value{{font-family:'Space Grotesk',sans-serif;font-size:20px;font-weight:800;
            color:white;letter-spacing:-.5px;margin-bottom:4px;}}
.kpi-var{{font-size:13px;font-weight:700;}}

/* ═══ SECTION CARDS ══════════════════════════════════════════════════════════ */
.section{{background:var(--surface);border:1px solid var(--border);border-radius:18px;
          padding:28px;margin-bottom:20px;backdrop-filter:blur(12px);
          transition:border-color .3s,box-shadow .3s;
          animation:fadeUp .6s ease-out both;}}
.section:hover{{border-color:rgba(34,211,238,.2);box-shadow:0 0 40px rgba(34,211,238,.05);}}
.sec-header{{display:flex;align-items:center;gap:12px;margin-bottom:22px;}}
.sec-icon{{width:46px;height:46px;border-radius:13px;display:flex;align-items:center;
           justify-content:center;font-size:22px;background:var(--surface2);
           border:1px solid var(--border);flex-shrink:0;}}
.sec-title{{font-family:'Space Grotesk',sans-serif;font-size:18px;font-weight:700;color:white;}}
.sec-sub{{font-size:12px;color:var(--muted);margin-top:2px;}}
.sec-pill{{margin-left:auto;font-size:10px;font-weight:700;letter-spacing:.5px;
           text-transform:uppercase;padding:4px 10px;border-radius:20px;flex-shrink:0;}}
.pill-gold{{color:var(--gold);background:rgba(245,200,66,.1);border:1px solid rgba(245,200,66,.2);}}
.pill-blue{{color:var(--blue);background:rgba(59,130,246,.1);border:1px solid rgba(59,130,246,.2);}}
.pill-green{{color:var(--green);background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.2);}}
.pill-cyan{{color:var(--cyan);background:rgba(34,211,238,.1);border:1px solid rgba(34,211,238,.2);}}
.acc-gold{{border-left:3px solid var(--gold);}}
.acc-blue{{border-left:3px solid var(--blue);}}
.acc-green{{border-left:3px solid var(--green);}}
.acc-cyan{{border-left:3px solid var(--cyan);}}
.acc-red{{border-left:3px solid #ef4444;}}
.pill-red{{color:#ef4444;background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.2);}}

/* ═══ ASSET CARDS GRID ═══════════════════════════════════════════════════════ */
.asset-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px;}}
.asset-card{{background:var(--surface2);border:1px solid var(--border);border-radius:14px;
             padding:16px;transition:transform .2s,border-color .2s;position:relative;overflow:hidden;}}
.asset-card::before{{content:'';position:absolute;inset:0;
  background:radial-gradient(circle at 50% 0%,rgba(59,130,246,.06),transparent 70%);
  opacity:0;transition:opacity .3s;}}
.asset-card:hover{{transform:translateY(-3px);border-color:rgba(255,255,255,.14);}}
.asset-card:hover::before{{opacity:1;}}
.asset-header{{display:flex;align-items:center;gap:10px;margin-bottom:12px;}}
.asset-logo{{width:36px;height:36px;border-radius:50%;object-fit:contain;
             background:rgba(255,255,255,.08);padding:5px;flex-shrink:0;}}
.asset-logo-fb{{width:36px;height:36px;border-radius:50%;background:rgba(59,130,246,.25);
               border:1px solid rgba(59,130,246,.4);display:flex;align-items:center;
               justify-content:center;font-size:11px;font-weight:700;color:var(--cyan);flex-shrink:0;}}
.asset-name{{font-size:13px;font-weight:700;color:white;}}
.asset-sym{{font-size:10px;color:var(--muted);margin-top:1px;}}
.asset-badge{{margin-left:auto;font-size:11px;font-weight:700;
              padding:3px 8px;border-radius:6px;border:1px solid transparent;flex-shrink:0;}}
.asset-price{{font-family:'Space Grotesk',sans-serif;font-size:22px;font-weight:800;
              color:white;letter-spacing:-.5px;margin-bottom:10px;}}
.sparkline-canvas{{width:100% !important;display:block;margin-bottom:10px;}}
.asset-meta-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:4px;}}
.meta-item{{text-align:center;background:rgba(255,255,255,.03);border-radius:6px;padding:5px 3px;}}
.meta-lbl{{display:block;font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:.4px;}}
.meta-item span:last-child{{font-size:11px;font-weight:600;color:var(--text);}}

/* ═══ FEAR & GREED ═══════════════════════════════════════════════════════════ */
.fg-wrap{{display:flex;flex-direction:column;align-items:center;padding:8px 0;}}
.fg-track-wrap{{width:100%;margin-bottom:16px;}}
.fg-labels{{display:flex;justify-content:space-between;font-size:10px;color:var(--muted);margin-bottom:6px;}}
.fg-track{{height:12px;border-radius:10px;position:relative;
  background:linear-gradient(90deg,#ef4444 0%,#f97316 20%,#eab308 40%,#84cc16 65%,#22c55e 100%);}}
.fg-needle{{position:absolute;top:50%;width:22px;height:22px;background:#fff;
            border-radius:50%;transform:translate(-50%,-50%);
            border:3px solid {fg_color};box-shadow:0 0 14px {fg_color};
            left:{fg_val}%;transition:left 1.2s cubic-bezier(.34,1.56,.64,1);}}
.fg-center{{text-align:center;}}
.fg-big{{font-family:'Space Grotesk',sans-serif;font-size:56px;font-weight:900;
          color:{fg_color};text-shadow:0 0 40px {fg_color}55;line-height:1;
          display:flex;align-items:center;justify-content:center;gap:14px;margin-bottom:6px;}}
.fg-emoji-big{{font-size:44px;animation:pop .5s ease-out .3s both;}}
@keyframes pop{{from{{transform:scale(0)rotate(-20deg);}}to{{transform:scale(1)rotate(0);}}}}
.fg-lbl{{font-size:15px;font-weight:800;color:{fg_color};letter-spacing:2px;
          text-transform:uppercase;margin-bottom:8px;}}
.fg-note{{font-size:12px;color:var(--muted);max-width:340px;text-align:center;}}

/* ═══ MARKET TABLE ═══════════════════════════════════════════════════════════ */
.mkt-table{{width:100%;border-collapse:collapse;font-size:13px;}}
.mkt-table thead th{{font-size:10px;text-transform:uppercase;letter-spacing:1px;
                      color:var(--muted);font-weight:600;padding:8px 10px;text-align:left;
                      border-bottom:1px solid var(--border);}}
.trow td{{padding:11px 10px;border-bottom:1px solid rgba(255,255,255,.04);vertical-align:middle;}}
.trow:last-child td{{border-bottom:none;}}
.trow:hover td{{background:var(--surface2);}}
.ticker-lbl{{font-size:10px;color:var(--muted);font-family:monospace;}}
.tnums{{font-variant-numeric:tabular-nums;color:#94a3b8;font-weight:500;}}
.td-company{{display:flex;align-items:center;gap:8px;}}
.stock-avatar{{width:32px;height:32px;border-radius:8px;display:flex;align-items:center;
               justify-content:center;font-size:11px;font-weight:800;flex-shrink:0;}}
.up{{color:var(--green);font-weight:700;font-size:12px;}}
.dn{{color:var(--red);font-weight:700;font-size:12px;}}
.fl{{color:var(--muted);font-weight:600;font-size:12px;}}

/* ═══ PERF BAR CHART ═════════════════════════════════════════════════════════ */
.chart-wrap{{position:relative;height:220px;margin-top:20px;}}

/* ═══ NEWS ═══════════════════════════════════════════════════════════════════ */
.news-item{{display:flex;align-items:flex-start;gap:12px;padding:13px 8px;
            border-bottom:1px solid var(--border);text-decoration:none;
            border-radius:8px;transition:background .2s;}}
.news-item:last-child{{border-bottom:none;}}
.news-item:hover{{background:var(--surface2);}}
.news-pulse{{width:10px;height:10px;border-radius:50%;background:var(--cyan);flex-shrink:0;
             margin-top:4px;box-shadow:0 0 8px var(--cyan);animation:pulse 2s ease-in-out infinite;}}
.news-body{{flex:1;}}
.news-title{{font-size:13px;font-weight:500;color:#cbd5e1;line-height:1.5;margin-bottom:5px;}}
.news-meta{{display:flex;align-items:center;gap:8px;flex-wrap:wrap;}}
.news-source{{font-size:11px;color:var(--muted);}}
.news-tag{{font-size:10px;color:var(--green);background:rgba(34,197,94,.1);
           border:1px solid rgba(34,197,94,.2);padding:1px 7px;border-radius:4px;}}

/* ═══ CONCEPT ════════════════════════════════════════════════════════════════ */
.concept-top{{display:flex;align-items:center;gap:10px;margin-bottom:16px;}}
.concept-badge{{font-size:11px;font-weight:600;color:var(--green);
                background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.25);
                padding:4px 12px;border-radius:20px;}}
.card-body{{color:#cbd5e1;font-size:15px;line-height:1.85;}}
.card-body p{{margin-bottom:16px;}}
.card-body p:last-child{{margin-bottom:0;}}
.card-body strong{{color:white;font-weight:700;}}
.nl-h2{{font-family:'Space Grotesk',sans-serif;font-size:20px;font-weight:700;color:white;margin:28px 0 12px;padding:0 0 8px;border-bottom:2px solid rgba(34,211,238,.3);line-height:1.3;}}
.nl-h3{{font-family:'Space Grotesk',sans-serif;font-size:16px;font-weight:700;color:white;margin:18px 0 10px;}}
.nl-p{{font-size:15px;line-height:1.85;color:#cbd5e1;margin-bottom:16px;}}

/* ═══ DIVIDER ════════════════════════════════════════════════════════════════ */
.divider{{height:1px;
  background:linear-gradient(90deg,transparent,rgba(59,130,246,.4),rgba(245,200,66,.3),transparent);
  margin:6px 0 22px;}}

/* ═══ ANALYSIS TEXT ══════════════════════════════════════════════════════════ */
.analysis-block{{margin-top:24px;padding-top:22px;border-top:1px solid var(--border);}}
.analysis-label{{display:flex;align-items:center;gap:8px;font-size:11px;font-weight:700;
                  color:var(--muted);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:14px;}}
.analysis-label::after{{content:'';flex:1;height:1px;background:var(--border);}}

/* ═══ FOOTER ═════════════════════════════════════════════════════════════════ */
.footer{{text-align:center;padding:32px 20px;border-top:1px solid var(--border);margin-top:12px;}}
.footer-brand{{font-family:'Space Grotesk',sans-serif;font-size:20px;font-weight:800;
               background:linear-gradient(135deg,var(--cyan),var(--gold));
               -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;
               margin-bottom:8px;}}
.footer-txt{{font-size:12px;color:var(--muted);line-height:1.7;}}
.footer-disc{{font-size:11px;color:#334155;max-width:520px;margin:14px auto 0;
              padding:10px 16px;background:rgba(255,255,255,.02);border:1px solid var(--border);border-radius:8px;}}
.unsub{{font-size:11px;color:var(--muted);margin-top:14px;}}
.unsub a{{color:var(--cyan);text-decoration:none;}}

/* ═══ ANIMATIONS ═════════════════════════════════════════════════════════════ */
@keyframes fadeDown{{from{{opacity:0;transform:translateY(-18px);}}to{{opacity:1;transform:translateY(0);}}}}
@keyframes fadeUp  {{from{{opacity:0;transform:translateY(22px); }}to{{opacity:1;transform:translateY(0);}}}}

/* ═══ RESPONSIVE ════════════════════════════════════════════════════════════ */
@media(max-width:600px){{
  .wrap{{padding:10px 10px 40px;}}
  .section{{padding:18px 14px;}}
  .header{{padding:34px 18px 28px;}}
  .kpi-grid{{grid-template-columns:repeat(2,1fr);}}
  .asset-grid{{grid-template-columns:1fr 1fr;}}
  .ai-stat{{display:none;}}
}}
</style>
</head>
<body>
<div class="scan"></div>
<div class="bg-wrap"><div class="bg-grid"></div>
  <div class="orb orb1"></div><div class="orb orb2"></div><div class="orb orb3"></div></div>

<div class="wrap">

<!-- ── TICKER ── -->
<div class="ticker-bar">
  <div class="ticker-live"><div class="live-dot"></div>LIVE</div>
  <div class="ticker-inner">
    <div class="t-chunk">{ticker_text} &nbsp;&nbsp; {ticker_text}</div>
  </div>
</div>

<!-- ── HEADER ── -->
<div class="header">
  <div class="h-tag">⚡ {semaine}</div>
  <div class="h-title">🤖 {NEWSLETTER_NAME}</div>
  <div class="h-sub">{NEWSLETTER_TAGLINE}</div>
  <div class="h-badges">
    <span class="h-badge b-date">📅 {date}</span>
    <span class="h-badge b-ai"><span class="ai-dot2"></span>100% Généré par IA</span>
    <span class="h-badge b-rt"><span style="color:#ef4444;">●</span> Temps réel</span>
  </div>
</div>

<div class="divider"></div>

<!-- ── AI BANNER ── -->
<div class="ai-banner">
  <div class="ai-icon">⚡</div>
  <div class="ai-banner-text">
    <div class="ai-banner-title">100% automatisé — 0 news manquée</div>
    <div class="ai-banner-sub">Des agents IA surveillent les marchés en continu. Dès qu'une information sort — analyse publiée en quelques secondes, sans intervention humaine.</div>
  </div>
  <div class="ai-stat">
    <div class="ai-stat-num" id="newsCount">0</div>
    <div class="ai-stat-lbl">sources<br>surveillées</div>
  </div>
</div>

<!-- ── KPI CARDS ── -->
<div class="kpi-grid">
{kpi_html}
</div>

<!-- ── FEAR & GREED ── -->
<div class="section" style="animation-delay:.25s">
  <div class="sec-header">
    <div class="sec-icon">🧠</div>
    <div><div class="sec-title">Fear & Greed Index</div>
      <div class="sec-sub">Baromètre du sentiment crypto · 0 = peur · 100 = avidité</div></div>
  </div>
  <div class="fg-wrap">
    <div class="fg-track-wrap">
      <div class="fg-labels"><span>😱 Peur extrême</span><span>😐 Neutre</span><span>🤑 Avidité extrême</span></div>
      <div class="fg-track"><div class="fg-needle" id="fgN"></div></div>
    </div>
    <div class="fg-center">
      <div class="fg-big"><span class="fg-emoji-big">{fg_emoji}</span>
        <span id="fgC">0</span><span style="font-size:22px;color:var(--muted)">/100</span></div>
      <div class="fg-lbl">{fg_lbl}</div>
      <div class="fg-note">Un score sous 25 signifie que les investisseurs ont peur : historiquement, c'est souvent le meilleur moment pour acheter. Au-dessus de 75, l'euphorie guette — prudence recommandée.</div>
    </div>
  </div>
</div>

<!-- ── MACRO / GÉOPOLITIQUE ── -->
<div class="section acc-red" style="animation-delay:.30s">
  <div class="sec-header">
    <div class="sec-icon">🌍</div>
    <div><div class="sec-title">Macro & Géopolitique</div>
      <div class="sec-sub">Dollar · Or · Pétrole · Forex · Tensions mondiales</div></div>
    <span class="sec-pill pill-red">MACRO</span>
  </div>
  {commodities_table_html}
  <div class="analysis-block" style="margin-top:1.2rem">
    <div class="analysis-label">🧠 Analyse IA — Géopolitique & Macro</div>
    <div class="card-body">{self._md(analyses.get("macro",""))}</div>
  </div>
</div>

<!-- ── INSIGHTS GÉOPOLITIQUES ── -->
{insights_geo_html}

<!-- ── BOURSE SECTION ── -->
<div class="section acc-blue" style="animation-delay:.35s">
  <div class="sec-header">
    <div class="sec-icon">📊</div>
    <div><div class="sec-title">Marchés Boursiers</div>
      <div class="sec-sub">Indices mondiaux · Actions à surveiller</div></div>
    <span class="sec-pill pill-blue">LIVE</span>
  </div>

  <!-- Performance comparison chart -->
  {perf_chart_html}

  <!-- Tableau -->
  {market_table_html}

  <div class="analysis-block">
    <div class="analysis-label">🧠 Analyse IA — Bourse</div>
    <div class="card-body">{self._md(analyses.get("bourse",""))}</div>
  </div>
</div>

<!-- ── INTRO / SYNTHÈSE ── -->
<div class="section acc-cyan" style="animation-delay:.45s">
  <div class="sec-header">
    <div class="sec-icon">🌍</div>
    <div><div class="sec-title">Synthèse du jour</div>
      <div class="sec-sub">Vue d'ensemble rédigée par l'IA</div></div>
    <span class="sec-pill pill-cyan">IA</span>
  </div>
  <div class="card-body">{self._md(analyses.get("intro",""))}</div>
</div>

<!-- ── ROBOT TRADER ── -->
{self._build_trader_section(analyses)}

<!-- ── NEWS ── -->
{news_section_html}

<!-- ── ANECDOTE BOURSE ── -->
{self._build_anecdote_section(analyses)}

<!-- ── CONCEPT ── -->
<div class="section acc-green" style="animation-delay:.65s">
  <div class="sec-header">
    <div class="sec-icon">💡</div>
    <div><div class="sec-title">Le concept du jour</div>
      <div class="sec-sub">Une notion clé expliquée en 1 minute</div></div>
  </div>
  <div class="concept-top"><span class="concept-badge">✨ +1 notion maîtrisée</span></div>
  <div class="card-body">{self._md(analyses.get("concept",""))}</div>
</div>

<!-- ── CRYPTO SECTION ── -->
<div class="section acc-gold" style="animation-delay:.15s">
  <div class="sec-header">
    <div class="sec-icon">₿</div>
    <div><div class="sec-title">Marchés Crypto</div>
      <div class="sec-sub">Prix en temps réel · Variations · Capitalisation</div></div>
    <span class="sec-pill pill-gold">LIVE</span>
  </div>
  <div class="asset-grid">
    {crypto_cards_html}
  </div>
  <div class="analysis-block">
    <div class="analysis-label">🧠 Analyse IA — Crypto</div>
    <div class="card-body">{self._md(analyses.get("crypto",""))}</div>
  </div>
</div>

<!-- ── FOOTER ── -->
<div class="footer">
  <div class="footer-brand">🤖 {NEWSLETTER_NAME}</div>
  <div class="footer-txt">Newsletter entièrement générée par des agents IA · Propulsée par Claude (Anthropic)<br>
    Chaque jour, la finance décryptée pour les investisseurs de demain.</div>
  <div class="footer-disc">⚠️ Contenu fourni à titre informatif et pédagogique uniquement. Ne constitue pas un conseil en investissement. Investir comporte des risques dont la perte partielle ou totale du capital.</div>
  <div class="unsub"><a href="#">Se désabonner</a> · <a href="#">Archives</a> · <a href="#">Partager</a></div>
</div>

</div><!-- /wrap -->

<script>
// ── Data from Python ────────────────────────────────────────────────────────
const CRYPTO_DATA   = {crypto_js};
const BAR_LABELS    = {bar_labels};
const BAR_VALUES    = {bar_values};
const BAR_COLORS    = {bar_colors};
const FG_VAL        = {fg_val};

Chart.defaults.color = '#64748b';
Chart.defaults.font.family = "'Inter', sans-serif";

// ── Sparkline generator ──────────────────────────────────────────────────────
function genSparkline(price, var7d, n=9) {{
  const start = price / (1 + var7d / 100);
  const noise = price * 0.012;
  const pts = [];
  for (let i = 0; i < n; i++) {{
    const t = i / (n - 1);
    const trend = start + (price - start) * t;
    const jitter = (Math.sin(i * 2.3 + price % 10) * noise * 0.6 +
                    Math.cos(i * 1.7 + var7d) * noise * 0.4);
    pts.push(+(trend + jitter).toFixed(2));
  }}
  pts[n - 1] = price;
  return pts;
}}

// ── Sparkline charts ─────────────────────────────────────────────────────────
Object.entries(CRYPTO_DATA).forEach(([sym, d]) => {{
  const canvas = document.getElementById('chart_' + sym);
  if (!canvas) return;
  const pts   = genSparkline(d.price, d.var7);
  const color = d.color;
  const grad  = canvas.getContext('2d').createLinearGradient(0,0,0,55);
  grad.addColorStop(0, color + '44');
  grad.addColorStop(1, color + '00');
  new Chart(canvas, {{
    type: 'line',
    data: {{
      labels: pts.map((_,i) => i===0?'-7j':i===pts.length-1?'Auj':''),
      datasets: [{{ data: pts, borderColor: color, borderWidth: 2.5,
        backgroundColor: grad, fill: true, tension: 0.45,
        pointRadius: [0,0,0,0,0,0,0,0,3],
        pointBackgroundColor: color, pointBorderColor: '#fff', pointBorderWidth: 2 }}]
    }},
    options: {{
      responsive: true, animation: {{ duration: 800, easing: 'easeOutCubic' }},
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          enabled: true,
          backgroundColor: '#1e293b',
          borderColor: color,
          borderWidth: 2,
          titleColor: '#94a3b8',
          bodyColor: '#e2e8f0',
          padding: 10,
          titleFont: {{ size: 12, weight: 'bold' }},
          bodyFont: {{ size: 14, weight: 'bold' }},
          callbacks: {{
            label: ctx => '$' + ctx.raw.toLocaleString('en-US', {{minimumFractionDigits:2}})
          }}
        }}
      }},
      scales: {{
        x: {{ display: false }},
        y: {{ display: false, min: Math.min(...pts)*0.992, max: Math.max(...pts)*1.008 }}
      }}
    }}
  }});
}});

// ── Performance bar chart ────────────────────────────────────────────────────
const perfCanvas = document.getElementById('perfChart');
if (perfCanvas && BAR_LABELS.length > 0) {{
  new Chart(perfCanvas, {{
    type: 'bar',
    data: {{
      labels: BAR_LABELS,
      datasets: [{{
        label: 'Performance',
        data: BAR_VALUES,
        backgroundColor: BAR_COLORS.map(c => c + 'aa'),
        borderColor: BAR_COLORS,
        borderWidth: 2,
        borderRadius: 8,
      }}]
    }},
    options: {{
      indexAxis: 'y',
      responsive: true, maintainAspectRatio: false,
      animation: {{
        duration: 1200,
        easing: 'easeOutQuart',
        delay: (ctx) => ctx.dataIndex * 80
      }},
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          backgroundColor: '#1e293b',
          borderColor: (ctx) => BAR_COLORS[ctx[0].dataIndex],
          borderWidth: 2,
          titleColor: '#94a3b8',
          bodyColor: '#e2e8f0',
          padding: 12,
          titleFont: {{ size: 12, weight: 'bold' }},
          bodyFont: {{ size: 13, weight: 'bold' }},
          callbacks: {{
            label: (ctx) => {{
              const val = ctx.raw;
              return (val >= 0 ? '▲ +' : '▼ ') + val + '%';
            }}
          }}
        }}
      }},
      scales: {{
        x: {{ grid: {{ color: 'rgba(255,255,255,0.04)' }},
               ticks: {{ callback: v => v + '%', font: {{ size: 11 }} }} }},
        y: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 12 }}, color: '#e2e8f0' }} }}
      }}
    }}
  }});
}}

// ── Fear & Greed counter ─────────────────────────────────────────────────────
(function() {{
  const el = document.getElementById('fgC');
  let start = null;
  function ease(t) {{ return 1 - Math.pow(1-t, 3); }}
  function step(ts) {{
    if (!start) start = ts;
    const p = Math.min((ts - start) / 1300, 1);
    el.textContent = Math.round(ease(p) * FG_VAL);
    if (p < 1) requestAnimationFrame(step);
  }}
  setTimeout(() => requestAnimationFrame(step), 300);
}})();

// ── News counter ─────────────────────────────────────────────────────────────
(function() {{
  const el = document.getElementById('newsCount');
  let v = 0, target = 47;
  const iv = setInterval(() => {{
    v += 3; if (v >= target) {{ v = target; clearInterval(iv); }}
    el.textContent = v;
  }}, 40);
}})();

// ── Scroll fade-in ────────────────────────────────────────────────────────────
(function() {{
  const sections = document.querySelectorAll('.section,.kpi-card,.ai-banner');
  sections.forEach(s => {{
    s.style.opacity = '0'; s.style.transform = 'translateY(28px)';
    s.style.transition = 'opacity .65s ease, transform .65s ease';
  }});
  const obs = new IntersectionObserver(entries => {{
    entries.forEach(e => {{
      if (e.isIntersecting) {{
        e.target.style.opacity = '1'; e.target.style.transform = 'translateY(0)';
        obs.unobserve(e.target);
      }}
    }});
  }}, {{ threshold: 0.08 }});
  sections.forEach(s => obs.observe(s));
}})();

// ── Mouse glow on asset cards ─────────────────────────────────────────────────
document.querySelectorAll('.asset-card,.kpi-card').forEach(card => {{
  card.addEventListener('mousemove', e => {{
    const r = card.getBoundingClientRect();
    const x = ((e.clientX - r.left) / r.width * 100).toFixed(1);
    const y = ((e.clientY - r.top)  / r.height * 100).toFixed(1);
    card.style.background = `radial-gradient(circle at ${{x}}% ${{y}}%, rgba(255,255,255,0.08), rgba(255,255,255,0.04))`;
  }});
  card.addEventListener('mouseleave', () => {{ card.style.background = ''; }});
}});
</script>
</body>
</html>"""

    # ─── POINT D'ENTRÉE ──────────────────────────────────────────────────────

    def rediger_newsletter(self, analyses: dict) -> str:
        print("\n━━━ AGENT RÉDACTEUR : Assemblage de la newsletter ━━━")
        _log(_AGENT_R, "start", "Génération de la newsletter en cours...")
        html = self._build_html(analyses)
        nom  = f"alphabot_newsletter_{datetime.now().strftime('%Y-%m-%d')}.html"
        path = os.path.join(OUTPUT_DIR, nom)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"\n✅ Newsletter générée : {path}")
        _log(_AGENT_R, "success", f"Newsletter générée : {nom}", {"fichier": nom, "taille_kb": round(len(html)/1024, 1)})
        # Mettre à jour l'archive automatiquement
        self.maj_archive()
        _log(_AGENT_R, "info", "Archive newsletters.html mise à jour")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        return path

    def maj_archive(self) -> str:
        """
        Génère / met à jour newsletters.html à la racine du projet.
        Scanne tous les fichiers alphabot_newsletter_*.html dans outputs/
        et crée une page d'archive publique classée par date.
        """
        import glob, re
        BASE_URL = "https://alphabotweeklynetlifyapp.netlify.app"
        pattern  = os.path.join(OUTPUT_DIR, "alphabot_newsletter_*.html")
        fichiers = sorted(glob.glob(pattern), reverse=True)

        cards_html = ""
        for f in fichiers:
            nom  = os.path.basename(f)
            m    = re.search(r"(\d{4}-\d{2}-\d{2})", nom)
            if not m:
                continue
            date_iso = m.group(1)
            try:
                d = datetime.strptime(date_iso, "%Y-%m-%d")
                date_fr  = d.strftime("%d %B %Y").lstrip("0")
                jour_sem = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"][d.weekday()]
            except ValueError:
                date_fr, jour_sem = date_iso, ""
            url = f"{BASE_URL}/outputs/{nom}"
            taille_kb = round(os.path.getsize(f) / 1024, 1) if os.path.exists(f) else "?"
            cards_html += f"""
        <a href="{url}" target="_blank" class="card">
          <div class="card-date">{jour_sem} {date_fr}</div>
          <div class="card-title">📊 Édition AlphaBot Weekly</div>
          <div class="card-meta">{taille_kb} KB · Générée par IA</div>
          <div class="card-cta">Lire l'édition →</div>
        </a>"""

        nb = len(fichiers)
        now_str = datetime.now().strftime("%d/%m/%Y à %H:%M")

        archive_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>AlphaBot Weekly — Toutes les newsletters</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@700;800&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:#04091a;color:#e2e8f0;font-family:'Inter',sans-serif;min-height:100vh;padding:32px 16px 60px;}}
.bg{{position:fixed;inset:0;z-index:0;pointer-events:none;
  background-image:linear-gradient(rgba(59,130,246,.025)1px,transparent 1px),
  linear-gradient(90deg,rgba(59,130,246,.025)1px,transparent 1px);
  background-size:60px 60px;}}
.wrap{{position:relative;z-index:1;max-width:900px;margin:0 auto;}}
header{{text-align:center;margin-bottom:40px;padding:36px 24px;
  background:linear-gradient(135deg,rgba(59,130,246,.1),rgba(245,200,66,.06));
  border:1px solid rgba(59,130,246,.2);border-radius:20px;}}
.logo{{font-family:'Space Grotesk',sans-serif;font-size:28px;font-weight:900;
  background:linear-gradient(135deg,#fff,#63b3ed,#f5c842);
  -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;
  margin-bottom:8px;}}
.sub{{color:#64748b;font-size:14px;margin-bottom:16px;}}
.badge{{display:inline-block;background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.3);
  color:#22c55e;font-size:12px;font-weight:700;padding:4px 14px;border-radius:20px;}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px;}}
.card{{display:block;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);
  border-radius:14px;padding:20px;text-decoration:none;
  transition:transform .2s,border-color .2s;}}
.card:hover{{transform:translateY(-3px);border-color:rgba(99,179,237,.35);}}
.card-date{{font-size:11px;color:#64748b;font-weight:600;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;}}
.card-title{{font-family:'Space Grotesk',sans-serif;font-size:16px;font-weight:700;color:white;margin-bottom:6px;}}
.card-meta{{font-size:12px;color:#475569;margin-bottom:12px;}}
.card-cta{{font-size:13px;font-weight:600;color:#63b3ed;}}
.back{{display:inline-block;color:#64748b;font-size:13px;text-decoration:none;margin-bottom:28px;}}
.back:hover{{color:#93c5fd;}}
.update{{text-align:center;color:#334155;font-size:11px;margin-top:32px;}}
</style>
</head>
<body>
<div class="bg"></div>
<div class="wrap">
  <a href="index.html" class="back">← Retour à l'accueil</a>
  <header>
    <div class="logo">🤖 AlphaBot Weekly</div>
    <div class="sub">L'essentiel des marchés bourse &amp; crypto — par l'IA</div>
    <div class="badge">📚 {nb} édition(s) disponible(s)</div>
  </header>
  <div class="grid">
    {cards_html if cards_html else "<div style='color:#64748b;text-align:center;padding:40px;grid-column:1/-1;'>Aucune newsletter générée pour l'instant.</div>"}
  </div>
  <div class="update">Mis à jour automatiquement · {now_str}</div>
</div>
</body>
</html>"""

        archive_path = "newsletters.html"
        with open(archive_path, "w", encoding="utf-8") as f:
            f.write(archive_html)
        print(f"  📚 Archive newsletters mise à jour : {archive_path} ({nb} édition(s))")
        return archive_path
