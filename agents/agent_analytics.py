"""
AlphaBot — Agent Analytics 📊
Rôle : Agréger toutes les données des agents, calculer les KPIs clés,
       et générer un dashboard HTML hebdomadaire pour le fondateur.

Sources :
  - data/subscribers.csv  (Agent Growth)
  - data/send_log.csv     (Agent Growth)
  - data/prospects.csv    (Agent Commercial)
  - data/revenues.csv     (Agent CFO)
"""

import os, csv, json
from datetime import datetime, timedelta
from pathlib import Path

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import NEWSLETTER_NAME, OUTPUT_DIR

DATA_DIR = "data"


class AgentAnalytics:

    def __init__(self):
        Path(DATA_DIR).mkdir(exist_ok=True)
        Path(OUTPUT_DIR).mkdir(exist_ok=True)
        print("📊 Agent Analytics initialisé ✅")

    # ─── LECTURE DES DONNÉES ─────────────────────────────────────────────────

    def _lire_csv(self, path: str) -> list:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return list(csv.DictReader(f))
        except FileNotFoundError:
            return []

    def _collecter_donnees(self) -> dict:
        """Agrège toutes les données de l'entreprise."""
        abonnes   = self._lire_csv(os.path.join(DATA_DIR, "subscribers.csv"))
        send_log  = self._lire_csv(os.path.join(DATA_DIR, "send_log.csv"))
        prospects = self._lire_csv(os.path.join(DATA_DIR, "prospects.csv"))
        revenues  = self._lire_csv(os.path.join(DATA_DIR, "revenues.csv"))
        return {
            "abonnes":   abonnes,
            "send_log":  send_log,
            "prospects": prospects,
            "revenues":  revenues,
        }

    # ─── CALCUL DES KPIs ─────────────────────────────────────────────────────

    def calculer_kpis(self) -> dict:
        """Calcule tous les KPIs de l'entreprise."""
        d = self._collecter_donnees()

        # ── Abonnés ──
        actifs    = [a for a in d["abonnes"] if a.get("actif") == "oui"]
        inactifs  = [a for a in d["abonnes"] if a.get("actif") != "oui"]
        nb_actifs = len(actifs)

        # Croissance sur 7 et 30 jours
        now = datetime.now()
        j7  = [a for a in actifs if self._date_depuis(a.get("date_inscription","")) <= 7]
        j30 = [a for a in actifs if self._date_depuis(a.get("date_inscription","")) <= 30]
        taux_churn = round(len(inactifs) / max(len(d["abonnes"]), 1) * 100, 1)

        # Sources d'acquisition
        sources = {}
        for a in actifs:
            s = a.get("source", "inconnu")
            sources[s] = sources.get(s, 0) + 1

        # ── Envois ──
        nb_editions = len(d["send_log"])
        total_envoyes = sum(int(r.get("nb_envoyes", 0)) for r in d["send_log"])
        total_erreurs = sum(int(r.get("nb_erreurs", 0)) for r in d["send_log"])
        taux_livraison = round(
            total_envoyes / max(total_envoyes + total_erreurs, 1) * 100, 1
        )

        # ── Prospects commerciaux ──
        par_statut = {}
        for p in d["prospects"]:
            s = p.get("statut", "inconnu")
            par_statut[s] = par_statut.get(s, 0) + 1

        nb_partenaires  = par_statut.get("partenaire", 0)
        nb_contactes    = par_statut.get("contacte", 0)
        nb_discussion   = par_statut.get("en_discussion", 0)
        nb_prospects    = par_statut.get("prospect", 0)
        taux_conversion = round(
            nb_partenaires / max(nb_contactes + nb_discussion + nb_partenaires, 1) * 100, 1
        )

        # ── Revenus ──
        rev_total = sum(float(r.get("montant", 0)) for r in d["revenues"])
        rev_mois  = sum(
            float(r.get("montant", 0)) for r in d["revenues"]
            if self._date_depuis(r.get("date", "")) <= 30
        )

        # ── Tendance abonnés (7 dernières semaines simulée si peu de données) ──
        trend_abonnes = self._calculer_tendance_abonnes(actifs)

        return {
            "timestamp":          datetime.now().strftime("%d/%m/%Y %H:%M"),
            # Growth
            "nb_abonnes_actifs":  nb_actifs,
            "nouveaux_7j":        len(j7),
            "nouveaux_30j":       len(j30),
            "taux_churn":         taux_churn,
            "sources":            sources,
            "trend_abonnes":      trend_abonnes,
            # Distribution
            "nb_editions":        nb_editions,
            "total_envoyes":      total_envoyes,
            "taux_livraison":     taux_livraison,
            # Commercial
            "nb_prospects_total": len(d["prospects"]),
            "nb_prospects_dispo": nb_prospects,
            "nb_contactes":       nb_contactes,
            "nb_discussion":      nb_discussion,
            "nb_partenaires":     nb_partenaires,
            "taux_conversion":    taux_conversion,
            # Finance
            "rev_total":          round(rev_total, 2),
            "rev_30j":            round(rev_mois, 2),
        }

    @staticmethod
    def _date_depuis(date_str: str) -> int:
        """Retourne le nombre de jours depuis une date ISO."""
        if not date_str:
            return 9999
        try:
            d = datetime.strptime(date_str[:10], "%Y-%m-%d")
            return (datetime.now() - d).days
        except ValueError:
            return 9999

    def _calculer_tendance_abonnes(self, abonnes: list) -> list:
        """Calcule la tendance hebdomadaire des abonnements (7 semaines)."""
        semaines = []
        now = datetime.now()
        for i in range(6, -1, -1):
            debut_sem = now - timedelta(weeks=i+1)
            fin_sem   = now - timedelta(weeks=i)
            count = sum(
                1 for a in abonnes
                if self._dans_periode(a.get("date_inscription",""), debut_sem, fin_sem)
            )
            semaines.append({
                "label": f"S-{i}" if i > 0 else "Cette sem.",
                "count": count
            })
        return semaines

    @staticmethod
    def _dans_periode(date_str: str, debut: datetime, fin: datetime) -> bool:
        if not date_str:
            return False
        try:
            d = datetime.strptime(date_str[:10], "%Y-%m-%d")
            return debut <= d < fin
        except ValueError:
            return False

    # ─── GÉNÉRATION DU DASHBOARD HTML ────────────────────────────────────────

    def generer_dashboard(self) -> str:
        """Génère un dashboard HTML complet avec tous les KPIs."""
        kpis = self.calculer_kpis()
        print("\n━━━ AGENT ANALYTICS : Génération du dashboard ━━━")

        # Données pour les graphiques JS
        trend_labels = json.dumps([s["label"] for s in kpis["trend_abonnes"]])
        trend_data   = json.dumps([s["count"] for s in kpis["trend_abonnes"]])
        pipeline_labels = json.dumps(["Prospects", "Contactés", "En discussion", "Partenaires"])
        pipeline_data   = json.dumps([
            kpis["nb_prospects_dispo"], kpis["nb_contactes"],
            kpis["nb_discussion"],       kpis["nb_partenaires"]
        ])
        pipeline_colors = json.dumps(["#475569","#3b82f6","#f59e0b","#22c55e"])
        sources_labels = json.dumps(list(kpis["sources"].keys()) or ["—"])
        sources_data   = json.dumps(list(kpis["sources"].values()) or [0])
        sources_colors = json.dumps(["#3b82f6","#22c55e","#f59e0b","#ec4899","#8b5cf6","#06b6d4"])

        def kpi_card(icon, label, value, sub="", color="#3b82f6"):
            return f"""
            <div class="kpi">
              <div class="kpi-icon" style="background:{color}18;border-color:{color}33;">{icon}</div>
              <div class="kpi-body">
                <div class="kpi-val" style="color:{color};">{value}</div>
                <div class="kpi-lbl">{label}</div>
                {f'<div class="kpi-sub">{sub}</div>' if sub else ""}
              </div>
            </div>"""

        # KPI cards
        cards_growth = (
            kpi_card("👥", "Abonnés actifs",  kpis["nb_abonnes_actifs"], f"+{kpis['nouveaux_7j']} cette semaine", "#22c55e") +
            kpi_card("📈", "Nouveaux / 7j",   kpis["nouveaux_7j"],  f"{kpis['nouveaux_30j']} sur 30j", "#3b82f6") +
            kpi_card("📧", "Éditions envoyées", kpis["nb_editions"], f"{kpis['total_envoyes']} emails au total", "#f59e0b") +
            kpi_card("✅", "Taux livraison",   f"{kpis['taux_livraison']}%", "des emails arrivent à destination", "#22c55e")
        )
        cards_commercial = (
            kpi_card("🎯", "Pipeline total",  kpis["nb_prospects_total"], f"{kpis['nb_prospects_dispo']} disponibles", "#8b5cf6") +
            kpi_card("📨", "Contactés",        kpis["nb_contactes"],  "en attente de réponse", "#3b82f6") +
            kpi_card("💬", "En discussion",    kpis["nb_discussion"], "partenariat en cours", "#f59e0b") +
            kpi_card("🤝", "Partenaires",      kpis["nb_partenaires"], f"taux conversion : {kpis['taux_conversion']}%", "#22c55e")
        )
        cards_finance = (
            kpi_card("💰", "Revenus 30 jours", f"{kpis['rev_30j']}€", "ce mois", "#f5c842") +
            kpi_card("💎", "Revenus totaux",   f"{kpis['rev_total']}€", "depuis le lancement", "#22c55e") +
            kpi_card("📉", "Taux churn",        f"{kpis['taux_churn']}%", "désabonnements", "#ef4444") +
            kpi_card("🚀", "Objectif",          "1 000 abonnés", f"progression : {min(kpis['nb_abonnes_actifs'],1000)}/1000", "#8b5cf6")
        )

        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>AlphaBot — Dashboard Analytics</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Space+Grotesk:wght@600;700;800&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
