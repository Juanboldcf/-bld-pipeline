/* Oficina BLD — núcleo compartido por las dos vistas (profesional y pixel). LOCAL ONLY.
 * Datos (/api/office), estado por agente y proyecto, terminal inferior, chat lateral con contexto,
 * creación de proyectos y visor de archivos. Cada vista llama Office.start({render, avatar, palette}). */
(function () {
  const $ = (s, r = document) => r.querySelector(s);
  const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const PRIORITY = ["working", "question", "done", "recent", "delivered", "idle"];
  const PCOLORS = ["#41a6f6", "#ef7d57", "#38b764", "#b13e53", "#ffcd75", "#73eff7", "#a7f070", "#d77bba"];
  const EV = { start: "empezó", stop: "terminó", write: "escribió", question: "preguntó" };
  const STATE = { working: "Trabajando", recent: "Actividad reciente", done: "Terminó", question: "Tiene preguntas", delivered: "Ya entregó", idle: "Sin actividad" };
  const QUICK = {
    agent: ["¿Qué entregaste en este proyecto?", "¿Qué te está bloqueando?", "¿Qué preguntas abiertas tienes para mí?", "Resume tu estado en 3 puntos"],
    boss: ["¿Cómo va su trabajo?", "¿Qué riesgos ves en este proyecto?", "¿Qué decisión necesitas de mí?", "¿Qué sigue en el pipeline?"],
  };
  const TYPE_META = {
    FEA: { n: "Feature", d: "Algo nuevo del producto: PR, PRD, historias de usuario", i: "🧩", c: "#3b5dc9" },
    DIS: { n: "Diseño", d: "Flujos, prototipos y pantallas UX/UI", i: "🎨", c: "#c23c85" },
    INV: { n: "Investigación", d: "Mercado, voz del cliente y discovery", i: "🔭", c: "#257179" },
    MET: { n: "Seguimiento de métricas", d: "KRs, dashboards y reportes periódicos", i: "📊", c: "#8a4fb3" },
    CAM: { n: "Campaña", d: "Incentivos, cashback y modelo de ROI", i: "📣", c: "#d9822b" },
    OTR: { n: "Otro", d: "Cualquier otra iniciativa", i: "📁", c: "#566c86" },
  };
  const fmtDate = ts => ts ? new Date(ts * 1000).toLocaleDateString("es-CO", { day: "numeric", month: "short" }) : "";
  const hhmm = d => d.toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit", hour12: false });

  const LAMP_ICON = { question: "▲", hand: "◆", working: "●", idle: "○" }; // un estado = un color + una forma + una palabra

  const Office = {
    esc, $, STATE, TYPE_META, fmtDate, data: null, cur: "", token: "", view: {}, busy: false, timer: null,
    seen: (() => { try { const v = JSON.parse(localStorage.getItem("office.seen") || "{}"); return v && typeof v === "object" ? v : {}; } catch (e) { return {}; } })(),
    chat: { agent: null, project: "", mode: "agent", logs: {} },
    dockTab: "feed", dockOpen: true, tctx: null, tlogs: {}, tbusy: false,
    side: { room: null, back: null }, rf: { filter: "all", q: "", group: false }, rexp: {},

    async start(view) {
      this.view = view;
      const saved = localStorage.getItem("office.cur");
      if (saved !== null) this.cur = saved;
      this.mount();
      await this.load();
      const q = new URLSearchParams(location.search); // enlaces directos: ?chat=<agente>&mode=boss
      if (q.get("new")) this.newProject();
      if (q.get("room")) this.openRoom(q.get("room"));
      if (q.get("chat") && this.find(q.get("chat"))) this.openChat(q.get("chat"), undefined, q.get("mode") === "boss" ? "boss" : "agent");
      this.timer = setInterval(() => { if (!this.view.paused || !this.view.paused()) this.load(); }, 5000);
    },
    async load() {
      try {
        const r = await fetch("/api/office?i=" + encodeURIComponent(this.cur));
        if (!r.ok) throw new Error("http " + r.status);
        this.data = await r.json();
        this.token = this.data.token; this.lastOk = Date.now(); this.offline(false);
        if (this.cur && !this.data.current) this.cur = "";
        this.view.render && this.view.render(this.data);
        this.renderFeed(); this.updateInfo(); this.liveUI();
        if (this.chat.agent) this.renderChatHeader();
        if (this.side.room && !this.view.inlineRooms) this.renderRoom();
      } catch (e) { this.offline(true); }
    },
    // ---------- LIVE: encendido, los agentes que lances con «Ejecutar» pueden salir a internet; se apaga solo ----------
    liveUI() {
      const L = (this.data && this.data.live) || { on: false, seconds_left: 0 }; this._liveEnd = L.on ? Date.now() + L.seconds_left * 1000 : 0;
      const S = (this.data && this.data.security) || {}, chip = $("#secChip");
      if (chip) { chip.className = "o-sec " + (S.ok === true ? "ok" : S.ok === false ? "bad" : ""); chip.textContent = S.ok === true ? "🛡 Verificado" : S.ok === false ? "⚠ " + (S.alerts || []).length + " alerta(s)" : "🛡 sin verificar";
        chip.title = S.ok === null || S.ok === undefined ? "Aún no hay verificación. Ejecuta security_check.py --init y activa los hooks de sesión." : `Última verificación (${S.mode}): ${S.when}` + ((S.alerts || []).length ? "\n" + S.alerts.join("\n") : "\nSin alertas"); }
      this.liveTick(); if (!this._liveT) this._liveT = setInterval(() => this.liveTick(), 1000);
    },
    liveTick() {
      const b = document.querySelectorAll("#liveBtn"); if (!b.length) return;
      const left = this._liveEnd ? Math.max(0, Math.round((this._liveEnd - Date.now()) / 1000)) : 0, on = left > 0;
      b.forEach(x => { x.classList.toggle("on", on); x.setAttribute("aria-pressed", on);
        x.textContent = on ? `● LIVE ${Math.floor(left / 60)}:${String(left % 60).padStart(2, "0")} · Apagar` : "○ LIVE apagado · Encender";
        x.title = on ? "Los agentes que ejecutes pueden buscar en internet. Se apaga solo al llegar a 0. Clic para apagar ya." : "Enciende LIVE para que los agentes que ejecutes desde aquí puedan salir a internet (60 min, se apaga solo)."; });
      if (this._liveEnd && !on) { this._liveEnd = 0; this.load(); }
    },
    async toggleLive() {
      const on = this._liveEnd && this._liveEnd > Date.now();
      if (!on && !window.confirm("Encender LIVE\n\nDurante 60 minutos, los agentes que lances con «▶ Ejecutar» podrán buscar en internet (búsqueda y lectura de páginas web). Siguen sin shell y escriben solo en la carpeta de su proyecto.\nSe apaga solo; apágalo tú cuando termines.")) return;
      let r; try { r = await this.post("/api/live", { on: !on, minutes: 60 }); } catch (e) { r = { ok: false, json: {} }; }
      if (!r.ok) { this.print("No se pudo cambiar LIVE: " + (r.json.error || r.status), "err"); return; }
      this._liveEnd = r.json.on ? Date.now() + r.json.seconds_left * 1000 : 0; if (this.data) this.data.live = r.json; this.liveTick();
      this.print(r.json.on ? "● LIVE encendido: los agentes que ejecutes pueden salir a internet durante 60 min. Apágalo cuando terminemos." : "○ LIVE apagado: los agentes vuelven a trabajar sin internet.", r.json.on ? "who" : "muted");
    },
    offline(on) { // una luz verde vieja miente: si falla la carga, lo decimos y atenuamos las puertas
      const b = $("#oOffline"); if (!b) return;
      b.hidden = !on; document.body.classList.toggle("o-down", on);
      if (on) b.textContent = "Sin conexión con el servidor local" + (this.lastOk ? " · datos de las " + hhmm(new Date(this.lastOk)) : "") + " · reintentando";
    },
    setProject(p) { this.cur = p || ""; localStorage.setItem("office.cur", this.cur); this.load(); },

    // ---------- modelo ----------
    allAgents() { return [...this.data.front, ...this.data.rooms.flatMap(r => r.agents)]; },
    find(name) { return this.allAgents().find(a => a.name === name); },
    proj(name) { return (this.data.initiatives || []).find(p => p.name === name); },
    short(p) { const m = /^([A-Z]{3}-\d+|\d+)-/.exec(p); return m ? m[1] : (p || "—").slice(0, 10); },
    typeOf(p) { const i = this.proj(p); const t = i ? i.type : (/^([A-Z]{3})-/.exec(p || "") || [0, /^\d+-/.test(p || "") ? "FEA" : "OTR"])[1]; return { code: t, ...(TYPE_META[t] || TYPE_META.OTR) }; },
    title(p) { const i = this.proj(p); return i ? i.title : String(p || "").replace(/^([A-Z]{3}-\d+|\d+)-/, ""); },
    pcolor(p) { const pal = this.view.palette || PCOLORS; let h = 0; for (const c of p || "") h = (h * 31 + c.charCodeAt(0)) >>> 0; return pal[h % pal.length]; },
    agent(name) {
      const base = this.find(name); if (!base) return null;
      let projs = (this.data.projects[name] || []);
      if (this.cur) projs = projs.filter(p => p.project === this.cur);
      let best = null;
      for (const p of projs) if (!best || PRIORITY.indexOf(p.state) < PRIORITY.indexOf(best.state)) best = p;
      const hand = projs.some(p => p.state === "done" && p.done_at > (this.seen[name + "|" + p.project] || 0));
      return { ...base, projects: projs, state: best ? best.state : "idle",
        note: best ? best.note : "Sin actividad" + (this.cur ? " en este proyecto" : ""), hand,
        open_items: projs.reduce((n, p) => n + p.open_items, 0), files: best ? best.files : [],
        active: projs.filter(p => p.state === "working" || p.state === "done" || p.state === "question") };
    },
    stats() {
      const ag = this.allAgents().map(a => this.agent(a.name));
      const oi = this.data.state ? this.data.state.open_items : [];
      return { working: ag.filter(a => a.state === "working" || a.state === "recent").length, hands: ag.filter(a => a.hand).length,
               questions: oi.length, frena: oi.filter(q => q.blocks.replace(/\s/g, "") === "frena").length };
    },
    chips(a) {
      const list = [...a.projects].sort((x, y) => PRIORITY.indexOf(x.state) - PRIORITY.indexOf(y.state)).slice(0, 3);
      return list.map(p => `<span class="o-proj" style="--pc:${this.pcolor(p.project)}" title="${esc(p.project)} · ${esc(p.note)}">${esc(this.short(p.project))}</span>`).join("");
    },
    milestones(S) { // hitos del proyecto con fecha; el primero sin cumplir es «próximo»
      const nx = S.stages.findIndex(x => !x.done);
      return S.stages.map((x, i) => ({ ...x, next: i === nx, date: fmtDate(x.at) }));
    },
    invocation(a, project) {
      const folder = project ? this.data.bld_root + "/" + project : this.data.state ? this.data.state.path : this.data.bld_root;
      if (a.invoke_cmd) return `${a.invoke_cmd}\nCarpeta del proyecto: ${folder}\nGuarda el resultado en ${folder}/${a.kind === "skill" ? "storm" : "referencias"}/`;
      return `Usa el agente ${a.invoke_name || a.name} para la iniciativa ${project || this.data.focus}.\nCarpeta de trabajo: ${folder}\nLee los archivos upstream de la carpeta, escribe tu entregable ahí y deja las dudas como open items.`;
    },

    // ---------- DOM compartido ----------
    mount() {
      const el = document.createElement("div");
      el.innerHTML = `
      <div class="o-dock" id="oDock">
        <div class="o-dock-bar">
          <div class="o-tabs"><button data-tab="feed" class="on">ACTIVIDAD</button><button data-tab="term">TERMINAL</button></div>
          <span class="o-dock-info" id="oInfo"></span>
          <button class="o-x" id="oTall" title="Agrandar / achicar la terminal" aria-label="Agrandar terminal">⤢</button><button class="o-x" id="oFold" title="Plegar / desplegar" aria-label="Plegar terminal">▾</button>
        </div>
        <div class="o-dock-body">
          <div class="o-feed" id="oFeed"></div>
          <div class="o-term" id="oTerm" hidden><div class="o-out" id="oOut"></div>
            <div class="o-line"><span class="o-prompt" id="oPrompt">&gt;</span><input id="oIn" autocomplete="off" spellcheck="false" placeholder="escribe «ayuda»" aria-label="Terminal de la Oficina"><button class="o-run" id="oRun" title="Lanza al agente de verdad (pide confirmación): lee, busca en la web y escribe solo en la carpeta del proyecto" disabled>▶ Ejecutar</button></div></div>
        </div>
      </div>
      <aside class="o-chat" id="oChat" hidden>
        <div class="o-chat-head" id="oChatHead"></div>
        <div class="o-chat-log" id="oChatLog"></div>
        <div class="o-quick" id="oQuick"></div>
        <div class="o-chat-form"><textarea id="oChatIn" rows="2" placeholder="Escribe al agente…"></textarea>
          <button id="oChatSend" class="o-btn hot">Enviar</button></div>
      </aside>
      <aside class="o-chat o-room" id="oRoom" role="complementary" aria-label="Sala" hidden></aside>
      <div class="o-drawer" id="oDrawer"><div class="o-bar"><b id="oDTitle"></b><button class="o-btn" id="oDClose">Cerrar</button></div><pre id="oDBody"></pre></div>
      <div class="o-modal" id="oNew"><form class="o-sheet" id="oNewForm" autocomplete="off">
        <h3>Nuevo proyecto</h3>
        <p class="o-muted">Crea la carpeta del proyecto con su estructura estándar (<code>00-init.md</code>, <code>storm/</code>, <code>praxis/</code>, <code>disenos/</code>…). Esta app no escribe en Bold Brain: el registro se hace con <code>/bld-init</code> desde Claude Code.</p>
        <label>¿Qué tipo de proyecto es?</label>
        <div class="o-types" id="nTypes">${Object.entries(TYPE_META).map(([k, t], i) => `<label class="o-type" style="--tc:${t.c}"><input type="radio" name="nType" value="${k}" ${i === 0 ? "checked" : ""}><span class="o-type-c"><span class="o-type-i">${t.i}</span><b>${t.n}</b><small>${t.d}</small></span></label>`).join("")}</div>
        <label>Título <input id="nTitle" placeholder="Límites de tarjeta débito" required></label>
        <label>Nombre de carpeta <input id="nSlug" placeholder="limites-tarjeta-debito" pattern="[a-z0-9]+(-[a-z0-9]+)*" required></label>
        <label>ID de ADO <small>(solo si ya existe el feature; el ID del proyecto lo asigna el tipo)</small> <input id="nId" placeholder="170290" inputmode="numeric" pattern="\\d{1,9}"></label>
        <div class="o-muted" id="nPrev"></div><div class="o-err" id="nErr"></div>
        <div class="o-row"><button type="button" class="o-btn" id="nCancel">Cancelar</button><button class="o-btn hot" id="nOk">Crear proyecto</button></div>
      </form></div>
      <div class="o-toast" id="oToast" role="status" aria-live="polite"></div><div class="o-offline" id="oOffline" role="alert" hidden></div>`;
      document.body.append(...el.children);
      $("#oFold").onclick = () => { this.dockOpen = !this.dockOpen; this.applyDock(); };
      $("#oTall").onclick = () => { $("#oDock").classList.toggle("tall"); this.applyDock(); };
      document.querySelectorAll(".o-tabs button").forEach(b => b.onclick = () => { this.dockTab = b.dataset.tab; this.applyDock(); if (this.dockTab === "term") $("#oIn").focus(); });
      document.querySelectorAll("#liveBtn").forEach(b => b.onclick = () => this.toggleLive());
      $("#oRun").onclick = () => { const i = $("#oIn"); let t = i.value.trim(); if (!this.tctx) { this.openTerm(); this.print("Primero toca un agente sentado (o «hablar <agente>») para elegir quién ejecuta.", "err"); return; }
        if (!t) t = (window.prompt(`¿Qué tarea ejecuta ${this.tctx.agent} en ${this.tctx.project || "(elige un proyecto)"}?`) || "").trim(); if (!t) return; i.value = ""; this.print("> /ejecutar " + t, "cmd"); this.termRun(t); };
      $("#oIn").addEventListener("keydown", e => { if (e.key === "Enter") { const v = e.target.value; e.target.value = ""; this.run(v); } });
      $("#oChatSend").onclick = () => this.send();
      document.addEventListener("keydown", e => {
        if ((e.key === "Enter" || e.key === " ") && e.target.matches && e.target.matches('[role="button"][tabindex]')) { e.preventDefault(); e.target.click(); }
        else if (e.key === "Escape" && this.side.room && (e.target.id !== "oIn" || !e.target.value) && !document.querySelector(".o-modal.show,.o-drawer.show")) this.closeRoom();
      });
      $("#oRoom").addEventListener("click", e => this.roomClick(e));
      $("#oRoom").addEventListener("input", e => { if (e.target.id === "oRQ") { this.rf.q = e.target.value; this.renderRoom(); } });
      $("#oRoom").addEventListener("change", e => { if (e.target.id === "oRG") { this.rf.group = e.target.checked; this.renderRoom(); } });
      $("#oChatIn").addEventListener("keydown", e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); this.send(); } });
      $("#oDClose").onclick = () => $("#oDrawer").classList.remove("show");
      $("#nCancel").onclick = () => $("#oNew").classList.remove("show");
      const prev = () => { const t = ($("input[name=nType]:checked") || {}).value || "FEA", s = $("#nSlug").value.trim(), nid = ((this.data || {}).next_ids || {})[t] || t + "-001";
        $("#nPrev").innerHTML = `ID asignado: <b>${esc(nid)}</b>` + (s ? ` · Carpeta: <code>${esc(nid)}-${esc(s)}</code>` : ""); };
      this.prevId = prev; $("#nTypes").addEventListener("change", prev);
      $("#nTitle").addEventListener("input", e => { $("#nSlug").value = e.target.value.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, ""); prev(); });
      $("#nSlug").addEventListener("input", prev); $("#nId").addEventListener("input", prev);
      $("#oNewForm").addEventListener("submit", e => { e.preventDefault(); this.createProject(); });
      this.applyDock();
      this.print("Terminal de la Oficina BLD. Escribe «ayuda» para ver los comandos.", "muted");
    },
    applyDock() {
      const d = $("#oDock");
      d.classList.toggle("folded", !this.dockOpen);
      $("#oFold").textContent = this.dockOpen ? "▾" : "▴";
      document.querySelectorAll(".o-tabs button").forEach(b => b.classList.toggle("on", b.dataset.tab === this.dockTab));
      $("#oFeed").hidden = this.dockTab !== "feed"; $("#oTerm").hidden = this.dockTab !== "term";
      requestAnimationFrame(() => document.documentElement.style.setProperty("--o-dock-h", d.offsetHeight + "px"));
    },
    toast(t) { const e = $("#oToast"); e.textContent = t; e.style.display = "block"; clearTimeout(this._t); this._t = setTimeout(() => e.style.display = "none", 2400); },
    openText(title, text) { $("#oDTitle").textContent = title; $("#oDBody").textContent = text; $("#oDrawer").classList.add("show"); },
    async openFile(f, project) {
      const r = await fetch(`/api/file?i=${encodeURIComponent(project || this.data.focus)}&f=${encodeURIComponent(f)}`);
      this.openText(f, r.ok ? await r.text() : "No se pudo abrir el archivo.");
    },
    async openDefinition(name) {
      const r = await fetch("/api/agent?n=" + encodeURIComponent(name));
      this.openText("Definición · " + name, r.ok ? await r.text() : "No se pudo abrir.");
    },
    async post(url, body) {
      const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json", "X-Office-Token": this.token }, body: JSON.stringify(body || {}) });
      return { ok: r.ok, status: r.status, json: await r.json().catch(() => ({})) };
    },
    async copyInvocation(name, project) {
      await navigator.clipboard.writeText(this.invocation(this.find(name), project)); this.toast("Invocación copiada: pégala en Claude Code");
    },

    // ---------- proyectos nuevos ----------
    newProject() { $("#nErr").textContent = ""; $("#oNewForm").reset(); this.prevId(); $("#oNew").classList.add("show"); $("#nTitle").focus(); },
    async createProject() {
      $("#nOk").disabled = true; $("#nErr").textContent = "";
      const r = await this.post("/api/new-project", { title: $("#nTitle").value, slug: $("#nSlug").value.trim(), ado: $("#nId").value.trim(), type: ($("input[name=nType]:checked") || {}).value });
      $("#nOk").disabled = false;
      if (!r.ok) { $("#nErr").textContent = r.json.error || "No se pudo crear el proyecto"; return; }
      $("#oNew").classList.remove("show"); this.toast("Proyecto creado: " + this.short(r.json.name)); this.setProject(r.json.name);
    },

    // ---------- actividad ----------
    renderFeed() {
      const f = this.data.feed.filter(e => !this.cur || e.project === this.cur);
      const t = ts => new Date(ts * 1000).toLocaleTimeString("es-CO", { hour12: false });
      $("#oFeed").innerHTML = f.length ? f.map(e => {
        const a = this.find(e.agent);
        return `<div class="o-ev ${esc(e.event)}"><span class="o-t">${t(e.ts)}</span> <span class="o-proj" style="--pc:${this.pcolor(e.project)}">${esc(this.short(e.project))}</span>
          <b>${esc((a ? a.name : e.agent).replace(/^bld-/, ""))}</b> ${EV[e.event] || esc(e.event)} ${esc(e.note)}</div>`;
      }).join("") : `<div class="o-ev muted">Sin eventos todavía. Los hooks de ~/.claude/office/hooks-settings.json escriben aquí cuando un agente empieza, escribe o termina.</div>`;
      const box = $("#oFeed"); box.scrollTop = box.scrollHeight;
    },
    updateInfo() { const s = this.stats(); $("#oInfo").textContent = `${s.working} trabajando · ✋ ${s.hands} terminaron · ❓ ${s.questions}`; },

    // ---------- terminal ----------
    print(t, cls) { const o = $("#oOut"); const d = document.createElement("div"); d.className = "o-l " + (cls || ""); d.textContent = t; o.append(d); while (o.childElementCount > 800) o.firstChild.remove(); o.scrollTop = o.scrollHeight; },
    match(q) {
      q = (q || "").toLowerCase().replace(/^bld-/, ""); if (!q) return null;
      const all = this.allAgents();
      return all.find(a => a.name.replace(/^bld-/, "") === q) || all.find(a => a.name.toLowerCase().includes(q)) || null;
    },
    // ---------- terminal conversacional (hablar con un agente desde aquí; solo lectura) ----------
    setPrompt() { const c = this.tctx, p = $("#oPrompt"); if (!p) return; const rb = $("#oRun"); if (rb) { rb.disabled = !(c && c.project); rb.title = !c ? "Primero elige un agente" : !c.project ? "Elige un proyecto concreto arriba (no «Todos»)" : "Lanza al agente de verdad (pide confirmación): lee, busca en la web y escribe solo en la carpeta del proyecto"; } p.textContent = c ? c.agent.replace(/^(bld-|pm-|storm-)/, "") + (c.mode === "boss" ? " (jefe)" : "") + " ›" : (this.side.room && this.view.inlineRooms ? "sala ›" : ">"); },
    openTerm() { this.dockTab = "term"; this.dockOpen = true; this.applyDock(); const i = $("#oIn"); if (i) i.focus(); },
    talkTerm(name, mode, project) {
      const base = this.find(name); if (!base) return;
      const m = mode === "boss" && base.boss ? "boss" : "agent", sp = m === "boss" ? this.find(base.boss) : base;
      const act = (this.agent(name).projects || []).find(p => p.state === "working" || p.state === "done" || p.state === "question");
      this.tctx = { agent: name, mode: m, project: project !== undefined ? project : (this.cur || (act ? act.project : (this.data && this.data.focus)) || "") };
      this.openTerm(); this.setPrompt();
      const a = this.agent(name);
      this.print("");
      this.print(`── ${sp.name} · ${sp.role}${m === "boss" ? " (jefe de " + base.name + ")" : ""}`, "who");
      this.print(`   ${STATE[a.state] || a.state} · proyecto: ${this.tctx.project || "(general)"} · conversar es solo lectura. Para que trabaje de verdad escribe «/ejecutar <tarea>» (pide confirmación).`, "muted");
      this.print("   Escribe tu mensaje y Enter. «/salir» termina · «/jefe» habla con su jefe · «/chat» abre el panel · «@otro-agente texto» cambia de agente.", "muted");
      if (a.hand) this.print("   ✋ Este agente terminó y te espera.", "muted");
      this.view.render && this.data && this.view.render(this.data);
    },
    leaveTerm(silent) { if (this.tctx && !silent) this.print("Saliste de la conversación con " + this.tctx.agent + ".", "muted"); this.tctx = null; this.setPrompt(); this.view.render && this.data && this.view.render(this.data); },
    async termAsk(text) {
      const c = this.tctx; if (!c) return;
      if (this.tbusy) { this.print("Espera: todavía estoy esperando la respuesta anterior.", "err"); return; }
      const key = `${c.agent}|${c.project}|${c.mode}`, log = this.tlogs[key] || (this.tlogs[key] = []);
      const history = log.slice(-8).map(m => ({ role: m.role, text: String(m.text).slice(0, 1500) })), who = (this.speaker2(c) || {}).name || c.agent;
      this.tbusy = true;
      const o = $("#oOut"), wait = document.createElement("div"); wait.className = "o-l muted"; o.append(wait);
      let n = 0; const tick = setInterval(() => { wait.textContent = `${who.replace(/^(bld-|pm-|storm-)/, "")} está leyendo y pensando` + ".".repeat(1 + (n++ % 3)); o.scrollTop = o.scrollHeight; }, 400);
      wait.textContent = `${who.replace(/^(bld-|pm-|storm-)/, "")} está leyendo y pensando.`;
      let r; try { r = await this.post("/api/chat", { agent: c.agent, project: c.project, mode: c.mode, message: text, history }); } catch (e) { r = { ok: false, json: { error: "sin conexión con el servidor local" } }; }
      clearInterval(tick); wait.remove(); this.tbusy = false;
      if (!r.ok) { this.print("No se pudo responder: " + (r.json.error || r.status), "err"); return; }
      const reply = r.json.reply || "(sin respuesta)";
      log.push({ role: "user", text }, { role: "agent", text: reply });
      this.print(`${(r.json.speaker || who).replace(/^(bld-|pm-|storm-)/, "")} ›`, "who"); this.print(reply, "reply");
    },
    // ---------- modo ejecutar: lanza al agente de verdad (escribe solo en la carpeta del proyecto; pide confirmación) ----------
    async termRun(task) {
      const c = this.tctx; if (!c) { this.print("Primero elige un agente: «hablar <agente>» o toca a uno sentado.", "err"); return; }
      if (!task) { this.print("Uso: /ejecutar <tarea>   (ej. /ejecutar investiga competidores y escribe 01-market.md)", "err"); return; }
      if (!c.project) { this.print("Elige un proyecto concreto arriba (no «Todos») para poder ejecutar.", "err"); return; }
      if (this.trun) { this.print("Ya hay una ejecución en curso.", "err"); return; }
      const ok = window.confirm(`¿Ejecutar de verdad?\n\nAgente: ${c.agent}\nProyecto: ${c.project}\nTarea: ${task}\n\nEl agente podrá leer${this._liveEnd > Date.now() ? ", buscar en internet (LIVE encendido)" : " (sin internet: LIVE apagado)"} y ESCRIBIR archivos solo dentro de la carpeta de ese proyecto. No usa shell ni servicios externos.`);
      if (!ok) { this.print("Ejecución cancelada.", "muted"); return; }
      let r; try { r = await this.post("/api/run", { agent: c.agent, project: c.project, task, confirm: true }); } catch (e) { r = { ok: false, json: { error: "sin conexión con el servidor local" } }; }
      if (!r.ok) { this.print("No se pudo ejecutar: " + (r.json.error || r.status), "err"); return; }
      this.trun = r.json.id; this.print(`▶ ${c.agent} empezó a trabajar en ${c.project}. Verás la luz encendida; te aviso aquí cuando termine.`, "who");
      const id = r.json.id, t0 = Date.now();
      const poll = async () => {
        let s; try { s = await (await fetch("/api/run-status?id=" + id)).json(); } catch (e) { s = null; }
        if (s && s.status === "running" || !s) { setTimeout(poll, 4000); return; }
        this.trun = null;
        if (s.status === "done") { this.print(`✔ ${c.agent} terminó (${Math.round((Date.now() - t0) / 1000)} s):`, "who"); this.print(s.reply || "(sin resumen)", "reply"); if (this._liveEnd > Date.now()) this.print("○ LIVE sigue encendido: cuando terminemos, apágalo con el botón LIVE.", "muted"); }
        else this.print("✖ La ejecución falló: " + (s.error || "error"), "err");
        this.load && this.load();
      };
      setTimeout(poll, 4000);
    },
    speaker2(c) { const b = this.find(c.agent); return c.mode === "boss" && b && b.boss ? this.find(b.boss) : b; },
    run(line) {
      line = line.trim(); if (!line) return;
      this.print((this.tctx ? this.tctx.agent.replace(/^(bld-|pm-|storm-)/, "") + " › " : "> ") + line, "cmd");
      const at = line.match(/^@(\S+)\s*(.*)$/s);
      if (at) { const a = this.match(at[1]); if (!a) { this.print("No encontré a «" + at[1] + "». Prueba «agentes».", "err"); return; }
        this.talkTerm(a.name); if (at[2]) this.termAsk(at[2]); return; }
      { const ej = line.match(/^\/?ejecutar(?:\s+(.*))?$/is); if (ej) { this.termRun((ej[1] || "").trim()); return; } }
      if (this.tctx && !line.startsWith("/")) { this.termAsk(line); return; }
      if (!this.tctx && this.side.room && this.view.inlineRooms && !line.startsWith("/") && !/^(ayuda|help|agentes|proyectos?|sala|nuevo|estado|preguntas|hablar|jefe|abrir|limpiar|clear|salir|exit|chat)\b/i.test(line)) {
        this.print("Estás en una sala: elige con quién hablar. Toca a alguien sentado o escribe «@nombre mensaje».", "err"); return; }
      if (line.startsWith("/")) line = line.slice(1);
      const [cmd, ...rest] = line.split(/\s+/); const arg = rest.join(" "), D = this.data;
      switch (cmd.toLowerCase()) {
        case "salir": case "exit": if (this.tctx) this.leaveTerm(); else if (this.side.room) this.closeRoom(); else this.print("No hay nada de lo que salir.", "muted"); break;
        case "chat": if (this.tctx) this.openChat(this.tctx.agent, this.tctx.project, this.tctx.mode); else this.print("No hay conversación abierta. Usa «hablar <agente>».", "err"); break;
        case "ayuda": case "help":
          ["agentes                lista de agentes, estado y proyecto", "proyectos              proyectos y avance", "proyecto <id|todos>     filtra la oficina",
           "sala <nombre>          abre una sala (ej. sala storm)", "nuevo                  crea un proyecto nuevo", "estado <agente>        qué hace y en qué proyecto", "preguntas              open items pendientes",
           "hablar <agente>        conversa con el agente aquí mismo (o «@agente texto»)", "jefe <agente>          conversa con su jefe", "salir                  termina la conversación (con conversación abierta: «/salir»)", "chat                   pasa la conversación al panel lateral", "ejecutar <tarea>       (con agente abierto) lo lanza de verdad, tras confirmar; escribe solo en el proyecto", "abrir <archivo>        muestra un archivo del proyecto",
           "limpiar               borra la pantalla"].forEach(l => this.print(l)); break;
        case "nuevo": this.newProject(); break;
        case "sala": { const q = arg.toLowerCase(); const r = D.rooms.find(x => x.id.includes(q) || x.name.toLowerCase().includes(q));
          if (r) { this.openRoom(r.id); this.print("Abriendo " + r.name); } else this.print("No encontré esa sala: " + D.rooms.map(x => x.id).join(", "), "err"); break; }
        case "agentes": this.allAgents().forEach(a => { const x = this.agent(a.name); this.print(`${(x.hand ? "✋" : "  ")} ${x.name.padEnd(30)} ${x.state.padEnd(9)} ${x.projects.map(p => this.short(p.project)).join(",") || "-"}`); }); break;
        case "proyectos": D.initiatives.forEach(p => this.print(`${(p.pid || "").padEnd(8)} ${p.type_name.padEnd(12)} ${p.title}  ${p.stages_done}/${p.stages_total} hitos  ${p.open_items} preguntas${p.frena ? " (" + p.frena + " frenan)" : ""}`)); if (!D.initiatives.length) this.print("No hay proyectos. Escribe «nuevo».", "muted"); break;
        case "proyecto": {
          if (!arg || arg === "todos") { this.setProject(""); this.print("Mostrando todos los proyectos."); break; }
          const p = D.initiatives.find(i => i.name === arg || this.short(i.name) === arg || i.name.includes(arg));
          if (p) { this.setProject(p.name); this.print("Proyecto: " + p.name); } else this.print("No encontré ese proyecto.", "err"); break; }
        case "estado": {
          const a = this.match(arg); if (!a) { this.print("Agente no encontrado. Prueba «agentes».", "err"); break; }
          const x = this.agent(a.name); this.print(`${a.name} · ${a.role} · jefe: ${a.boss || "tú (PM)"}`);
          if (!x.projects.length) this.print("Sin actividad en los proyectos visibles.", "muted");
          x.projects.forEach(p => this.print(`  ${p.project}: ${p.state} — ${p.note}${p.open_items ? " (" + p.open_items + " preguntas)" : ""}`)); break; }
        case "preguntas": { const q = D.state ? D.state.open_items : []; if (!q.length) this.print("Sin preguntas abiertas.", "muted");
          q.forEach(i => this.print(`${i.id} [${i.type}${i.blocks.replace(/\s/g, "") === "frena" ? " · FRENA" : ""}] ${i.item}  (${i.file})`)); break; }
        case "hablar": case "jefe": {
          const a = arg ? this.match(arg) : (this.tctx ? this.find(this.tctx.agent) : null);
          if (!a) { this.print(arg ? "Agente no encontrado. Prueba «agentes»." : `Uso: ${cmd} <agente> (o «/${cmd}» dentro de una conversación)`, "err"); break; }
          if (cmd === "jefe" && !a.boss) { this.print(`${a.name} responde directamente a ti.`, "err"); break; }
          this.talkTerm(a.name, cmd === "jefe" ? "boss" : "agent"); break; }
        case "abrir": if (!arg) this.print("Uso: abrir <archivo>", "err"); else this.openFile(arg); break;
        case "limpiar": case "clear": $("#oOut").innerHTML = ""; break;
        default: this.print(`Comando desconocido: ${cmd}. Escribe «ayuda».`, "err");
      }
    },

    // ---------- salas (puertas) ----------
    roomStats(r) {
      const ag = r.agents.map(a => this.agent(a.name));
      const n = f => ag.filter(f).length, names = f => ag.filter(f).map(a => a.name.replace(/^(bld-|pm-|storm-)/, ""));
      const working = a => a.state === "working" || a.state === "recent", asking = a => a.state === "question" || (a.open_items > 0 && !working(a));
      return { agents: ag, total: ag.length, working: n(working), hands: n(a => a.hand), questions: n(asking), idle: n(a => a.state === "idle"),
               workingNames: names(working), handNames: names(a => a.hand), questionNames: names(asking) };
    },
    door(r) { // estado de la puerta: lo más urgente para el PM gana (pregunta > terminó > trabajando > apagada)
      const S = this.roomStats(r);
      const state = S.questions ? "question" : S.hands ? "hand" : S.working ? "working" : "idle";
      const icon = LAMP_ICON[state];
      const label = S.questions ? `${S.questions} con pregunta` : S.hands ? `${S.hands} terminó` : S.working ? `${S.working} trabajando` : "sin actividad";
      const tip = [S.questions && "Con preguntas: " + S.questionNames.join(", "), S.hands && "Terminaron: " + S.handNames.join(", "), S.working && "Trabajando: " + S.workingNames.join(", ")].filter(Boolean).join(" · ") || "Nadie trabajando ahora";
      const aria = `${r.name}: ${[S.questions && `${S.questions} con pregunta`, S.hands && `${S.hands} terminó`, S.working && `${S.working} trabajando`].filter(Boolean).join(", ") || "sin actividad"}, ${S.total} agentes`;
      return { ...S, state, icon, label, tip, aria, open: S.working > 0 };
    },
    openRoom(id, keepFilters) {
      const r = this.data.rooms.find(x => x.id === id); if (!r) return;
      this.chat.agent = null; $("#oChat").hidden = true;
      this.side = { room: id, back: null };
      if (this.view.inlineRooms) { // vista pixel: se entra a la sala (no panel lateral) y la terminal queda en la sala
        this.roomOpener = document.activeElement;
        this.view.enterRoom(r); this.view.render && this.view.render(this.data);
        this.leaveTerm(true); this.setPrompt(); this.openTerm();
        const S = this.roomStats(r);
        this.print(""); this.print(`── Entraste a ${r.name}: ${S.agents.map(a => a.name.replace(/^(bld-|pm-|storm-)/, "")).join(", ")}`, "who");
        this.print(`   ${S.working} trabajando · ${S.hands} terminaron · ${S.questions} con preguntas. Toca a alguien sentado o escribe «@nombre mensaje». «/salir» vuelve al pasillo.`, "muted");
        return;
      }
      if (!keepFilters) this.rf = { filter: "all", q: "", group: false };
      this.roomOpener = document.activeElement;
      $("#oRoom").hidden = false; document.body.classList.add("o-chat-open");
      this.renderRoom(); this.view.render && this.view.render(this.data);
      const x = $("#oRoomClose"); if (x) x.focus();
    },
    closeRoom() {
      const id = this.side.room; this.side.room = null; $("#oRoom").hidden = true;
      if (this.view.inlineRooms) { this.view.leaveRoom(); this.leaveTerm(true); } document.body.classList.remove("o-chat-open"); this.view.render && this.view.render(this.data);
      const back = id && document.querySelector(`[data-room="${id}"]`); if (back) back.focus();
    },
    renderRoom() {
      const r = this.data.rooms.find(x => x.id === this.side.room); if (!r) return;
      const S = this.roomStats(r), f = this.rf, el = $("#oRoom");
      const keep = el.querySelector(".o-rlist") ? el.querySelector(".o-rlist").scrollTop : 0, hadFocus = document.activeElement && document.activeElement.id === "oRQ";
      const pri = a => PRIORITY.indexOf(a.state) - (a.hand ? 2.5 : 0) - (a.open_items ? 0.5 : 0);
      const match = a => {
        const q = f.q.trim().toLowerCase();
        if (q && !(a.name + " " + a.role + " " + a.projects.map(p => p.project).join(" ")).toLowerCase().includes(q)) return false;
        return f.filter === "all" || (f.filter === "working" && (a.state === "working" || a.state === "recent")) || (f.filter === "hand" && a.hand)
          || (f.filter === "question" && (a.state === "question" || a.open_items > 0)) || (f.filter === "idle" && a.state === "idle");
      };
      const list = S.agents.filter(match).sort((a, b) => pri(a) - pri(b) || a.name.localeCompare(b.name));
      const row = a => {
        const open = this.rexp[a.name];
        return `<div class="o-ra ${a.state} ${a.hand ? "hand" : ""}" data-ag="${esc(a.name)}">
          <div class="o-ra-main" data-exp="${esc(a.name)}" role="button" tabindex="0" aria-expanded="${open ? "true" : "false"}"><div class="o-rav">${this.view.avatar ? this.view.avatar(a.name, a.state, 3) : esc(a.emoji)}</div>
            <div class="o-rtx"><b>${esc(a.name)}</b><small>${esc(a.role)}</small><span class="o-rnote">${esc(a.hand ? "✋ " : "")}${esc(a.note)}</span><span class="o-rchips">${this.chips(a)}</span></div>
            <div class="o-rst"><span class="o-badge ${a.state}">${esc(STATE[a.state] || a.state)}</span>${a.open_items ? `<span class="o-qn">❓ ${a.open_items}</span>` : ""}</div></div>
          <div class="o-ra-act"><button class="o-btn hot" data-talk="${esc(a.name)}">Hablar</button>${a.boss ? `<button class="o-btn" data-bossof="${esc(a.name)}">Su jefe</button>` : ""}<button class="o-btn" data-copyinv="${esc(a.name)}">Copiar invocación</button></div>
          ${open ? `<div class="o-ra-det"><p>${esc(a.description)}</p>${a.files.length ? `<div>${a.files.map(x => `<button class="o-file" data-rfile="${esc(x)}">📄 ${esc(x)}</button>`).join("")}</div>` : ""}</div>` : ""}</div>`;
      };
      let body;
      if (!list.length) body = `<div class="o-welcome">Ningún agente coincide con el filtro. <button class="o-chip" data-rclear>Quitar filtros</button></div>`;
      else if (f.group) {
        const groups = {}; list.forEach(a => { const p = (a.active[0] || a.projects[0] || {}).project || "(sin proyecto)"; (groups[p] = groups[p] || []).push(a); });
        body = Object.entries(groups).map(([p, arr]) => `<div class="o-grp"><span class="o-proj" style="--pc:${this.pcolor(p)}">${esc(this.short(p))}</span> ${esc(p)} <small>· ${arr.length}</small></div>${arr.map(row).join("")}`).join("");
      } else body = list.map(row).join("");
      const F = [["all", "Todos", S.total], ["working", "Trabajando", S.working], ["hand", "✋ Terminaron", S.hands], ["question", "❓ Preguntas", S.questions], ["idle", "Sin actividad", S.idle]];
      el.innerHTML = `<div class="o-chat-head o-room-head">
          <div class="o-ch-top"><div class="o-ch-id"><b>${esc(r.name)}</b><small>${S.total} agentes · ${S.working} trabajando · ${S.hands} terminaron · ${S.questions} con preguntas</small></div><button class="o-x" id="oRoomClose" title="Cerrar sala (Esc)" aria-label="Cerrar sala">✕</button></div>
          <div class="o-scene">${S.agents.map(a => `<span class="o-sc ${a.state} ${a.hand ? "hand" : ""}" title="${esc(a.name)} · ${esc(a.note)}">${this.view.avatar ? this.view.avatar(a.name, a.state, 3) : esc(a.emoji)}</span>`).join("")}</div>
          <div class="o-filters">${F.filter(x => x[0] === "all" || x[2] > 0 || f.filter === x[0]).map(([k, l, n]) => `<button class="o-chip ${f.filter === k ? "on" : ""}" data-rf="${k}" aria-pressed="${f.filter === k}">${esc(l)} <b>${n}</b></button>`).join("")}</div>
          <div class="o-rtools"><input id="oRQ" class="o-search" placeholder="Buscar agente, rol o proyecto…" value="${esc(f.q)}" autocomplete="off">
            <label class="o-tg"><input type="checkbox" id="oRG" ${f.group ? "checked" : ""}> Agrupar por proyecto</label>
            ${S.hands ? `<button class="o-btn hot" id="oRNext">Atender siguiente ✋ (${S.hands})</button>` : ""}</div></div>
        <div class="o-rlist">${body}</div>`;
      el.querySelector(".o-rlist").scrollTop = keep;
      if (hadFocus) { const q = $("#oRQ"); q.focus(); q.setSelectionRange(q.value.length, q.value.length); }
      if (this.view.afterChat) this.view.afterChat();
    },
    roomClick(e) {
      const t = e.target.closest("[data-talk],[data-bossof],[data-copyinv],[data-rf],[data-rclear],[data-rfile],[data-exp],#oRoomClose,#oRNext"); if (!t) return;
      const id = this.side.room;
      if (t.dataset.talk) this.openChat(t.dataset.talk, null, "agent", { back: id });
      else if (t.dataset.bossof) this.openChat(t.dataset.bossof, null, "boss", { back: id });
      else if (t.dataset.copyinv) this.copyInvocation(t.dataset.copyinv, this.cur || this.data.focus);
      else if (t.dataset.rf) { this.rf.filter = t.dataset.rf; this.renderRoom(); }
      else if (t.dataset.rclear !== undefined) { this.rf = { filter: "all", q: "", group: false }; this.renderRoom(); }
      else if (t.dataset.rfile) this.openFile(t.dataset.rfile, this.cur || this.data.focus);
      else if (t.dataset.exp) { this.rexp[t.dataset.exp] = !this.rexp[t.dataset.exp]; this.renderRoom(); }
      else if (t.id === "oRoomClose") this.closeRoom();
      else if (t.id === "oRNext") {
        const r = this.data.rooms.find(x => x.id === id), next = this.roomStats(r).agents.find(a => a.hand);
        if (next) this.openChat(next.name, null, "agent", { back: id });
      }
    },

    // ---------- chat lateral con contexto ----------
    key() { const c = this.chat; return `${c.agent}|${c.project}|${c.mode}`; },
    speaker() { const base = this.find(this.chat.agent); return this.chat.mode === "boss" && base.boss ? this.find(base.boss) : base; },
    openChat(name, project, mode, opts) {
      const a = this.agent(name) || this.find(name); if (!a) return;
      const c = this.chat; if (c.agent !== name) c.ctxOpen = undefined; c.agent = name; c.mode = mode || "agent";
      this.side = { room: null, back: (opts && opts.back) || null }; $("#oRoom").hidden = true;
      const act = (a.projects || []).find(p => p.state === "working" || p.state === "done" || p.state === "question");
      c.project = project !== undefined && project !== null ? project : (this.cur || (act ? act.project : this.data.focus) || "");
      (a.projects || []).forEach(p => { if (p.state === "done") this.seen[name + "|" + p.project] = p.done_at; });
      localStorage.setItem("office.seen", JSON.stringify(this.seen));
      $("#oChat").hidden = false; document.body.classList.add("o-chat-open");
      this.renderChatHeader(); this.renderChatLog();
      this.view.render && this.view.render(this.data);
      $("#oChatIn").focus();
    },
    closeChat() { this.chat.agent = null; this.side.back = null; $("#oChat").hidden = true; document.body.classList.remove("o-chat-open"); this.view.render && this.view.render(this.data); },
    renderChatHeader() {
      const c = this.chat, base = this.find(c.agent); if (!base) return;
      const a = this.agent(c.agent), sp = this.speaker(), P = this.proj(c.project);
      const mine = (this.data.projects[c.agent] || []).find(p => p.project === c.project);
      const spMine = (this.data.projects[sp.name] || []).find(p => p.project === c.project);
      const st = spMine ? spMine.state : "idle", note = mine ? mine.note : "Sin actividad en este proyecto";
      const nMsgs = (c.logs[this.key()] || []).length, ctxOpen = c.ctxOpen === undefined ? nMsgs === 0 : c.ctxOpen;
      const files = P ? P.files : [], oi = P ? P.open_list : [];
      const who = c.mode === "boss" ? `${esc(sp.name)} <span class="o-muted">(jefe de ${esc(base.name.replace(/^bld-/, ""))})</span>` : `${esc(sp.name)}`;
      const backRoom = this.side.back ? (this.data.rooms.find(x => x.id === this.side.back) || {}).name || "la sala" : "";
      $("#oChatHead").innerHTML = `
        ${this.side.back ? `<button class="o-btn o-back" id="oBack">← Volver a ${esc(backRoom)}</button>` : ""}
        <div class="o-ch-top"><div class="o-av">${this.view.avatar ? this.view.avatar(sp.name, a.state) : esc(sp.emoji)}</div>
          <div class="o-ch-id"><b>${esc(sp.name)}</b><small>${esc(sp.role)}</small><span class="o-badge ${st}">${esc(STATE[st] || st)}</span></div>
          <button class="o-x" id="oChatClose" title="Cerrar">✕</button></div>
        <div class="o-seg" role="tablist"><button data-mode="agent" class="${c.mode === "agent" ? "on" : ""}">Hablar con ${esc(base.name.replace(/^bld-/, ""))}</button>
          ${base.boss ? `<button data-mode="boss" class="${c.mode === "boss" ? "on" : ""}">Con su jefe · ${esc(base.boss.replace(/^bld-/, ""))}</button>` : `<span class="o-muted o-direct">Responde directo a ti</span>`}</div>
        <details class="o-ctx" ${ctxOpen ? "open" : ""}><summary>Contexto de la conversación</summary>
          <dl>
            <dt>Hablas con</dt><dd>${who}</dd>
            <dt>Proyecto</dt><dd><select id="oChatProj"><option value="">(general · sin proyecto)</option>${this.data.initiatives.map(p => `<option value="${esc(p.name)}" ${p.name === c.project ? "selected" : ""}>${esc(p.name)}</option>`).join("")}</select></dd>
            <dt>Estado de ${esc(base.name.replace(/^bld-/, ""))}</dt><dd>${esc(note)}</dd>
            <dt>Archivos que puede leer</dt><dd>${files.length ? files.map(f => `<button class="o-file" data-file="${esc(f)}">📄 ${esc(f)}</button>`).join("") : '<span class="o-muted">Aún no hay archivos en este proyecto</span>'}</dd>
            <dt>Preguntas abiertas</dt><dd>${oi.length ? oi.map(i => `<div class="o-oi ${i.blocks.replace(/\s/g, "") === "frena" ? "frena" : ""}"><b>${esc(i.id)}</b> ${esc(i.item)}</div>`).join("") : '<span class="o-muted">Ninguna</span>'}</dd>
            <dt>Alcance</dt><dd>🔒 Solo lectura: puede leer archivos y responder. No escribe ni envía nada.</dd>
          </dl>
          <div class="o-row"><button class="o-btn" id="oChatCopy">Copiar invocación</button><button class="o-btn" id="oChatDef">Ver definición</button></div>
        </details>`;
      $("#oChatClose").onclick = () => this.closeChat();
      if ($("#oBack")) $("#oBack").onclick = () => this.openRoom(this.side.back, true);
      $("#oChatHead").querySelector(".o-ctx").addEventListener("toggle", e => { c.ctxOpen = e.target.open; });
      $("#oChatHead").querySelectorAll("[data-mode]").forEach(b => b.onclick = () => { c.mode = b.dataset.mode; this.renderChatHeader(); this.renderChatLog(); });
      $("#oChatProj").onchange = e => { c.project = e.target.value; this.renderChatHeader(); this.renderChatLog(); };
      $("#oChatCopy").onclick = () => this.copyInvocation(c.agent, c.project);
      $("#oChatDef").onclick = () => this.openDefinition(c.agent);
      $("#oChatHead").querySelectorAll("[data-file]").forEach(b => b.onclick = () => this.openFile(b.dataset.file, c.project || undefined));
      $("#oChatIn").placeholder = `Escribe a ${sp.name.replace(/^bld-/, "")}… (Enter envía)`;
      if (this.view.afterChat) this.view.afterChat();
    },
    renderChatLog() {
      const c = this.chat, log = c.logs[this.key()] || (c.logs[this.key()] = []), sp = this.speaker();
      const nm = sp.name.replace(/^bld-/, "");
      $("#oChatLog").innerHTML = (log.length ? "" : `<div class="o-welcome"><b>${esc(nm)}</b> puede responder sobre ${c.project ? `el proyecto <b>${esc(c.project)}</b>` : "tu trabajo en general"}. Lee los archivos de la carpeta antes de contestar y no inventa datos.</div>`)
        + log.map(m => m.role === "sys" ? `<div class="o-msg sys">${esc(m.text)}</div>`
          : `<div class="o-msg ${m.role}"><div class="o-bub"><div class="o-who">${m.role === "user" ? "Tú" : esc(String(m.speaker || sp.name).replace(/^bld-/, ""))} <time>${esc(m.time || "")}</time></div>${esc(m.text)}</div></div>`).join("")
        + (this.busy ? `<div class="o-msg agent"><div class="o-bub o-think">${esc(nm)} está leyendo y pensando<span>…</span></div></div>` : "");
      $("#oQuick").innerHTML = QUICK[c.mode].map(q => `<button class="o-chip" data-q="${esc(q)}">${esc(q)}</button>`).join("");
      $("#oQuick").querySelectorAll("[data-q]").forEach(b => b.onclick = () => { $("#oChatIn").value = b.dataset.q; this.send(); });
      const l = $("#oChatLog"); l.scrollTop = l.scrollHeight;
    },
    async send() {
      const inp = $("#oChatIn"), text = inp.value.trim(); if (!text || this.busy || !this.chat.agent) return;
      const c = this.chat, key = this.key(), log = c.logs[key] || (c.logs[key] = []);
      const history = log.filter(m => m.role !== "sys").slice(-8).map(m => ({ role: m.role, text: String(m.text).slice(0, 1500) }));
      log.push({ role: "user", text, time: hhmm(new Date()) }); inp.value = ""; this.busy = true; this.renderChatLog();
      const r = await this.post("/api/chat", { agent: c.agent, project: c.project, mode: c.mode, message: text, history });
      this.busy = false;
      log.push(r.ok ? { role: "agent", text: r.json.reply || "(sin respuesta)", speaker: r.json.speaker, time: hhmm(new Date()) } : { role: "sys", text: "No se pudo responder: " + (r.json.error || r.status) });
      this.renderChatLog();
    },
  };
  window.Office = Office;
})();
