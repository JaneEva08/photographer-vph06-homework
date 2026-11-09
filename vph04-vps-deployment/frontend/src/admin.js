import "./style.css";

const app = document.querySelector("#app");
const euro = (amount) => new Intl.NumberFormat("de-DE", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(Number(amount || 0));
const esc = (value = "") => String(value).replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
let currentTab = "leads";
let services = [];

async function api(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    credentials: "same-origin",
    headers: { Accept: "application/json", ...(options.body ? { "Content-Type": "application/json" } : {}), ...options.headers },
    ...options,
  });
  if (response.status === 204) return null;
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || `HTTP ${response.status}`);
  return body;
}

function shell(content, active = "") {
  app.innerHTML = `<div class="admin-shell"><aside class="admin-sidebar"><a class="admin-brand" href="/">Fotografie <small>STUDIO</small></a><p class="admin-kicker">ARBEITSBEREICH</p><nav>${[
    ["leads", "Anfragen"], ["services", "Angebote"], ["clients", "Kunden"], ["shoots", "Shootings"], ["tasks", "Aufgaben"], ["payments", "Zahlungen"], ["metrics", "Website-Statistik"], ["sheets", "Google Sheets"],
  ].map(([id, label]) => `<button class="nav-item ${active === id ? "active" : ""}" data-tab="${id}">${label}</button>`).join("")}</nav><div class="sidebar-bottom"><span>Deutschland · EUR</span><button id="logout-button" class="text-button">Abmelden</button></div></aside><main class="admin-main"><header class="admin-topbar"><div><p class="admin-kicker">FOTOGRAFIE · CRM</p><h1>${active ? ({ leads: "Anfragen", services: "Angebote", clients: "Kunden", shoots: "Shootings", tasks: "Aufgaben", payments: "Zahlungen", metrics: "Website-Statistik", sheets: "Google Sheets" }[active] || "Studio") : "Studio"}</h1></div><a class="preview-link" href="/" target="_blank" rel="noreferrer">Website ansehen ↗</a></header><section class="admin-content">${content}</section></main></div>`;
  document.querySelectorAll("[data-tab]").forEach((button) => button.addEventListener("click", () => renderTab(button.dataset.tab)));
  document.querySelector("#logout-button")?.addEventListener("click", async () => { await api("/auth/logout", { method: "POST" }); location.reload(); });
}

function authScreen(register = false) {
  app.innerHTML = `<main class="auth-shell"><a class="admin-brand" href="/">Fotografie <small>STUDIO</small></a><section class="auth-card"><p class="admin-kicker">GESCHÜTZTER BEREICH</p><h1>${register ? "Studio einrichten" : "Willkommen zurück"}</h1><p>${register ? "Legen Sie das erste Administratorkonto an. Der einmalige Einrichtungscode wird nur auf dem Server angezeigt." : "Melden Sie sich an, um Anfragen, Kunden und Shootings zu verwalten."}</p><form id="auth-form" class="auth-form">${register ? '<label>Einrichtungscode<input name="bootstrap_token" required minlength="32" autocomplete="off" /></label>' : ""}<label>Benutzername<input name="username" required autocomplete="username" minlength="3" /></label><label>Passwort<input name="password" type="password" required autocomplete="${register ? "new-password" : "current-password"}" minlength="12" /></label><button class="submit-button" type="submit">${register ? "Konto anlegen" : "Anmelden"}</button><p id="auth-error" class="form-status error" role="alert"></p></form>${register ? '<button id="back-login" class="text-button">Zur Anmeldung</button>' : ""}</section><p class="auth-foot">Private Verwaltungsoberfläche · Lernprojekt</p></main>`;
  document.querySelector("#auth-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    try {
      if (register) {
        await api("/auth/register", { method: "POST", body: JSON.stringify(Object.fromEntries(data)) });
        await api("/auth/token", { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body: new URLSearchParams({ username: data.get("username"), password: data.get("password") }) });
      } else {
        await api("/auth/token", { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body: new URLSearchParams({ username: data.get("username"), password: data.get("password") }) });
      }
      location.reload();
    } catch (error) { document.querySelector("#auth-error").textContent = error.message; }
  });
  document.querySelector("#back-login")?.addEventListener("click", () => authScreen(false));
}