:root{{--bg:#04091a;--bg2:#060d1f;--s:rgba(255,255,255,.04);--s2:rgba(255,255,255,.07);
       --b:rgba(255,255,255,.08);--gold:#f5c842;--blue:#3b82f6;--cyan:#22d3ee;
       --green:#22c55e;--red:#ef4444;--text:#e2e8f0;--muted:#64748b;}}
body{{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;min-height:100vh;}}
.bg-grid{{position:fixed;inset:0;z-index:0;pointer-events:none;
  background-image:linear-gradient(rgba(59,130,246,.025)1px,transparent 1px),
    linear-gradient(90deg,rgba(59,130,246,.025)1px,transparent 1px);
  background-size:60px 60px;}}
.wrap{{position:relative;z-index:1;max-width:1100px;margin:0 auto;padding:28px 18px 60px;}}

/* HEADER */
.dash-header{{display:flex;align-items:center;justify-content:space-between;
              flex-wrap:wrap;gap:12px;margin-bottom:32px;
              padding:24px 28px;border-radius:16px;
              background:linear-gradient(135deg,rgba(59,130,246,.1),rgba(245,200,66,.06));
              border:1px solid var(--b);}}
.dash-title{{font-family:'Space Grotesk',sans-serif;font-size:24px;font-weight:800;
             background:linear-gradient(135deg,#fff,var(--cyan),var(--gold));
             -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;}}
.dash-sub{{font-size:13px;color:var(--muted);margin-top:3px;}}
.dash-badge{{display:flex;align-items:center;gap:6px;font-size:11px;font-weight:700;
             color:var(--green);background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.25);
             padding:6px 14px;border-radius:20px;}}
.live-dot{{width:6px;height:6px;border-radius:50%;background:var(--green);
           animation:pulse 1.5s ease-in-out infinite;}}
@keyframes pulse{{0%,100%{{transform:scale(1);opacity:1;}}50%{{transform:scale(1.6);opacity:.4;}}}}

/* SECTIONS */
.section-title{{font-family:'Space Grotesk',sans-serif;font-size:15px;font-weight:700;
                color:var(--muted);text-transform:uppercase;letter-spacing:1.5px;
                display:flex;align-items:center;gap:8px;margin:28px 0 14px;}}
.section-title::after{{content:'';flex:1;height:1px;background:var(--b);}}

/* KPI GRID */
.kpi-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;}}
.kpi{{background:var(--s);border:1px solid var(--b);border-radius:14px;padding:18px;
      display:flex;align-items:center;gap:14px;
      transition:transform .2s,border-color .2s;cursor:default;}}
