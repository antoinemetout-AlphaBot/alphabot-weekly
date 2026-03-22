"""
AlphaBot — Live Monitor 🖥️
===========================
Serveur HTTP local qui expose un dashboard de supervision en temps réel.
Tourne en permanence sur l'ordi d'Antoine, accessible depuis n'importe quel navigateur.

Usage :
    python monitor.py              → démarre sur http://localhost:8080
    python monitor.py --port 9090  → port personnalisé

Le dashboard se met à jour automatiquement toutes les 5 secondes.
Chaque agent écrit dans data/activity_log.jsonl via utils/activity_logger.py.
"""

import os, sys, json, csv, argparse, threading, webbrowser
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ─── Chemin absolu du projet ─────────────────────────────────────────────────
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_DIR)
sys.path.insert(0, PROJECT_DIR)

DATA_DIR   = os.path.join(PROJECT_DIR, "data")
LOG_FILE   = os.path.join(DATA_DIR, "activity_log.jsonl")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "outputs")

# Couleurs et icônes par type d'event
EVENT_STYLES = {
    "start":     {"color": "#3b82f6",  "bg": "rgba(59,130,246,.08)",  "icon": "▶"},
    "progress":  {"color": "#f59e0b",  "bg": "rgba(245,158,11,.08)",  "icon": "⟳"},
    "success":   {"color": "#22c55e",  "bg": "rgba(34,197,94,.08)",   "icon": "✓"},
    "error":     {"color": "#ef4444",  "bg": "rgba(239,68,68,.08)",   "icon": "✕"},
    "warning":   {"color": "#f59e0b",  "bg": "rgba(245,158,11,.06)",  "icon": "⚠"},
    "info":      {"color": "#64748b",  "bg": "rgba(100,116,139,.06)", "icon": "ℹ"},
    "milestone": {"color": "#f5c842",  "bg": "rgba(245,200,66,.1)",   "icon": "★"},
}

# Agents connus et leur emoji
AGENTS_CONNUS = {
    "Directeur Adjoint":    "🤝",
    "Agent Veille":         "📡",
    "Agent Analyste":       "🧠",
    "Agent Rédacteur":      "✍️",
    "Agent Growth":         "📈",
    "Agent Growth Booster": "🚀",
    "Agent Commercial":     "💼",
    "Agent Analytics":      "📊",
    "Agent CFO":            "💰",
    "Agent CEO Brief":      "👔",
    "Monitor":              "🖥️",
}


# ─── Lecture des données ─────────────────────────────────────────────────────

def lire_events(n: int = 300) -> list:
    events = []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in reversed(lines[-n:]):
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except Exception:
                    pass
    except FileNotFoundError:
        pass
    return events