function table(headers, rows, empty = "Noch keine Einträge vorhanden.") {
  return rows.length ? `<div class="table-wrap"><table><thead><tr>${headers.map((h) => `<th>${h}</th>`).join("")}</tr></thead><tbody>${rows.join("")}</tbody></table></div>` : `<div class="empty-state">${empty}</div>`;
}

async function renderTab(tab) {
  currentTab = tab;
  shell('<div class="loading-card">Lade Daten …</div>', tab);
  try {
    if (tab === "leads") await renderLeads();
    if (tab === "services") await renderServices();
    if (tab === "clients") await renderClients();
    if (tab === "shoots") await renderShoots();
    if (tab === "tasks") await renderTasks();
    if (tab === "payments") await renderPayments();
    if (tab === "metrics") await renderMetrics();
    if (tab === "sheets") await renderSheets();
  } catch (error) { shell(`<div class="error-card">${esc(error.message)} <button id="retry" class="text-button">Erneut versuchen</button></div>`, tab); document.querySelector("#retry")?.addEventListener("click", () => renderTab(tab)); }
}

async function renderLeads() {
  const rows = await api("/admin/applications?limit=300");
  const counts = { hot: rows.filter((x) => x.priority_label === "hot").length, warm: rows.filter((x) => x.priority_label === "warm").length, cold: rows.filter((x) => x.priority_label === "cold").length };
  const content = `<div class="metric-cards"><article><span>Alle Anfragen</span><strong>${rows.length}</strong></article><article><span>Heiß</span><strong>${counts.hot}</strong></article><article><span>Warm</span><strong>${counts.warm}</strong></article><article><span>Kalt</span><strong>${counts.cold}</strong></article></div><div class="panel-heading"><div><h2>Priorisierte Anfragen</h2><p>Die Bewertung nutzt Wunschtermin, Budget und Briefdetails. Sie ersetzt keine persönliche Einschätzung.</p></div><button id="seed-demo" class="secondary-button">10 Demo-Anfragen erzeugen</button></div>${table(["Priorität", "Kontakt", "Angebot", "Termin", "Budget", "Status", "Aktion"], rows.map((item) => `<tr><td><span class="priority ${esc(item.priority_label)}">${esc(item.priority_label)} · ${item.priority_score}</span></td><td><strong>${esc(item.full_name)}</strong><small>${esc(item.email)}</small></td><td>${esc(item.service_name)}<small>${esc(item.language.toUpperCase())} · ${esc(item.category)}</small></td><td>${esc(item.preferred_date || "offen")}</td><td>${euro(item.budget_eur)}</td><td><select data-status="${item.id}">${["new", "contacted", "proposal_sent", "confirmed", "completed", "cancelled"].map((s) => `<option ${s === item.status ? "selected" : ""}>${s}</option>`).join("")}</select></td><td><button class="text-button" data-detail="${item.id}">Details</button></td></tr>`), "Noch keine Anfragen eingegangen.")}<p id="action-note" class="form-status"></p>`;
  shell(content, "leads");
  document.querySelectorAll("[data-status]").forEach((select) => select.addEventListener("change", async () => { try { await api(`/admin/applications/${select.dataset.status}`, { method: "PATCH", body: JSON.stringify({ status: select.value }) }); await renderTab("leads"); } catch (e) { alert(e.message); } }));
  document.querySelectorAll("[data-detail]").forEach((button) => button.addEventListener("click", async () => { const item = await api(`/admin/applications/${button.dataset.detail}`); alert(`${item.full_name}\n${item.email}\n${item.message || "Kein Nachrichtentext"}\n\nBewertung ${item.priority_label.toUpperCase()} (${item.priority_score})\n${item.priority_reasons.join("\n")}`); }));
  document.querySelector("#seed-demo").addEventListener("click", async () => { const note = document.querySelector("#action-note"); try { const result = await api("/admin/demo/seed-priorities", { method: "POST" }); note.textContent = `${result.created} synthetische Anfragen erstellt: ${result.priorities.hot} heiß, ${result.priorities.warm} warm, ${result.priorities.cold} kalt.`; await renderTab("leads"); } catch (e) { note.textContent = e.message; } });
}