.kpi:hover{{transform:translateY(-2px);border-color:rgba(255,255,255,.14);}}
.kpi-icon{{width:46px;height:46px;border-radius:12px;display:flex;align-items:center;
           justify-content:center;font-size:20px;flex-shrink:0;border:1px solid;}}
.kpi-val{{font-family:'Space Grotesk',sans-serif;font-size:26px;font-weight:800;line-height:1;}}
.kpi-lbl{{font-size:12px;color:var(--muted);margin-top:3px;font-weight:500;}}
.kpi-sub{{font-size:11px;color:#475569;margin-top:2px;}}

/* CHARTS GRID */
.charts-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px;}}
.chart-card{{background:var(--s);border:1px solid var(--b);border-radius:16px;padding:22px;}}
.chart-title{{font-size:14px;font-weight:700;color:white;margin-bottom:4px;}}
.chart-sub{{font-size:11px;color:var(--muted);margin-bottom:18px;}}
.chart-wrap{{position:relative;height:200px;}}

/* PIPELINE FUNNEL */
.funnel{{display:flex;flex-direction:column;gap:8px;margin-top:6px;}}
.funnel-row{{display:flex;align-items:center;gap:10px;}}
.funnel-bar-wrap{{flex:1;height:28px;background:var(--s2);border-radius:6px;overflow:hidden;}}
.funnel-bar{{height:100%;border-radius:6px;transition:width 1s cubic-bezier(.34,1.56,.64,1);}}
.funnel-lbl{{font-size:12px;font-weight:600;color:var(--muted);width:90px;text-align:right;}}
.funnel-num{{font-size:13px;font-weight:700;color:white;width:30px;text-align:right;}}