def lire_kpis() -> dict:
    def lire_csv(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return list(csv.DictReader(f))
        except Exception:
            return []

    abonnes  = lire_csv(os.path.join(DATA_DIR, "subscribers.csv"))
    send_log = lire_csv(os.path.join(DATA_DIR, "send_log.csv"))
    revenus  = lire_csv(os.path.join(DATA_DIR, "revenues.csv"))
    prospects= lire_csv(os.path.join(DATA_DIR, "prospects.csv"))

    actifs     = [a for a in abonnes if a.get("actif") == "oui"]
    humains    = [a for a in actifs if "simulation" not in a.get("source","")]
    rev_total  = sum(float(r.get("montant",0)) for r in revenus)

    booster_score = 0
    try:
        with open(os.path.join(DATA_DIR, "booster_score.json"), "r", encoding="utf-8") as f:
            booster_score = json.load(f).get("total_points", 0)
    except Exception:
        pass

    return {
        "abonnes_total":   len(actifs),
        "abonnes_humains": len(humains),
        "editions":        len(send_log),
        "revenus":         round(rev_total, 2),
        "prospects":       len(prospects),
        "booster_score":   booster_score,
    }

def statut_agents(events: list) -> dict:
    """Calcule le statut actuel de chaque agent à partir du log."""
    statuts = {}
    for agent in AGENTS_CONNUS:
        statuts[agent] = {"statut": "idle", "dernier_event": None, "derniere_action": "—"}

    for e in reversed(events):
        agent = e.get("agent", "")
        if agent not in statuts:
            statuts[agent] = {"statut": "idle", "dernier_event": None, "derniere_action": "—"}
        s = statuts[agent]
        if s["dernier_event"] is None:
            s["dernier_event"] = e
            s["derniere_action"] = e.get("message", "—")[:80]
            etype = e.get("type", "")
            if etype == "start":
                s["statut"] = "running"
            elif etype == "error":
                s["statut"] = "error"
            elif etype == "success":
                s["statut"] = "success"
            else:
                s["statut"] = "idle"
    return statuts


# ─── HTML du dashboard ───────────────────────────────────────────────────────

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>AlphaBot — Live Monitor</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0;}
:root{--bg:#04091a;--bg2:#060d1f;--card:rgba(255,255,255,.03);--border:rgba(255,255,255,.07);
      --blue:#3b82f6;--green:#22c55e;--yellow:#f5c842;--red:#ef4444;--purple:#a855f7;
      --cyan:#22d3ee;--text:#e2e8f0;--muted:#64748b;}
body{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;min-height:100vh;overflow-x:hidden;}
.grid-bg{position:fixed;inset:0;z-index:0;pointer-events:none;
  background-image:linear-gradient(rgba(59,130,246,.02)1px,transparent 1px),
  linear-gradient(90deg,rgba(59,130,246,.02)1px,transparent 1px);background-size:50px 50px;}
.wrap{position:relative;z-index:1;max-width:1400px;margin:0 auto;padding:20px 16px 60px;}

/* HEADER */
.header{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;
  padding:20px 24px;background:linear-gradient(135deg,rgba(59,130,246,.1),rgba(168,85,247,.06));
  border:1px solid rgba(59,130,246,.2);border-radius:16px;margin-bottom:20px;}
.header-left h1{font-family:'Space Grotesk',sans-serif;font-size:22px;font-weight:900;
  background:linear-gradient(135deg,#fff,var(--cyan),var(--yellow));
  -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;}
.header-left p{color:var(--muted);font-size:13px;margin-top:3px;}
.live-badge{display:flex;align-items:center;gap:8px;font-size:12px;font-weight:700;color:var(--green);
  background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.25);padding:7px 16px;border-radius:20px;}
.dot{width:7px;height:7px;border-radius:50%;background:var(--green);animation:pulse 1.4s ease-in-out infinite;}
@keyframes pulse{0%,100%{transform:scale(1);opacity:1;}50%{transform:scale(1.8);opacity:.3;}}
#last-update{color:var(--muted);font-size:11px;margin-top:4px;}

/* LAYOUT */
.layout{display:grid;grid-template-columns:320px 1fr;gap:16px;}
@media(max-width:900px){.layout{grid-template-columns:1fr;}}

/* KPIs */
.kpi-row{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px;}
.kpi{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:14px 16px;}
.kpi-val{font-family:'Space Grotesk',sans-serif;font-size:24px;font-weight:800;}
.kpi-lbl{font-size:11px;color:var(--muted);margin-top:2px;}

/* AGENT STATUS CARDS */
.section-title{font-size:10px;letter-spacing:2px;color:var(--muted);font-weight:700;
  text-transform:uppercase;margin-bottom:10px;}
.agents-grid{display:flex;flex-direction:column;gap:6px;}
.agent-card{background:var(--card);border:1px solid var(--border);border-radius:10px;
  padding:10px 14px;display:flex;align-items:center;gap:10px;cursor:default;
  transition:border-color .2s;}
.agent-card:hover{border-color:rgba(255,255,255,.14);}
.agent-icon{font-size:18px;flex-shrink:0;width:28px;text-align:center;}
.agent-info{flex:1;min-width:0;}
.agent-name{font-size:12px;font-weight:600;color:var(--text);}
.agent-action{font-size:11px;color:var(--muted);margin-top:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.status-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;}
.status-idle   {background:#334155;}
.status-running{background:var(--blue);animation:pulse 1s infinite;}
.status-success{background:var(--green);}
.status-error  {background:var(--red);}

/* LIVE FEED */
.feed-wrap{background:var(--card);border:1px solid var(--border);border-radius:14px;
  padding:16px;height:calc(100vh - 280px);min-height:400px;display:flex;flex-direction:column;}
.feed-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;}
.feed-scroll{flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:4px;}
.feed-scroll::-webkit-scrollbar{width:4px;}
.feed-scroll::-webkit-scrollbar-track{background:transparent;}
.feed-scroll::-webkit-scrollbar-thumb{background:rgba(255,255,255,.08);border-radius:2px;}
.event{display:flex;align-items:flex-start;gap:8px;padding:7px 10px;border-radius:7px;
  font-size:12px;animation:fadeIn .3s ease;}
@keyframes fadeIn{from{opacity:0;transform:translateY(-4px);}to{opacity:1;transform:none;}}
.event-icon{font-size:11px;font-family:'JetBrains Mono',monospace;font-weight:600;
  flex-shrink:0;width:14px;text-align:center;margin-top:1px;}
.event-body{flex:1;min-width:0;}
.event-meta{display:flex;align-items:center;gap:6px;margin-bottom:2px;}
.event-agent{font-weight:600;font-size:11px;}
.event-time{color:var(--muted);font-size:10px;font-family:'JetBrains Mono',monospace;}
.event-msg{color:#cbd5e1;line-height:1.4;}
.event-data{color:var(--muted);font-size:10px;font-family:'JetBrains Mono',monospace;
  margin-top:2px;word-break:break-all;}

/* FILTER BUTTONS */
.filters{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px;}
.filter-btn{font-size:10px;font-weight:600;padding:3px 10px;border-radius:12px;cursor:pointer;
  border:1px solid;background:transparent;transition:all .2s;}
.filter-btn.active{background:rgba(255,255,255,.08);}
.filter-btn:hover{background:rgba(255,255,255,.06);}

/* BOTTOM BAR */
.bottom-bar{margin-top:16px;display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.mini-card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:12px 14px;}
.mini-card-title{font-size:10px;letter-spacing:1.5px;color:var(--muted);font-weight:700;margin-bottom:8px;}
.mini-stat{display:flex;justify-content:space-between;font-size:12px;padding:3px 0;
  border-bottom:1px solid rgba(255,255,255,.04);}
.mini-stat:last-child{border:none;}
.mini-stat-val{font-weight:600;}
</style>
</head>
<body>
<div class="grid-bg"></div>
<div class="wrap">

  <!-- HEADER -->
  <div class="header">
    <div class="header-left">
      <h1>🖥️ AlphaBot — Live Monitor</h1>
      <p>Supervision en temps réel de tous les agents IA · Mise à jour toutes les 5s</p>
      <div id="last-update">Connexion...</div>
    </div>
    <div>
      <div class="live-badge"><div class="dot"></div>LIVE</div>
    </div>
  </div>

  <!-- KPIs TOP -->
  <div class="kpi-row" id="kpi-row">
    <div class="kpi"><div class="kpi-val" style="color:#22c55e;" id="kpi-abonnes">—</div><div class="kpi-lbl">Abonnés actifs</div></div>
    <div class="kpi"><div class="kpi-val" style="color:#3b82f6;" id="kpi-editions">—</div><div class="kpi-lbl">Éditions envoyées</div></div>
    <div class="kpi"><div class="kpi-val" style="color:#f5c842;" id="kpi-score">—</div><div class="kpi-lbl">Score Growth Booster</div></div>
  </div>

  <!-- LAYOUT PRINCIPAL -->
  <div class="layout">

    <!-- COLONNE GAUCHE : Status des agents -->
    <div>
      <div class="section-title">👔 Équipe — Statut temps réel</div>
      <div class="agents-grid" id="agents-grid">
        <!-- Rempli par JS -->
      </div>

      <!-- Mini stats -->
      <div class="bottom-bar" style="margin-top:12px;grid-template-columns:1fr;">
        <div class="mini-card">
          <div class="mini-card-title">📊 KPIs ENTREPRISE</div>
          <div class="mini-stat"><span>Abonnés humains</span><span class="mini-stat-val" id="st-humains" style="color:#22c55e;">—</span></div>
          <div class="mini-stat"><span>Abonnés simulation</span><span class="mini-stat-val" id="st-simul" style="color:#64748b;">—</span></div>
          <div class="mini-stat"><span>Revenus totaux</span><span class="mini-stat-val" id="st-revenus" style="color:#f5c842;">—</span></div>
          <div class="mini-stat"><span>Pipeline prospects</span><span class="mini-stat-val" id="st-prospects" style="color:#8b5cf6;">—</span></div>
        </div>
      </div>
    </div>

    <!-- COLONNE DROITE : Live feed -->
    <div>
      <div class="feed-wrap">
        <div class="feed-header">
          <div class="section-title" style="margin-bottom:0;">⚡ ACTIVITÉ EN DIRECT</div>
          <div style="display:flex;gap:8px;align-items:center;">
            <div class="filters" id="filters">
              <button class="filter-btn active" style="color:#e2e8f0;border-color:rgba(255,255,255,.15);" data-filter="all">Tous</button>
              <button class="filter-btn" style="color:#22c55e;border-color:rgba(34,197,94,.3);" data-filter="success">Succès</button>
              <button class="filter-btn" style="color:#ef4444;border-color:rgba(239,68,68,.3);" data-filter="error">Erreurs</button>
              <button class="filter-btn" style="color:#f5c842;border-color:rgba(245,200,66,.3);" data-filter="milestone">Milestones</button>
            </div>
          </div>
        </div>
        <div class="feed-scroll" id="feed">
          <div style="color:var(--muted);text-align:center;padding:40px;font-size:13px;">
            ⏳ En attente d'activité...
          </div>
        </div>
      </div>
    </div>

  </div>
</div>

<script>
// ── Config ────────────────────────────────────────────────────────────────────
const REFRESH_MS   = 5000;
const AGENT_ICONS  = {
  "Directeur Adjoint":    "🤝",
  "Agent Veille":         "📡",
  "Agent Analyste":       "🧠",
  "Agent Rédacteur":      "✍️",
  "Agent Growth":         "📈",
  "Agent Growth Booster": "🚀",
  "Agent Commercial":     "💼",
  "Agent Analytics":      "📊",
  "Agent CFO":            "💰",
  "Agent CEO Brief":      "👔",
  "Monitor":              "🖥️",
};
const EVENT_ICONS  = { start:"▶", progress:"⟳", success:"✓", error:"✕", warning:"⚠", info:"ℹ", milestone:"★" };
const EVENT_COLORS = {
  start:"#3b82f6", progress:"#f59e0b", success:"#22c55e",
  error:"#ef4444",  warning:"#f59e0b",  info:"#64748b", milestone:"#f5c842"
};
const EVENT_BG = {
  start:"rgba(59,130,246,.07)", progress:"rgba(245,158,11,.07)",
  success:"rgba(34,197,94,.07)", error:"rgba(239,68,68,.07)",
  warning:"rgba(245,158,11,.05)", info:"rgba(100,116,139,.05)", milestone:"rgba(245,200,66,.1)"
};

let activeFilter = "all";
let lastEventTs  = null;
let allEvents    = [];

// ── Fetch data ────────────────────────────────────────────────────────────────
async function fetchData() {
  try {
    const [evRes, kpiRes] = await Promise.all([
      fetch("/api/events"),
      fetch("/api/kpis"),
    ]);
    const events = await evRes.json();
    const kpis   = await kpiRes.json();
    updateFeed(events);
    updateKpis(kpis);
    updateAgentCards(events);
    document.getElementById("last-update").textContent =
      "Dernière mise à jour : " + new Date().toLocaleTimeString("fr-FR");
  } catch(e) {
    document.getElementById("last-update").textContent = "⚠️ Erreur de connexion";
  }
}

// ── Feed ──────────────────────────────────────────────────────────────────────
function updateFeed(events) {
  allEvents = events;
  renderFeed();
}

function renderFeed() {
  const feed = document.getElementById("feed");
  const filtered = activeFilter === "all"
    ? allEvents
    : allEvents.filter(e => e.type === activeFilter);

  if (!filtered.length) {
    feed.innerHTML = '<div style="color:var(--muted);text-align:center;padding:40px;font-size:13px;">Aucune activité pour ce filtre</div>';
    return;
  }

  const prevScrollTop = feed.scrollTop;
  const atBottom = feed.scrollHeight - feed.clientHeight - prevScrollTop < 40;

  feed.innerHTML = filtered.map(e => {
    const ts    = new Date(e.ts);
    const time  = ts.toLocaleTimeString("fr-FR", {hour:"2-digit",minute:"2-digit",second:"2-digit"});
    const date  = ts.toLocaleDateString("fr-FR", {day:"2-digit",month:"2-digit"});
    const icon  = EVENT_ICONS[e.type]  || "•";
    const color = EVENT_COLORS[e.type] || "#64748b";
    const bg    = EVENT_BG[e.type]     || "rgba(255,255,255,.03)";
    const agentIcon = AGENT_ICONS[e.agent] || "🤖";
    const dataStr = e.data && Object.keys(e.data).length
      ? JSON.stringify(e.data) : "";
    return `
    <div class="event" style="background:${bg};">
      <div class="event-icon" style="color:${color};">${icon}</div>
      <div class="event-body">
        <div class="event-meta">
          <span class="event-agent" style="color:${color};">${agentIcon} ${e.agent}</span>
          <span class="event-time">${date} ${time}</span>
        </div>
        <div class="event-msg">${e.message}</div>
        ${dataStr ? `<div class="event-data">${dataStr}</div>` : ""}
      </div>
    </div>`;
  }).join("");

  if (atBottom) feed.scrollTop = feed.scrollHeight;
}

// ── Agent cards ───────────────────────────────────────────────────────────────
function updateAgentCards(events) {
  const statuts = {};
  for (const [name, icon] of Object.entries(AGENT_ICONS)) {
    statuts[name] = {icon, statut:"idle", action:"Aucune activité récente"};
  }
  for (const e of [...events].reverse()) {
    if (!statuts[e.agent]) {
      statuts[e.agent] = {icon:"🤖", statut:"idle", action:"—"};
    }
    const s = statuts[e.agent];
    if (!s._set) {
      s.action = e.message.substring(0,60);
      s.statut  = e.type === "start" ? "running"
                : e.type === "error" ? "error"
                : e.type === "success" ? "success"
                : "idle";
      s._set = true;
    }
  }

  const grid = document.getElementById("agents-grid");
  grid.innerHTML = Object.entries(statuts).map(([name, s]) => {
    const dotClass = {running:"status-running", error:"status-error", success:"status-success", idle:"status-idle"}[s.statut] || "status-idle";
    const nameColor = s.statut === "running" ? "#93c5fd" : s.statut === "error" ? "#fca5a5" : s.statut === "success" ? "#86efac" : "#e2e8f0";
    return `
    <div class="agent-card">
      <div class="agent-icon">${s.icon}</div>
      <div class="agent-info">
        <div class="agent-name" style="color:${nameColor};">${name}</div>
        <div class="agent-action">${s.action}</div>
      </div>
      <div class="status-dot ${dotClass}"></div>
    </div>`;
  }).join("");
}

// ── KPIs ──────────────────────────────────────────────────────────────────────
function updateKpis(k) {
  document.getElementById("kpi-abonnes").textContent = k.abonnes_total ?? "—";
  document.getElementById("kpi-editions").textContent = k.editions ?? "—";
  document.getElementById("kpi-score").textContent = (k.booster_score ?? 0) + " pts";
  document.getElementById("st-humains").textContent  = k.abonnes_humains ?? "—";
  document.getElementById("st-simul").textContent    = (k.abonnes_total ?? 0) - (k.abonnes_humains ?? 0);
  document.getElementById("st-revenus").textContent  = (k.revenus ?? 0) + "€";
  document.getElementById("st-prospects").textContent= k.prospects ?? "—";
}

// ── Filters ───────────────────────────────────────────────────────────────────
document.getElementById("filters").addEventListener("click", e => {
  const btn = e.target.closest(".filter-btn");
  if (!btn) return;
  document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  activeFilter = btn.dataset.filter;
  renderFeed();
});

// ── Démarrage ─────────────────────────────────────────────────────────────────
fetchData();
setInterval(fetchData, REFRESH_MS);
</script>
</body>
</html>"""


# ─── Handler HTTP ─────────────────────────────────────────────────────────────

class MonitorHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # Silencer les logs HTTP par défaut
        pass

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/" or path == "/index.html":
            self._send(200, "text/html; charset=utf-8", DASHBOARD_HTML.encode("utf-8"))

        elif path == "/api/events":
            events = lire_events(300)
            body = json.dumps(events, ensure_ascii=False).encode("utf-8")
            self._send(200, "application/json; charset=utf-8", body)

        elif path == "/api/kpis":
            kpis = lire_kpis()
            body = json.dumps(kpis, ensure_ascii=False).encode("utf-8")
            self._send(200, "application/json; charset=utf-8", body)

        elif path == "/api/status":
            events  = lire_events(300)
            statuts = statut_agents(events)
            body    = json.dumps(statuts, ensure_ascii=False, default=str).encode("utf-8")
            self._send(200, "application/json; charset=utf-8", body)

        else:
            self._send(404, "text/plain", b"Not found")

    def _send(self, code: int, content_type: str, body: bytes):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)


# ─── Démarrage du serveur ─────────────────────────────────────────────────────

def run(port: int = 8080, open_browser: bool = True):
    from utils.activity_logger import log_event
    log_event("Monitor", "start", f"Dashboard Live Monitor démarré sur http://localhost:{port}")

    server = HTTPServer(("", port), MonitorHandler)
    url    = f"http://localhost:{port}"

    print(f"\n╔══════════════════════════════════════════════════════╗")
    print(f"║  🖥️  AlphaBot — Live Monitor                         ║")
    print(f"║  URL : {url:<46}║")
    print(f"║  Mise à jour toutes les 5 secondes                   ║")
    print(f"║  Ctrl+C pour arrêter                                 ║")
    print(f"╚══════════════════════════════════════════════════════╝\n")

    if open_browser:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log_event("Monitor", "info", "Dashboard arrêté par l'utilisateur")
        print("\n🛑 Monitor arrêté.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AlphaBot Live Monitor")
    parser.add_argument("--port",      type=int, default=8080, help="Port (défaut: 8080)")
    parser.add_argument("--no-browser", action="store_true", help="Ne pas ouvrir le navigateur")
    args = parser.parse_args()
    run(port=args.port, open_browser=not args.no_browser)