async function renderServices() {
  services = await api("/admin/services");
  const rows = services.map((x) => `<tr><td>${esc(x.category)}</td><td><strong>${esc(x.name)}</strong><small>${esc(x.description)}</small></td><td>${euro(x.min_price_eur)}–${euro(x.max_price_eur)}</td><td><span class="state-pill ${x.active ? "on" : "off"}">${x.active ? "Aktiv" : "Inaktiv"}</span></td><td><button class="text-button" data-edit="${x.id}">Bearbeiten</button>${x.active ? ` <button class="text-button danger-text" data-disable="${x.id}">Deaktivieren</button>` : ""}</td></tr>`);
  shell(`<div class="panel-heading"><div><h2>Leistungen und Preise</h2><p>Deutsch ist die Standardsprache; veröffentlichte Angaben sind Demo-Angebote, bis reale Preise festgelegt sind.</p></div><button id="new-service" class="submit-button">Angebot hinzufügen</button></div>${table(["Kategorie", "Name / Beschreibung", "Preisspanne", "Status", "Aktion"], rows, "Noch keine Angebote. Erstellen Sie mindestens fünf unterschiedliche Leistungen.")}<dialog id="service-dialog" class="service-dialog"><form id="service-form" method="dialog"><div class="dialog-head"><h2 id="dialog-title">Angebot</h2><button type="button" id="close-dialog" class="text-button">Schließen</button></div><input type="hidden" name="id"><div class="form-grid"><label>Kategorie<input name="category" required value="Portraits"></label><label>Name (DE)<input name="name" required minlength="2"></label><label>Name (EN)<input name="name_en"></label><label>Name (RU)<input name="name_ru"></label><label class="wide">Beschreibung (DE)<textarea name="description" rows="3"></textarea></label><label class="wide">Beschreibung (EN)<textarea name="description_en" rows="2"></textarea></label><label class="wide">Beschreibung (RU)<textarea name="description_ru" rows="2"></textarea></label><label>Ab (€)<input name="min_price_eur" type="number" min="0" step="0.01" required></label><label>Bis (€)<input name="max_price_eur" type="number" min="0" step="0.01" required></label><label class="wide check-line"><input name="active" type="checkbox" checked> Auf der Website anzeigen</label></div><p id="service-error" class="form-status error"></p><button class="submit-button" type="submit">Speichern</button></form></dialog>`, "services");
  const dialog = document.querySelector("#service-dialog");
  const form = document.querySelector("#service-form");
  const open = (item = null) => { form.reset(); form.elements.id.value = item?.id || ""; for (const key of ["category", "name", "name_en", "name_ru", "description", "description_en", "description_ru", "min_price_eur", "max_price_eur"]) form.elements[key].value = item?.[key] ?? (key === "category" ? "Portraits" : ""); form.elements.active.checked = item?.active ?? true; document.querySelector("#dialog-title").textContent = item ? "Angebot bearbeiten" : "Neues Angebot"; dialog.showModal(); };
  document.querySelector("#new-service").addEventListener("click", () => open());
  document.querySelector("#close-dialog").addEventListener("click", () => dialog.close());
  document.querySelectorAll("[data-edit]").forEach((button) => button.addEventListener("click", () => open(services.find((x) => x.id === Number(button.dataset.edit)))));
  document.querySelectorAll("[data-disable]").forEach((button) => button.addEventListener("click", async () => { if (confirm("Angebot von der Website nehmen? Historische Anfragen bleiben erhalten.")) { await api(`/admin/services/${button.dataset.disable}`, { method: "DELETE" }); await renderTab("services"); } }));
  form.addEventListener("submit", async (event) => { event.preventDefault(); const data = new FormData(form); const payload = Object.fromEntries(data); for (const key of ["min_price_eur", "max_price_eur"]) payload[key] = Number(payload[key]); payload.active = form.elements.active.checked; for (const key of ["name_en", "name_ru", "description_en", "description_ru"]) payload[key] ||= null; try { await api(payload.id ? `/admin/services/${payload.id}` : "/admin/services", { method: payload.id ? "PATCH" : "POST", body: JSON.stringify(payload) }); dialog.close(); await renderTab("services"); } catch (error) { document.querySelector("#service-error").textContent = error.message; } });
}

async function renderClients() {
  const rows = await api("/admin/clients");
  shell(`<div class="panel-heading"><div><h2>Kundenkartei</h2><p>Kontakte werden aus eingehenden Anfragen übernommen.</p></div></div>${table(["Kunde", "E-Mail", "Telefon", "Sprache", "Angelegt"], rows.map((x) => `<tr><td>${esc(x.full_name)}</td><td>${esc(x.email)}</td><td>${esc(x.phone || "—")}</td><td>${esc(x.language.toUpperCase())}</td><td>${new Date(x.created_at).toLocaleDateString("de-DE")}</td></tr>`))}`, "clients");
}