/* ACTIVITY LOG */
.activity{{display:flex;flex-direction:column;gap:6px;}}
.act-item{{display:flex;align-items:center;gap:10px;padding:10px 12px;
           background:var(--s2);border-radius:8px;font-size:12px;}}
.act-dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0;}}
.act-text{{flex:1;color:#cbd5e1;}}
.act-time{{color:var(--muted);font-size:11px;}}

/* OBJECTIFS */
.obj-list{{display:flex;flex-direction:column;gap:10px;}}
.obj-item{{background:var(--s2);border-radius:10px;padding:14px;}}
.obj-header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;}}
.obj-name{{font-size:13px;font-weight:600;color:white;}}
.obj-pct{{font-size:12px;font-weight:700;}}
.obj-bar-wrap{{height:6px;background:var(--s);border-radius:3px;overflow:hidden;}}
.obj-bar{{height:100%;border-radius:3px;transition:width 1.2s cubic-bezier(.34,1.56,.64,1);}}

@media(max-width:600px){{
  .wrap{{padding:12px 10px 40px;}}
  .kpi-grid{{grid-template-columns:repeat(2,1fr);}}
  .charts-grid{{grid-template-columns:1fr;}}
}}
</style>
</head>
<body>
<div class="bg-grid"></div>
<div class="wrap">

<!-- HEADER -->
<div class="dash-header">
  <div>
    <div class="dash-title">📊 AlphaBot — Dashboard Analytics</div>
    <div class="dash-sub">Vue d'ensemble de l'entreprise IA • Mis à jour le {kpis["timestamp"]}</div>
  </div>
  <div class="dash-badge"><div class="live-dot"></div>Rapport hebdomadaire</div>
</div>

<!-- SECTION GROWTH -->
<div class="section-title">📈 Growth & Audience</div>
<div class="kpi-grid">{cards_growth}</div>

<!-- SECTION COMMERCIAL -->
<div class="section-title">💼 Pipeline Commercial</div>
<div class="kpi-grid">{cards_commercial}</div>

<!-- SECTION FINANCE -->
<div class="section-title">💰 Finance & Revenus</div>
<div class="kpi-grid">{cards_finance}</div>

