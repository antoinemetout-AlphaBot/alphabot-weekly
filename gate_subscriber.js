/**
 * AlphaBot Weekly — Gate Abonnés
 * ================================
 * Vérifie que l'utilisateur est abonné avant d'afficher le contenu.
 * Partage la session avec newsletter.html via sessionStorage.
 *
 * Usage : inclure ce script + ajouter <div id="ab-gate"></div> avant le contenu principal.
 * Le contenu principal doit être dans un élément avec id="ab-content" (display:none par défaut).
 */

(function(){
  const GATE_ID = 'ab-gate';
  const CONTENT_ID = 'ab-content';
  const SESSION_KEY = 'ab_user';

  // Crée le HTML du gate
  function injectGate(){
    const gate = document.getElementById(GATE_ID);
    if(!gate) return;

    gate.innerHTML = `
    <div style="max-width:440px;margin:120px auto 0;padding:0 20px;">
      <div style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.1);border-radius:20px;padding:40px;text-align:center;backdrop-filter:blur(10px);">
        <div style="font-size:48px;margin-bottom:20px;">🔐</div>
        <h2 style="font-family:'Space Grotesk',sans-serif;font-size:22px;font-weight:700;color:white;margin-bottom:10px;">Accès Abonnés</h2>
        <p style="color:#64748b;font-size:14px;margin-bottom:24px;line-height:1.6;">Cette page est réservée aux abonnés AlphaBot Weekly.<br>Entrez votre email pour y accéder.</p>
        <input id="ab-gate-email" type="email" placeholder="votre@email.com" autocomplete="email"
          style="width:100%;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);border-radius:10px;padding:13px 16px;color:white;font-size:14px;font-family:inherit;outline:none;margin-bottom:12px;transition:.2s;"
          onfocus="this.style.borderColor='#22d3ee'" onblur="this.style.borderColor='rgba(255,255,255,.12)'"
        >
        <button onclick="window._abGateVerify()"
          style="width:100%;background:linear-gradient(135deg,#3b82f6,#22d3ee);color:white;border:none;border-radius:10px;padding:13px;font-size:14px;font-weight:600;cursor:pointer;font-family:inherit;transition:.2s;">
          Accéder →
        </button>
        <div id="ab-gate-error" style="color:#ef4444;font-size:13px;margin-top:10px;display:none;"></div>
        <div style="margin-top:16px;font-size:12px;color:#64748b;">
          Pas encore abonné ? <a href="index.html" style="color:#22d3ee;text-decoration:none;">C'est gratuit →</a>
        </div>
      </div>
    </div>`;

    // Enter key
    const inp = document.getElementById('ab-gate-email');
    if(inp) inp.addEventListener('keydown', e => { if(e.key==='Enter') window._abGateVerify(); });
  }

  // Vérifie l'email
  window._abGateVerify = async function(){
    const email = document.getElementById('ab-gate-email').value.trim().toLowerCase();
    const errEl = document.getElementById('ab-gate-error');
    if(!email || !email.includes('@')){
      errEl.style.display='block';
      errEl.textContent='⚠️ Entrez un email valide.';
      return;
    }

    // Charge la liste abonnés
    let subscriberEmails = null;
    try {
      const r = await fetch('data/subscribers.json?t='+Date.now());
      const d = await r.json();
      subscriberEmails = d.emails || [];
    } catch(e){
      // Si le fichier n'existe pas, mode dev : on accepte tout
      subscriberEmails = null;
    }

    const isSubscribed = subscriberEmails === null || subscriberEmails.map(e=>e.toLowerCase()).includes(email);

    if(isSubscribed){
      sessionStorage.setItem(SESSION_KEY, email);
      showContent();
    } else {
      errEl.style.display='block';
      errEl.innerHTML='❌ Email non reconnu. <a href="index.html" style="color:#22d3ee">S\'abonner gratuitement →</a>';
    }
  };

  function showContent(){
    const gate = document.getElementById(GATE_ID);
    const content = document.getElementById(CONTENT_ID);
    if(gate) gate.style.display = 'none';
    if(content) content.style.display = 'block';
  }

  // Extrait le pseudo à partir de l'email (partie avant @)
  function getPseudoFromEmail(email){
    const pseudo = email.split('@')[0];
    return pseudo.charAt(0).toUpperCase() + pseudo.slice(1);
  }

  // Met à jour le nav-cta pour afficher le pseudo de l'utilisateur connecté
  function updateNavCTA(email){
    const navCtaBtn = document.getElementById('nav-cta-btn') || document.querySelector('.nav-cta');
    if(!navCtaBtn) return;

    const pseudo = getPseudoFromEmail(email);

    // Crée le HTML pour le profil utilisateur
    navCtaBtn.innerHTML = `
      <span style="display:inline-flex;align-items:center;gap:8px;cursor:pointer;" onclick="window._abToggleUserMenu(event)">
        <span style="display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;background:linear-gradient(135deg,var(--cyan),var(--green));border-radius:50%;font-size:10px;color:white;font-weight:700;">
          ${pseudo.charAt(0).toUpperCase()}
        </span>
        <span>${pseudo}</span>
      </span>
    `;

    // Styles du bouton utilisateur
    navCtaBtn.style.background = 'transparent';
    navCtaBtn.style.color = 'white';
    navCtaBtn.style.padding = '8px 12px';
    navCtaBtn.style.borderRadius = '8px';
    navCtaBtn.style.fontWeight = '600';
    navCtaBtn.style.fontSize = '13px';
    navCtaBtn.style.textDecoration = 'none';
    navCtaBtn.style.cursor = 'pointer';
    navCtaBtn.style.transition = 'all .2s';
    navCtaBtn.style.border = '1px solid rgba(34,211,238,0.3)';
    navCtaBtn.style.position = 'relative';

    // Hover effect
    navCtaBtn.onmouseenter = function(){
      this.style.borderColor = 'rgba(34,211,238,0.6)';
      this.style.background = 'rgba(34,211,238,0.1)';
    };
    navCtaBtn.onmouseleave = function(){
      this.style.borderColor = 'rgba(34,211,238,0.3)';
      this.style.background = 'transparent';
    };

    // Crée le dropdown menu
    createUserMenu();
  }

  // Crée le menu déroulant utilisateur
  function createUserMenu(){
    let menu = document.getElementById('ab-user-menu');
    if(!menu){
      menu = document.createElement('div');
      menu.id = 'ab-user-menu';
      menu.style.cssText = `
        position:absolute;
        top:calc(100% + 8px);
        right:0;
        background:rgba(15,23,42,0.95);
        border:1px solid rgba(34,211,238,0.3);
        border-radius:10px;
        min-width:180px;
        box-shadow:0 10px 30px rgba(0,0,0,0.3);
        display:none;
        z-index:1000;
        backdrop-filter:blur(10px);
        overflow:hidden;
      `;
      menu.innerHTML = `
        <a href="#" style="display:block;padding:12px 16px;color:white;text-decoration:none;border-bottom:1px solid rgba(255,255,255,0.1);transition:background .2s;font-size:13px;" onmouseover="this.style.background='rgba(34,211,238,0.1)'" onmouseout="this.style.background='transparent'" onclick="event.preventDefault();alert('Mon compte - À implémenter');">
          Mon compte
        </a>
        <a href="#" style="display:block;padding:12px 16px;color:#ef4444;text-decoration:none;transition:background .2s;font-size:13px;" onmouseover="this.style.background='rgba(239,68,68,0.1)'" onmouseout="this.style.background='transparent'" onclick="event.preventDefault();window._abLogout();">
          Se deconnecter
        </a>
      `;
      const navCtaBtn = document.getElementById('nav-cta-btn') || document.querySelector('.nav-cta');
      if(navCtaBtn){
        navCtaBtn.appendChild(menu);
      }
    }
  }

  // Toggle le menu utilisateur
  window._abToggleUserMenu = function(e){
    e.stopPropagation();
    const menu = document.getElementById('ab-user-menu');
    if(menu){
      menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
    }
  };

  // Ferme le menu au clic ailleurs
  document.addEventListener('click', function(){
    const menu = document.getElementById('ab-user-menu');
    if(menu) menu.style.display = 'none';
  });

  // Déconnexion
  window._abLogout = function(){
    sessionStorage.removeItem(SESSION_KEY);
    location.reload();
  };

  // Au chargement : vérifier la session existante
  document.addEventListener('DOMContentLoaded', function(){
    const saved = sessionStorage.getItem(SESSION_KEY);
    if(saved){
      updateNavCTA(saved);
      showContent();
    } else {
      injectGate();
    }
  });
})();