async function renderShoots() {
  const [rows, clients] = await Promise.all([api("/admin/shoots"), api("/admin/clients")]);
  shell(`<div class="panel-heading"><div><h2>Gebuchte Shootings</h2><p>Eine Anfrage wird erst nach Bestätigung zum Auftrag. Status, Termin und Vertragssumme können hier angepasst werden.</p></div></div>${table(["Kunde", "Kategorie / Paket", "Datum", "Status", "Vertrag (€)"], rows.map((x) => `<tr><td>${esc(clients.find((c) => c.id === x.client_id)?.full_name || `Kunde #${x.client_id}`)}</td><td>${esc(x.category)}<small>${esc(x.package_name)}</small></td><td><input aria-label="Termin Shooting ${x.id}" data-shoot-date="${x.id}" type="date" value="${esc(x.shoot_date || "")}"></td><td><select data-shoot-status="${x.id}">${["planned", "in_progress", "completed", "cancelled"].map((s) => `<option ${s === x.status ? "selected" : ""}>${s}</option>`).join("")}</select></td><td><input aria-label="Vertragssumme Shooting ${x.id}" data-shoot-amount="${x.id}" type="number" min="0" step="0.01" value="${esc(x.contract_amount_eur)}"></td></tr>`))}`, "shoots");
  document.querySelectorAll("[data-shoot-status]").forEach((control) => control.addEventListener("change", () => api(`/admin/shoots/${control.dataset.shootStatus}`, { method: "PATCH", body: JSON.stringify({ status: control.value }) })));
  document.querySelectorAll("[data-shoot-date]").forEach((control) => control.addEventListener("change", () => api(`/admin/shoots/${control.dataset.shootDate}`, { method: "PATCH", body: JSON.stringify({ shoot_date: control.value || null }) })));
  document.querySelectorAll("[data-shoot-amount]").forEach((control) => control.addEventListener("change", () => api(`/admin/shoots/${control.dataset.shootAmount}`, { method: "PATCH", body: JSON.stringify({ contract_amount_eur: Number(control.value) }) })));
}