<!-- GRAPHIQUES -->
<div class="section-title">📉 Visualisations</div>
<div class="charts-grid">

  <!-- Tendance abonnés -->
  <div class="chart-card">
    <div class="chart-title">Croissance abonnés</div>
    <div class="chart-sub">Nouveaux abonnés par semaine</div>
    <div class="chart-wrap"><canvas id="trendChart"></canvas></div>
  </div>

  <!-- Sources acquisition -->
  <div class="chart-card">
    <div class="chart-title">Sources d'acquisition</div>
    <div class="chart-sub">D'où viennent vos abonnés</div>
    <div class="chart-wrap"><canvas id="sourcesChart"></canvas></div>
  </div>

  <!-- Pipeline commercial funnel -->
  <div class="chart-card">
    <div class="chart-title">Funnel commercial</div>
    <div class="chart-sub">Pipeline de prospection sponsors</div>
    <div class="funnel" id="funnelViz"></div>
  </div>

  <!-- Objectifs -->
  <div class="chart-card">
    <div class="chart-title">Objectifs</div>
    <div class="chart-sub">Progression vers les jalons clés</div>
    <div class="obj-list">
      {self._objectifs_html(kpis)}
    </div>
  </div>

</div><!-- /charts-grid -->
</div><!-- /wrap -->

<script>
Chart.defaults.color = '#64748b';
Chart.defaults.font.family = "'Inter',sans-serif";

const TREND_LABELS  = {trend_labels};
const TREND_DATA    = {trend_data};
const PIPE_LABELS   = {pipeline_labels};
const PIPE_DATA     = {pipeline_data};
const PIPE_COLORS   = {pipeline_colors};
const SRC_LABELS    = {sources_labels};
const SRC_DATA      = {sources_data};
const SRC_COLORS    = {sources_colors};

// ── Trend chart ───────────────────────────────────────────────────────────────
const trendCtx = document.getElementById('trendChart').getContext('2d');
const trendGrad = trendCtx.createLinearGradient(0,0,0,180);
trendGrad.addColorStop(0,'rgba(34,197,94,.3)');
trendGrad.addColorStop(1,'rgba(34,197,94,.0)');
new Chart(trendCtx, {{
  type: 'line',
  data: {{ labels: TREND_LABELS,
    datasets: [{{ label: 'Nouveaux abonnés', data: TREND_DATA,
      borderColor: '#22c55e', borderWidth: 2.5, backgroundColor: trendGrad,
      fill: true, tension: 0.4,
      pointRadius: 4, pointBackgroundColor: '#22c55e', pointBorderColor: '#fff', pointBorderWidth: 2
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ grid: {{ color: 'rgba(255,255,255,.04)' }} }},
      y: {{ beginAtZero: true, grid: {{ color: 'rgba(255,255,255,.04)' }},
             ticks: {{ stepSize: 1 }} }}
    }}
  }}
}});

