/* ─────────────────────────────────────────────
   Filmstrip portfolio (A2 "The Filmstrip")
   Content research-verified 2026-06-21 (plan approval = content approval).
   Loaded with defer; DOM is parsed before this runs.
   ───────────────────────────────────────────── */
(function () {
  'use strict';

  /* ---- DATA (approved Content Appendix) ---- */
  const projects = [
    {
      "num": "01", "name": "The Grove", "url": "thegrove.pro",
      "desc": "The LifeOS I built for my family and me",
      "tag": "Personal LifeOS · Multi-agent · Live 2026",
      "shot": "shots/thegrove-pro.jpg",
      "problem": "I had a good life on paper and no real visibility into it. Work follow-ups fell through the cracks. Recovery commitments competed with everything else. I was using my own memory as the system, and my memory had a spotty track record.",
      "solution": "I built a personal operating system - five domains, 20 AI agents, structured sprints, a progressive trust model that governs how much the system can act without me. It captures email, messages, and calendar. It composes my morning. It surfaces what I said I'd do. It tends to my life when I'd rather not.",
      "stack": ["Claude Code + multi-agent sprint pipeline", "Python / FastAPI / PostgreSQL", "Hermes agent layer", "Docker self-hosted"],
      "quote": "I didn't build this because I love productivity tools. I built it because I kept losing track of the things that mattered most."
    },
    {
      "num": "02", "name": "Human in the Loop", "url": "humanintheloop.stream",
      "desc": "A live show about AI, built with AI",
      "tag": "Media · LinkedIn Live · Weekly since Mar 2026",
      "shot": "shots/hitl.jpg",
      "problem": "Most AI content is polished demos on controlled data. You can't tell what AI tools actually feel like to use on messy, real work - and what breaks.",
      "solution": "Sash Mohapatra and I run a weekly 15-minute LinkedIn Live show where two practitioners pick one AI tool and use it live against real workflows. No script, no retakes. The production stack - admin portal, Echo RAG chatbot, YouTube Shorts pipeline, OBS overlays - automates everything after we say \"see you next week.\"",
      "stack": ["LinkedIn Live + OBS + VDO.Ninja", "Cloudflare Pages (static site)", "FastAPI + CouchDB (admin + API)", "React 19 + Vite (admin frontend)", "pgvector + Gemini (Echo RAG)"],
      "quote": "Hosts talk, machines ship. Everything after 'see you next week' is automated - no checklists, no portals, no exceptions."
    },
    {
      "num": "03", "name": "iLink Tools", "url": "ilink.tools",
      "desc": "Tools I built with Agents so my team sells smarter",
      "tag": "FSI AI Platform · 12+ tools · Live",
      "shot": "shots/ilink-tools.jpg",
      "problem": "FSI sales cycles die in discovery. You can't differentiate with a deck when every Microsoft partner claims the same AI capabilities. iLink needed a way to compress months of \"show them what we can do\" into a single sales call.",
      "solution": "A live portfolio of 12+ working AI tools for FSI customers and Microsoft sellers - opened on a laptop during the meeting, not described in a follow-up proposal. FabricGuard validates Azure Fabric BCDR in real time. iBrief pulls SEC filings and generates a talk track in seconds. WireDesk demos AI document review with GPT-4.1 vision. One of those tools - SignalScope - became WayFact.",
      "stack": ["React + Vite", "FastAPI + Flask", "Azure VM + Cosmos DB", "Claude API (Anthropic)", "Azure OpenAI (GPT-4.1)", "Cloudflare Pages + Tunnel", "Docker Compose"],
      "quote": "iLink doesn't talk about innovation. iLink builds it."
    },
    {
      "num": "04", "name": "AG Law", "url": "dev.aguptalaw.com",
      "desc": "Agents handle the paperwork - Lawyers handle the people",
      "tag": "Legal AI · Estate Planning · Live Mar 2026",
      "shot": "shots/aglaw.jpg",
      "problem": "In a solo estate planning practice, the attorney is also the administrator. Every hour spent on billing, scheduling, and document overhead is an hour not spent with clients - and in estate planning, the client relationship is the whole job.",
      "solution": "A purpose-built practice management system that handles the operational layer so the attorney can focus on people. AI provides document structure and research for Wills, Trusts, POAs, and Healthcare Directives as a starting point - the attorney reviews, edits, and signs off on every word before any client sees it. 41 deterministic Georgia O.C.G.A. compliance checks run on every document. A Chief of Staff Agent streamlines it all.",
      "stack": ["React + Vite + Tailwind v4", "FastAPI + CouchDB", "Claude Sonnet", "python-docx + DRAFT watermark", "Telegram bot", "Stripe", "Docker on VPS"],
      "quote": "Every document goes to the attorney before it goes anywhere else. That's not a disclaimer - that's the architecture."
    },
    {
      "num": "05", "name": "Twelfth.help", "url": "twelfth.help",
      "desc": "Carrying the message to the person who needs it",
      "tag": "Recovery · Daily delivery · Live 2026",
      "shot": "shots/twelfth-help.jpg",
      "problem": "Step work is hard to start and easy to abandon - especially the writing. The work happens between sponsor calls, in the quiet moments when there's no meeting and no one checking in.",
      "solution": "A shared step-work portal where the sponsor holds the account and controls advancement. The sponsee answers one question at a time. Kiran - a Telegram bot - carries one question every morning: one tap, one answer, no app to open. No AI reads what you write. Access requires a sponsor; there's no public signup.",
      "stack": ["FastAPI + asyncpg", "React 19 + TypeScript + Tailwind v4 (Cloudflare Pages)", "PostgreSQL with Fernet at-rest encryption", "Telegram bot (deterministic, no LLM)", "LaunchAgent cron on Mac Mini"],
      "quote": "AI helped build this. AI does not run it. No model reads what you write."
    },
    {
      "num": "06", "name": "TheGrove AI, LLC", "url": "thegrove.llc",
      "desc": "I help teams figure out what AI actually changes",
      "tag": "TheGrove AI LLC · Atlanta, GA · Est. 2026",
      "shot": "shots/thegrove-llc.jpg",
      "problem": "Teams that want to build with AI keep getting decks about AI. What they need is someone who can show up, understand the real workflow, and ship a working system - not a proposal, a prototype you can click through by the end of the first call.",
      "solution": "CTO-as-a-Service for agentic AI systems. Multi-agent orchestration, production infrastructure, Microsoft ecosystem integration - built by someone who spent 8 years selling it and now builds it instead. One-week end-to-end delivery. The LLC is also the holding entity for TheGrove, Twelfth.help, and WayFact.",
      "stack": ["Fractional CTO retainer ($5K-15K/mo)", "Project builds end-to-end ($15K-40K)", "AI Strategy Workshops ($2K-5K)", "Georgia LLC est. May 2026"],
      "quote": "You get a working system by the end of our first conversation. That's what 'shipped, not pitched' actually means."
    }
  ];

  /* ---- BUILD CARDS ---- */
  const filmstrip = document.getElementById('portfolio');
  const progressDots = document.getElementById('progressDots');
  if (!filmstrip || !progressDots) return;

  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  projects.forEach((p, i) => {
    const card = document.createElement('div');
    card.className = 'card' + (i === 0 ? ' active' : '');
    card.dataset.index = i;
    card.setAttribute('role', 'button');
    card.setAttribute('tabindex', '0');
    card.setAttribute('aria-label', 'Open ' + p.name + ' case study');

    card.innerHTML =
      '<div class="card-inner">' +
        '<div class="chrome-bar">' +
          '<div class="chrome-dots">' +
            '<div class="chrome-dot dot-red"></div>' +
            '<div class="chrome-dot dot-yellow"></div>' +
            '<div class="chrome-dot dot-green"></div>' +
          '</div>' +
          '<div class="chrome-url">' + esc(p.url) + '</div>' +
        '</div>' +
        '<div class="card-screenshot">' +
          '<img src="' + esc(p.shot) + '" alt="' + esc(p.name) + ' screenshot" loading="' + (i < 2 ? 'eager' : 'lazy') + '">' +
          '<div class="loop-badge">● LOOP</div>' +
        '</div>' +
        '<div class="card-label">' +
          '<div class="card-num">' + esc(p.num) + '</div>' +
          '<div class="card-name">' + esc(p.name) + '</div>' +
          '<div class="card-desc">' + esc(p.desc) + '</div>' +
        '</div>' +
      '</div>';

    card.addEventListener('click', () => openDrawer(i, card));
    card.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openDrawer(i, card); }
    });

    filmstrip.appendChild(card);

    const dot = document.createElement('div');
    dot.className = 'progress-dot' + (i === 0 ? ' active' : '');
    dot.dataset.index = i;
    progressDots.appendChild(dot);
  });

  /* ---- ACTIVE CARD DETECTION ---- */
  const cards = () => filmstrip.querySelectorAll('.card');
  const dots  = () => progressDots.querySelectorAll('.progress-dot');
  const progressCounter = document.getElementById('progressCounter');

  let activeIndex = 0;
  let rafPending = false;

  function updateActive() {
    rafPending = false;
    const containerCenter = filmstrip.scrollLeft + filmstrip.clientWidth / 2;
    let closestIdx = 0;
    let closestDist = Infinity;

    cards().forEach((card, i) => {
      const cardCenter = card.offsetLeft + card.offsetWidth / 2;
      const dist = Math.abs(cardCenter - containerCenter);
      if (dist < closestDist) { closestDist = dist; closestIdx = i; }
    });

    if (closestIdx !== activeIndex) {
      activeIndex = closestIdx;
      cards().forEach((c, i) => c.classList.toggle('active', i === activeIndex));
      dots().forEach((d, i)  => d.classList.toggle('active', i === activeIndex));
      if (progressCounter) {
        progressCounter.textContent =
          String(activeIndex + 1).padStart(2, '0') + ' / ' + String(projects.length).padStart(2, '0');
      }
    }
  }

  filmstrip.addEventListener('scroll', () => {
    if (!rafPending) { rafPending = true; requestAnimationFrame(updateActive); }
    hideHint();
  }, { passive: true });

  /* ---- DRAG TO SCROLL ---- */
  let isDragging = false;
  let dragStartX = 0;
  let scrollStartLeft = 0;

  filmstrip.addEventListener('mousedown', e => {
    isDragging = true;
    dragStartX = e.pageX;
    scrollStartLeft = filmstrip.scrollLeft;
    filmstrip.classList.add('is-dragging');
  });
  window.addEventListener('mousemove', e => {
    if (!isDragging) return;
    e.preventDefault();
    filmstrip.scrollLeft = scrollStartLeft - (e.pageX - dragStartX);
  });
  window.addEventListener('mouseup', () => {
    if (!isDragging) return;
    isDragging = false;
    filmstrip.classList.remove('is-dragging');
  });

  /* ---- SCROLL HINT ---- */
  const scrollHint = document.getElementById('scrollHint');
  let hintHidden = false;
  function hideHint() {
    if (!hintHidden && scrollHint) { hintHidden = true; scrollHint.classList.add('hidden'); }
  }

  /* ---- DRAWER ---- */
  const drawer        = document.getElementById('drawer');
  const drawerOverlay = document.getElementById('drawerOverlay');
  const drawerClose   = document.getElementById('drawerClose');
  let lastTrigger = null; // AC-7: focus returns to the triggering card

  function openDrawer(idx, triggerEl) {
    const p = projects[idx];
    lastTrigger = triggerEl || cards()[idx] || null;

    document.getElementById('drawerHeroImg').src  = esc(p.shot);
    document.getElementById('drawerHeroImg').alt  = p.name + ' screenshot';
    document.getElementById('drawerNum').textContent      = p.num;
    document.getElementById('drawerName').textContent     = p.name;
    document.getElementById('drawerUrl').textContent      = p.url;
    document.getElementById('drawerUrl').href             = 'https://' + esc(p.url);
    document.getElementById('drawerTag').textContent      = p.tag;
    document.getElementById('drawerProblem').textContent  = p.problem;
    document.getElementById('drawerSolution').textContent = p.solution;
    document.getElementById('drawerQuote').textContent    = '“' + p.quote + '”';

    const stackEl = document.getElementById('drawerStack');
    stackEl.innerHTML = '';
    p.stack.forEach(s => {
      const chip = document.createElement('span');
      chip.className = 'drawer-stack-item';
      chip.textContent = s;
      stackEl.appendChild(chip);
    });

    drawer.classList.add('open');
    drawerOverlay.classList.add('open');
    document.body.style.overflow = 'hidden';
    drawerClose.focus();
  }

  function closeDrawer() {
    drawer.classList.remove('open');
    drawerOverlay.classList.remove('open');
    document.body.style.overflow = '';
    if (lastTrigger && typeof lastTrigger.focus === 'function') {
      lastTrigger.focus();
    }
    lastTrigger = null;
  }

  if (drawerClose)   drawerClose.addEventListener('click', closeDrawer);
  if (drawerOverlay) drawerOverlay.addEventListener('click', closeDrawer);
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && drawer && drawer.classList.contains('open')) closeDrawer();
  });

  /* ---- INIT ---- */
  updateActive();
})();