async function renderTasks() {
  const [rows, clients, shoots] = await Promise.all([api("/admin/tasks"), api("/admin/clients"), api("/admin/shoots")]);
  shell(`<div class="panel-heading"><div><h2>Aufgaben</h2><p>Follow-up, Vorbereitung, Bearbeitung und Übergabe.</p></div><button id="new-task" class="submit-button" ${clients.length ? "" : "disabled"}>Aufgabe erstellen</button></div>${table(["Aufgabe", "Kunde", "Shooting", "Fällig", "Status", "Aktion"], rows.map((x) => `<tr><td>${esc(x.title)}</td><td>${esc(clients.find((c) => c.id === x.client_id)?.full_name || `#${x.client_id}`)}</td><td>${esc(x.shoot_id || "—")}</td><td>${esc(x.due_date || "—")}</td><td>${esc(x.status)}</td><td><select data-task="${x.id}">${["open", "in_progress", "done", "cancelled"].map((s) => `<option ${s === x.status ? "selected" : ""}>${s}</option>`).join("")}</select></td></tr>`))}<dialog id="task-dialog" class="service-dialog"><form id="task-form"><div class="dialog-head"><h2>Aufgabe hinzufügen</h2><button type="button" id="task-close" class="text-button">Schließen</button></div><label>Kunde<select name="client_id" required>${clients.map((x) => `<option value="${x.id}">${esc(x.full_name)}</option>`)}</select></label><label>Shooting<select name="shoot_id"><option value="">Ohne Shooting</option>${shoots.map((x) => `<option value="${x.id}">#${x.id} · ${esc(x.package_name)}</option>`)}</select></label><label>Titel<input name="title" required minlength="2"></label><label>Fällig am<input name="due_date" type="date"></label><button class="submit-button">Erstellen</button></form></dialog>`, "tasks");
  const dialog = document.querySelector("#task-dialog"); document.querySelector("#new-task").addEventListener("click", () => dialog.showModal()); document.querySelector("#task-close").addEventListener("click", () => dialog.close());
  document.querySelector("#task-form").addEventListener("submit", async (event) => { event.preventDefault(); const data = Object.fromEntries(new FormData(event.currentTarget)); data.client_id = Number(data.client_id); data.shoot_id = data.shoot_id ? Number(data.shoot_id) : null; data.due_date ||= null; await api("/admin/tasks", { method: "POST", body: JSON.stringify(data) }); await renderTab("tasks"); });
  document.querySelectorAll("[data-task]").forEach((select) => select.addEventListener("change", async () => { await api(`/admin/tasks/${select.dataset.task}`, { method: "PATCH", body: JSON.stringify({ status: select.value }) }); }));
}

async function renderPayments() {
  const [shoots, finance] = await Promise.all([api("/admin/shoots"), api("/admin/finance-summary")]);
  shell(`<div class="metric-cards"><article><span>Vertragssumme</span><strong>${euro(finance.contracted_eur)}</strong></article><article><span>Eingegangen (netto)</span><strong>${euro(finance.received_eur)}</strong></article><article><span>Offen</span><strong>${euro(finance.outstanding_eur)}</strong></article><article><span>Shootings</span><strong>${shoots.length}</strong></article></div><div class="panel-heading"><div><h2>Zahlungen</h2><p>Vertragssumme und tatsächlich eingegangene Beträge werden getrennt geführt. Rückerstattungen mindern den Zahlungseingang.</p></div></div>${shoots.length ? `<div class="shoot-payment-list">${shoots.map((x) => `<article class="payment-card"><div><strong>${esc(x.package_name || x.category)} · Shooting #${x.id}</strong><p>Vertrag: ${euro(x.contract_amount_eur)} · ${esc(x.shoot_date || "Termin offen")}</p><div id="payments-${x.id}" class="payment-items">Lade Zahlungen …</div></div><button data-payment="${x.id}" class="secondary-button">Zahlung erfassen</button></article>`).join("")}</div><dialog id="payment-dialog" class="service-dialog"><form id="payment-form"><div class="dialog-head"><h2>Zahlung erfassen</h2><button type="button" id="payment-close" class="text-button">Schließen</button></div><input type="hidden" name="shoot_id"><label>Betrag (€)<input name="amount_eur" type="number" min="0.01" step="0.01" required></label><label>Art<select name="kind"><option value="deposit">Anzahlung</option><option value="final">Restzahlung</option><option value="refund">Rückerstattung</option></select></label><label>Datum<input name="paid_on" type="date" required value="${new Date().toISOString().slice(0, 10)}"></label><label>Notiz<input name="note" maxlength="300"></label><button class="submit-button">Speichern</button></form></dialog>` : '<div class="empty-state">Nach der Bestätigung einer Anfrage erscheint hier das Shooting. Erst dann kann eine Zahlung erfasst werden.</div>'}`, "payments");
  for (const shoot of shoots) { const list = await api(`/admin/shoots/${shoot.id}/payments`); document.querySelector(`#payments-${shoot.id}`).textContent = list.length ? list.map((x) => `${x.paid_on} · ${x.kind} · ${euro(x.amount_eur)}`).join("  |  ") : "Noch keine Zahlungen"; }
  const dialog = document.querySelector("#payment-dialog"); if (!dialog) return; document.querySelectorAll("[data-payment]").forEach((button) => button.addEventListener("click", () => { document.querySelector("#payment-form").elements.shoot_id.value = button.dataset.payment; dialog.showModal(); })); document.querySelector("#payment-close").addEventListener("click", () => dialog.close()); document.querySelector("#payment-form").addEventListener("submit", async (event) => { event.preventDefault(); const data = Object.fromEntries(new FormData(event.currentTarget)); const id = data.shoot_id; delete data.shoot_id; data.amount_eur = Number(data.amount_eur); await api(`/admin/shoots/${id}/payments`, { method: "POST", body: JSON.stringify(data) }); await renderTab("payments"); });
}

async function renderMetrics(period = "day") {
  const data = await api(`/admin/metrics?period=${period}`);
  const dots = Array.from({ length: 240 }, (_, i) => { const x = i % 20; const y = Math.floor(i / 20); const n = data.heatmap.find((point) => point.x === x && point.y === y)?.count || 0; return `<i title="${n} Cursorpunkte" style="--heat:${n ? Math.min(.95, .16 + n / Math.max(1, ...data.heatmap.map((p) => p.count))) : 0}"></i>`; }).join("");
  shell(`<div class="metric-toolbar"><div class="period-tabs">${[["day", "Heute"], ["week", "Diese Woche"], ["month", "Dieser Monat"]].map(([id, label]) => `<button data-period="${id}" class="${period === id ? "selected" : ""}">${label}</button>`).join("")}</div></div><div class="metric-cards"><article><span>Besuche</span><strong>${data.sessions}</strong></article><article><span>Ø Verweildauer</span><strong>${Math.floor(data.average_seconds / 60)}:${String(data.average_seconds % 60).padStart(2, "0")} <small>Min.</small></strong></article><article><span>Erfasste Interaktionen</span><strong>${Object.values(data.events).reduce((a, b) => a + b, 0)}</strong></article><article><span>Cursorpunkte</span><strong>${data.heatmap.reduce((a, p) => a + p.count, 0)}</strong></article></div><div class="analytics-grid"><section class="data-panel"><h2>Cursor-Heatmap</h2><p>Nur nach aktiver Zustimmung; Koordinaten werden vor dem Speichern auf 20 × 12 Bereiche gerundet.</p><div class="heatmap-grid">${dots}</div><div class="heatmap-labels"><span>Links</span><span>Rechts</span></div></section><section class="data-panel"><h2>Ereignisse</h2>${Object.entries(data.events).map(([name, count]) => `<div class="event-line"><span>${esc(({ page_view: "Seitenaufrufe", cursor: "Cursor", heartbeat: "Aktivitätszeit", page_end: "Seitenende", form_start: "Formularstart", form_submit: "Anfrage gesendet", service_view: "Angebot angesehen" }[name] || name))}</span><strong>${count}</strong></div>`).join("") || '<p class="muted">Noch keine Daten. Besuchen Sie die Website und akzeptieren Sie die optionale Statistik.</p>'}</section></div><p class="privacy-note">Analytics consent is optional. No form fields, IP addresses, raw coordinates or marketing profiles are stored by this feature.</p>`, "metrics");
  document.querySelectorAll("[data-period]").forEach((button) => button.addEventListener("click", () => renderMetrics(button.dataset.period)));
}

async function renderSheets() {
  const data = await api("/admin/sheets-status");
  shell(`<section class="data-panel sheets-panel"><div class="panel-heading"><div><h2>PostgreSQL → Google Sheets</h2><p>PostgreSQL bleibt die führende Datenquelle; die private Tabelle ist ein synchronisiertes Arbeitsjournal und Reporting-Ansicht.</p></div><span class="state-pill ${data.enabled ? "on" : "off"}">${data.enabled ? "Verbunden" : "Nicht konfiguriert"}</span></div><div class="metric-cards compact"><article><span>Synchronisiert</span><strong>${data.synced_events}</strong></article><article><span>Warteschlange</span><strong>${data.pending}</strong></article><article><span>Fehler</span><strong>${data.errors}</strong></article></div><div class="button-row"><button id="bootstrap-sheets" class="secondary-button">Bestehende Daten zum Sync vormerken</button><button id="retry-sheets" class="secondary-button">Fehler erneut versuchen</button></div><p id="sheets-note" class="form-status"></p><p class="privacy-note">Nur das Backend erhält Zugriff auf die ausgewählte private Arbeitsmappe. Der Service-Account-Schlüssel gehört in den Server-Secrets-Ordner.</p></section>`, "sheets");
  for (const [id, path] of [["bootstrap-sheets", "/admin/sheets-sync/bootstrap"], ["retry-sheets", "/admin/sheets-sync/retry"]]) document.querySelector(`#${id}`).addEventListener("click", async () => { const note = document.querySelector("#sheets-note"); try { const result = await api(path, { method: "POST" }); note.textContent = `Vorgemerkt: ${result.queued} Datensätze.`; setTimeout(() => renderTab("sheets"), 800); } catch (e) { note.textContent = e.message; } });
}

async function start() {
  try { await api("/auth/me"); await renderTab(currentTab); }
  catch {
    try { const state = await api("/auth/registration-status"); authScreen(state.enabled); }
    catch { app.innerHTML = '<main class="auth-shell"><section class="auth-card"><h1>Verbindung nicht verfügbar</h1><p>Die Verwaltungsoberfläche konnte den Server nicht erreichen. Bitte später erneut versuchen.</p><a href="/">Zur Website</a></section></main>'; }
  }
}

start();