// ── Sources doughnut ──────────────────────────────────────────────────────────
new Chart(document.getElementById('sourcesChart'), {{
  type: 'doughnut',
  data: {{ labels: SRC_LABELS,
    datasets: [{{ data: SRC_DATA, backgroundColor: SRC_COLORS.slice(0,SRC_DATA.length),
      borderWidth: 0, hoverOffset: 8 }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{
      legend: {{ position: 'bottom', labels: {{ padding: 16, font: {{ size: 12 }} }} }}
    }}
  }}
}});

// ── Funnel bars ────────────────────────────────────────────────────────────────
(function() {{
  const funnel = document.getElementById('funnelViz');
  const max = Math.max(...PIPE_DATA, 1);
  PIPE_LABELS.forEach((lbl, i) => {{
    const pct = Math.round(PIPE_DATA[i] / max * 100);
    const row = document.createElement('div');
    row.className = 'funnel-row';
    row.innerHTML = `
      <div class="funnel-lbl">${{lbl}}</div>
      <div class="funnel-bar-wrap">
        <div class="funnel-bar" style="width:0%;background:${{PIPE_COLORS[i]}};"
             data-target="${{pct}}%"></div>
      </div>
      <div class="funnel-num">${{PIPE_DATA[i]}}</div>`;
    funnel.appendChild(row);
  }});
  // Animate bars
  setTimeout(() => {{
    document.querySelectorAll('.funnel-bar').forEach(bar => {{
      bar.style.width = bar.dataset.target;
    }});
  }}, 200);
}})();

// ── Progress bars (objectifs) ─────────────────────────────────────────────────
setTimeout(() => {{
  document.querySelectorAll('.obj-bar').forEach(bar => {{
    bar.style.width = bar.dataset.target;
  }});
}}, 300);

// ── Scroll fade-in ─────────────────────────────────────────────────────────────
document.querySelectorAll('.kpi,.chart-card').forEach((el,i) => {{
  el.style.opacity = '0';
  el.style.transform = 'translateY(20px)';
  el.style.transition = `opacity .5s ease ${{i*0.05}}s, transform .5s ease ${{i*0.05}}s`;
}});
new IntersectionObserver(entries => {{
  entries.forEach(e => {{
    if (e.isIntersecting) {{
      e.target.style.opacity = '1';
      e.target.style.transform = 'translateY(0)';
    }}
  }});
}}, {{threshold: 0.1}}).observe(document.body) ||
document.querySelectorAll('.kpi,.chart-card').forEach(el => {{
  el.style.opacity = '1'; el.style.transform = 'translateY(0)';
}});

// Simple scroll observer
const obs = new IntersectionObserver(entries => {{
  entries.forEach(e => {{
    if(e.isIntersecting){{e.target.style.opacity='1';e.target.style.transform='translateY(0)';}}
  }});
}}, {{threshold:0.05}});
document.querySelectorAll('.kpi,.chart-card').forEach(el => obs.observe(el));
</script>
</body>
</html>"""

        # Sauvegarde
        nom    = f"alphabot_dashboard_{datetime.now().strftime('%Y-%m-%d')}.html"
        chemin = os.path.join(OUTPUT_DIR, nom)
        with open(chemin, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"✅ Dashboard généré : {chemin}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        return chemin

    def _objectifs_html(self, kpis: dict) -> str:
        """Génère les barres de progression vers les objectifs."""
        objectifs = [
            {"nom": "1 000 abonnés",       "actuel": kpis["nb_abonnes_actifs"], "cible": 1000,  "color": "#22c55e"},
            {"nom": "5 partenaires actifs", "actuel": kpis["nb_partenaires"],    "cible": 5,     "color": "#f5c842"},
            {"nom": "1 000€ / mois",        "actuel": int(kpis["rev_30j"]),      "cible": 1000,  "color": "#3b82f6"},
            {"nom": "10 éditions envoyées", "actuel": kpis["nb_editions"],       "cible": 10,    "color": "#8b5cf6"},
        ]
        html = ""
        for obj in objectifs:
            pct   = min(round(obj["actuel"] / max(obj["cible"], 1) * 100), 100)
            color = obj["color"]
            html += f"""
        <div class="obj-item">
          <div class="obj-header">
            <div class="obj-name">{obj["nom"]}</div>
            <div class="obj-pct" style="color:{color};">{pct}%</div>
          </div>
          <div class="obj-bar-wrap">
            <div class="obj-bar" style="width:0%;background:{color};" data-target="{pct}%"></div>
          </div>
        </div>"""
        return html

    # ─── RAPPORT TEXTE ────────────────────────────────────────────────────────

    def rapport_texte(self) -> str:
        """Génère un rapport texte concis pour le fondateur."""
        k = self.calculer_kpis()
        return f"""
╔══════════════════════════════════════════════════╗
║       📊  RAPPORT ANALYTICS — {datetime.now().strftime("%d/%m/%Y"):<17} ║
╚══════════════════════════════════════════════════╝

👥 AUDIENCE
   Abonnés actifs     : {k['nb_abonnes_actifs']}
   Nouveaux (7j)      : +{k['nouveaux_7j']}
   Nouveaux (30j)     : +{k['nouveaux_30j']}
   Taux churn         : {k['taux_churn']}%

📧 DISTRIBUTION
   Éditions envoyées  : {k['nb_editions']}
   Emails envoyés     : {k['total_envoyes']}
   Taux livraison     : {k['taux_livraison']}%

💼 COMMERCIAL
   Pipeline total     : {k['nb_prospects_total']} prospects
   Contactés          : {k['nb_contactes']}
   En discussion      : {k['nb_discussion']}
   Partenaires        : {k['nb_partenaires']}
   Taux conversion    : {k['taux_conversion']}%

💰 FINANCE
   Revenus 30j        : {k['rev_30j']}€
   Revenus totaux     : {k['rev_total']}€
"""


if __name__ == "__main__":
    agent = AgentAnalytics()
    print(agent.rapport_texte())
    chemin = agent.generer_dashboard()
    print(f"Dashboard : {chemin}")
