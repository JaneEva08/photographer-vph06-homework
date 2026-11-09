import "./style.css";

const app = document.querySelector("#app");
const copy = {
  de: {
    home: "Zur Startseite", theme: "Farbschema wechseln", request: "Anfrage senden", location: "Fotografie · Deutschland",
    title: "Augenblicke, die", title_em: "bleiben.", intro: "Echte Geschichten verdienen Bilder mit Gefühl. Erzählen Sie mir von Ihrem Vorhaben — ich melde mich persönlich bei Ihnen.",
    cta: "Ihr Shooting anfragen", hero_note: "Geschichten · Veranstaltungen · Tanz & Performance", fields: "Arbeitsfelder", field_title: "Geschichten in vielen Facetten.",
    image_placeholder: "Bildplatzhalter", story: "Szenische Fotografie", story_desc: "Persönliche Geschichten mit Raum für Charakter und Ausdruck.",
    events: "Veranstaltungen", events_desc: "Atmosphäre, Begegnungen und die Momente dazwischen.", sport: "Sport", sport_desc: "Bewegung, Konzentration und echte Dynamik.",
    dance: "Tanz & Performance", dance_desc: "Körper, Bühne und erzählerische Inszenierungen.", love: "Love Stories", love_desc: "Unaufgeregte Bilder für gemeinsame Geschichten.",
    weddings: "Hochzeiten", weddings_desc: "Eine Reportage mit Blick auf Menschen und Details.", genre_note: "Die konkreten Angebote und Preisrahmen werden vom Studio verwaltet und sind unverbindliche Richtwerte.",
    first_step: "Der erste Schritt", request_title: "Erzählen Sie mir davon.", request_intro: "Unverbindlich und persönlich. Gemeinsam finden wir den passenden Rahmen.",
    service_label: "Wofür interessieren Sie sich?", service_placeholder: "Bitte wählen Sie ein Angebot", services_loading: "Angebote werden geladen …", services_empty: "Angebote folgen in Kürze",
    services_failed: "Angebote konnten nicht geladen werden", budget: "Ihr Budgetrahmen", choose_offer: "Bitte wählen Sie ein Angebot", budget_hint: "Der Richtwert hilft mir, ein passendes Angebot vorzubereiten.",
    name: "Ihr Name", full_name_placeholder: "Vor- und Nachname", email: "E-Mail-Adresse", email_placeholder: "name@beispiel.de", phone: "Telefon", optional: "optional",
    date: "Wunschtermin", region: "Ort / Region", region_placeholder: "z. B. Berlin und Umgebung", contact: "Bevorzugter Kontakt", inspiration: "Inspiration / Referenz",
    message: "Was möchten Sie festhalten?", message_placeholder: "Ein paar Worte zu Ihrer Idee, dem Anlass oder Ihren Wünschen …", consent: "Ich bin einverstanden, dass meine Angaben zur Beantwortung dieser Anfrage verwendet werden.",
    send: "Anfrage senden", sending: "Wird gesendet …", demo: "Demoformular für ein Lernprojekt. Bitte nur Testdaten verwenden.",
    sent: "Vielen Dank! Ihre Anfrage ist angekommen. Ich melde mich persönlich bei Ihnen.", send_failed: "Ihre Anfrage konnte nicht gesendet werden. Bitte prüfen Sie die Angaben und versuchen Sie es erneut.",
    connection_failed: "Die Verbindung ist gerade nicht möglich. Bitte laden Sie die Seite später erneut.", services_preparing: "Die Angebotsliste wird gerade vorbereitet. Bitte versuchen Sie es später erneut.",
    analytics: "Freiwillige Statistik", analytics_title: "Hilft mir, die Website zu verbessern.", analytics_text: "Nur mit Ihrer Zustimmung erfasse ich grobe Interaktionen und gerundete Cursorbereiche. Formularinhalte werden dabei nicht erfasst.",
    agree: "Einverstanden", decline: "Ablehnen", footer: "Fotografie · Lernprojekt", footer_note: "Mit Ruhe gesehen. Mit Gefühl erzählt.", email_option: "E-Mail", phone_option: "Telefon"
  },
  en: {
    home: "Home", theme: "Change color theme", request: "Send an enquiry", location: "Photography · Germany",
    title: "Moments that", title_em: "stay.", intro: "Real stories deserve photographs with feeling. Tell me about your idea — I will get back to you personally.",
    cta: "Plan your session", hero_note: "Stories · Events · Dance & performance", fields: "What I photograph", field_title: "Stories in many forms.",
    image_placeholder: "Image placeholder", story: "Story-led portraits", story_desc: "Personal stories with room for character and expression.",
    events: "Events", events_desc: "Atmosphere, encounters and the moments in between.", sport: "Sport", sport_desc: "Movement, focus and genuine energy.",
    dance: "Dance & performance", dance_desc: "Movement, stage and visual storytelling.", love: "Love stories", love_desc: "Natural photographs for a story you share.",
    weddings: "Weddings", weddings_desc: "A thoughtful story of people and details.", genre_note: "Current offers and price ranges are managed by the studio and are non-binding guide prices.",
    first_step: "A first step", request_title: "Tell me what you have in mind.", request_intro: "No obligation, just a personal conversation about the right approach.",
    service_label: "What are you interested in?", service_placeholder: "Choose an offer", services_loading: "Loading offers …", services_empty: "Offers coming soon",
    services_failed: "Offers could not be loaded", budget: "Your budget range", choose_offer: "Choose an offer first", budget_hint: "This guide helps me prepare a suitable proposal.",
    name: "Your name", full_name_placeholder: "First and last name", email: "Email address", email_placeholder: "name@example.com", phone: "Phone", optional: "optional",
    date: "Preferred date", region: "Location / region", region_placeholder: "e.g. Berlin and nearby", contact: "Preferred contact method", inspiration: "Inspiration / reference",
    message: "What would you like to capture?", message_placeholder: "A few words about your idea, occasion or wishes …", consent: "I agree that my details may be used to respond to this enquiry.",
    send: "Send enquiry", sending: "Sending …", demo: "Demo form for a learning project. Please use test data only.",
    sent: "Thank you! Your enquiry has arrived. I will get back to you personally.", send_failed: "Your enquiry could not be sent. Please check the details and try again.",
    connection_failed: "The connection is unavailable right now. Please try again later.", services_preparing: "The offer list is being prepared. Please try again later.",
    analytics: "Optional analytics", analytics_title: "Help improve this website.", analytics_text: "With your permission, I collect coarse interactions and rounded cursor areas only. Form contents are never included.",
    agree: "Allow analytics", decline: "Decline", footer: "Photography · learning project", footer_note: "Seen with care. Told with feeling.", email_option: "Email", phone_option: "Phone"
  },
  ru: {
    home: "На главную", theme: "Сменить тему оформления", request: "Оставить заявку", location: "Фотография · Германия",
    title: "Моменты, которые", title_em: "остаются.", intro: "Настоящие истории заслуживают фотографий с чувством. Расскажите о своей идее — я лично свяжусь с вами.",
    cta: "Обсудить съёмку", hero_note: "Истории · события · танец и перформанс", fields: "Направления", field_title: "Истории в разных жанрах.",
    image_placeholder: "Заглушка для фото", story: "Сюжетная съёмка", story_desc: "Личные истории, характер и выразительные образы.",
    events: "Мероприятия", events_desc: "Атмосфера, встречи и моменты между событиями.", sport: "Спорт", sport_desc: "Движение, концентрация и энергия.",
    dance: "Танец и перформанс", dance_desc: "Движение, сцена и визуальный рассказ.", love: "Love story", love_desc: "Естественные кадры вашей общей истории.",
    weddings: "Свадьбы", weddings_desc: "Репортаж о людях, эмоциях и деталях.", genre_note: "Актуальные услуги и диапазоны цен задаются в админке и пока являются предварительными ориентирами.",
    first_step: "Первый шаг", request_title: "Расскажите о вашей идее.", request_intro: "Без обязательств — обсудим подходящий формат и детали.",
    service_label: "Какая съёмка вас интересует?", service_placeholder: "Выберите предложение", services_loading: "Загрузка предложений …", services_empty: "Предложения скоро появятся",
    services_failed: "Не удалось загрузить список услуг", budget: "Ваш бюджет", choose_offer: "Сначала выберите предложение", budget_hint: "Это поможет подготовить подходящий вариант.",
    name: "Ваше имя", full_name_placeholder: "Имя и фамилия", email: "Электронная почта", email_placeholder: "name@example.com", phone: "Телефон", optional: "необязательно",
    date: "Желаемая дата", region: "Город / регион", region_placeholder: "например, Берлин и окрестности", contact: "Предпочтительный способ связи", inspiration: "Референс / вдохновение",
    message: "Что вы хотите запечатлеть?", message_placeholder: "Расскажите об идее, событии или пожеланиях …", consent: "Я согласен(на), что мои данные будут использованы для ответа на эту заявку.",
    send: "Отправить заявку", sending: "Отправляем …", demo: "Демонстрационная форма учебного проекта. Используйте только тестовые данные.",
    sent: "Спасибо! Заявка получена. Я свяжусь с вами лично.", send_failed: "Не удалось отправить заявку. Проверьте данные и попробуйте снова.",
    connection_failed: "Сейчас нет соединения с сервером. Попробуйте позже.", services_preparing: "Список услуг готовится. Попробуйте позже.",
    analytics: "Добровольная статистика", analytics_title: "Помогите улучшить сайт.", analytics_text: "Только с вашего согласия я собираю обобщённые действия и округлённые области курсора. Содержимое формы не записывается.",
    agree: "Разрешить сбор", decline: "Отказаться", footer: "Фотография · учебный проект", footer_note: "Увидеть спокойно. Рассказать с чувством.", email_option: "Электронная почта", phone_option: "Телефон"
  }
};
const supportedLanguages = Object.keys(copy);
const savedLanguage = localStorage.getItem("photography-language");
const browserLanguage = navigator.language.toLowerCase().split("-")[0];
const routeLanguage = location.pathname.match(/^\/(de|en|ru)(?:\/|$)/)?.[1];
let locale = routeLanguage || (supportedLanguages.includes(savedLanguage) ? savedLanguage : supportedLanguages.includes(browserLanguage) ? browserLanguage : "de");
const t = (key) => copy[locale][key] || copy.de[key] || key;

app.innerHTML = `
  <div class="ambient" aria-hidden="true">
    <span class="orb orb-one"></span><span class="orb orb-two"></span><span class="orb orb-three"></span>
  </div>
  <header class="site-header">
    <a class="brand" href="#top" aria-label="${t("home")}">Fotografie</a>
    <div class="header-actions"><select id="language-toggle" class="language-toggle" aria-label="Language"><option value="de">DE</option><option value="en">EN</option><option value="ru">RU</option></select><button id="theme-toggle" class="theme-toggle" type="button" aria-label="${t("theme")}" title="${t("theme")}"><span aria-hidden="true">☾</span></button><a class="header-link" href="#anfrage">${t("request")} <span aria-hidden="true">↗</span></a></div>
  </header>
  <main id="top" class="page-shell">
    <section class="hero" aria-labelledby="page-title">
      <p class="eyebrow"><span class="eyebrow-dot"></span> ${t("location")}</p>
      <h1 id="page-title">${t("title")} <em>${t("title_em")}</em></h1>
      <p class="intro">${t("intro")}</p>
      <a class="primary-link" href="#anfrage">${t("cta")} <span aria-hidden="true">↓</span></a>
      <p class="hero-note">${t("hero_note")}</p>
    </section>

    <section class="genre-section" aria-labelledby="genre-title">
      <p class="eyebrow">${t("fields")}</p>
      <h2 id="genre-title">${t("field_title")}</h2>
      <div class="genre-grid">
        <article><div class="genre-art art-story"><span>${t("image_placeholder")}</span></div><span>01</span><h3>${t("story")}</h3><p>${t("story_desc")}</p></article>
        <article><div class="genre-art art-event"><span>${t("image_placeholder")}</span></div><span>02</span><h3>${t("events")}</h3><p>${t("events_desc")}</p></article>
        <article><div class="genre-art art-sport"><span>${t("image_placeholder")}</span></div><span>03</span><h3>${t("sport")}</h3><p>${t("sport_desc")}</p></article>
        <article><div class="genre-art art-dance"><span>${t("image_placeholder")}</span></div><span>04</span><h3>${t("dance")}</h3><p>${t("dance_desc")}</p></article>
        <article><div class="genre-art art-love"><span>${t("image_placeholder")}</span></div><span>05</span><h3>${t("love")}</h3><p>${t("love_desc")}</p></article>
        <article><div class="genre-art art-wedding"><span>${t("image_placeholder")}</span></div><span>06</span><h3>${t("weddings")}</h3><p>${t("weddings_desc")}</p></article>
      </div>
      <p class="genre-note">${t("genre_note")}</p>
    </section>

    <section id="anfrage" class="request-section" aria-labelledby="request-title">
      <div class="section-heading">
        <p class="eyebrow">${t("first_step")}</p>
        <h2 id="request-title">${t("request_title")}</h2>
        <p>${t("request_intro")}</p>
      </div>

      <form id="request-form" class="request-card">
        <div class="field field-wide">
          <label for="service">${t("service_label")}</label>
          <select id="service" name="service_id" required>
            <option value="">${t("services_loading")}</option>
          </select>
          <small id="service-description" class="field-hint" aria-live="polite"></small>
        </div>

        <div class="field field-wide budget-field">
          <div class="range-heading"><label for="budget">${t("budget")}</label><output id="budget-output" for="budget">—</output></div>
          <input id="budget" name="budget_eur" type="range" min="0" max="1000" step="10" value="0" disabled />
          <div class="range-ends"><span id="budget-min">${t("choose_offer")}</span><span id="budget-max"></span></div>
          <small class="field-hint">${t("budget_hint")}</small>
        </div>

        <div class="field">
          <label for="full-name">${t("name")}</label>
          <input id="full-name" name="full_name" autocomplete="name" required minlength="2" maxlength="160" placeholder="${t("full_name_placeholder")}" />
        </div>
        <div class="field">
          <label for="email">${t("email")}</label>
          <input id="email" name="email" type="email" autocomplete="email" required maxlength="254" placeholder="${t("email_placeholder")}" />
        </div>
        <div class="field">
          <label for="phone">${t("phone")} <span class="optional">${t("optional")}</span></label>
          <input id="phone" name="phone" type="tel" autocomplete="tel" maxlength="48" placeholder="+49 …" />
        </div>
        <div class="field">
          <label for="preferred-date">${t("date")} <span class="optional">${t("optional")}</span></label>
          <input id="preferred-date" name="preferred_date" type="date" />
        </div>
        <div class="field">
          <label for="location">${t("region")} <span class="optional">${t("optional")}</span></label>
          <input id="location" name="location" maxlength="180" placeholder="${t("region_placeholder")}" />
        </div>
        <div class="field">
          <label for="preferred-contact">${t("contact")}</label>
          <select id="preferred-contact" name="preferred_contact"><option value="email">${t("email_option")}</option><option value="phone">${t("phone_option")}</option></select>
        </div>
        <div class="field field-wide">
          <label for="reference-url">${t("inspiration")} <span class="optional">${t("optional")}</span></label>
          <input id="reference-url" name="reference_url" type="url" maxlength="500" placeholder="https:// …" />
        </div>
        <div class="field field-wide">
          <label for="message">${t("message")}</label>
          <textarea id="message" name="message" rows="4" maxlength="4000" placeholder="${t("message_placeholder")}"></textarea>
        </div>
        <div class="field field-wide consent-field">
          <label class="checkbox-label"><input name="contact_consent" type="checkbox" required /><span>${t("consent")}</span></label>
        </div>
        <div class="field field-wide submit-row">
          <button id="submit-button" class="submit-button" type="submit" disabled>${t("send")} <span aria-hidden="true">↗</span></button>
          <p id="form-status" class="form-status" role="status" aria-live="polite"></p>
        </div>
      </form>
      <p class="demo-note">${t("demo")}</p>
    </section>
    <section class="analytics-consent" aria-labelledby="analytics-title">
      <div><p class="eyebrow">${t("analytics")}</p><h2 id="analytics-title">${t("analytics_title")}</h2><p>${t("analytics_text")}</p></div>
      <div class="consent-actions"><button id="analytics-accept" class="secondary-button">${t("agree")}</button><button id="analytics-decline" class="text-button">${t("decline")}</button></div>
    </section>
  </main>
  <footer class="site-footer"><span>${t("footer")}</span><span>${t("footer_note")}</span></footer>
`;

document.documentElement.lang = locale;
document.title = locale === "de" ? "Fotografie — Anfrage" : locale === "en" ? "Photography — enquiry" : "Фотография — заявка";
document.querySelector("#language-toggle").value = locale;
document.querySelector("#language-toggle").addEventListener("change", (event) => { const nextLocale = event.target.value; localStorage.setItem("photography-language", nextLocale); location.assign(`/${nextLocale}`); });

const form = document.querySelector("#request-form");
const serviceSelect = document.querySelector("#service");
const budgetInput = document.querySelector("#budget");
const budgetOutput = document.querySelector("#budget-output");
const status = document.querySelector("#form-status");
const submitButton = document.querySelector("#submit-button");
let services = [];

const euro = (amount) => new Intl.NumberFormat(locale === "en" ? "en-IE" : "de-DE", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 0,
}).format(amount);

function showStatus(message, kind = "") {
  status.textContent = message;
  status.className = `form-status ${kind}`.trim();
}

function updateBudget() {
  budgetOutput.value = euro(Number(budgetInput.value));
}

function selectService() {
  const service = services.find((item) => item.id === Number(serviceSelect.value));
  const description = document.querySelector("#service-description");
  if (!service) {
    budgetInput.disabled = true;
    submitButton.disabled = true;
    budgetOutput.value = "—";
    description.textContent = "";
    document.querySelector("#budget-min").textContent = t("choose_offer");
    document.querySelector("#budget-max").textContent = "";
    return;
  }
  budgetInput.min = String(service.min_price_eur);
  budgetInput.max = String(service.max_price_eur);
  budgetInput.value = String(service.min_price_eur);
  budgetInput.disabled = false;
  submitButton.disabled = false;
  document.querySelector("#budget-min").textContent = euro(service.min_price_eur);
  document.querySelector("#budget-max").textContent = euro(service.max_price_eur);
  description.textContent = service[`description_${locale}`] || service.description;
  updateBudget();
}

async function loadServices() {
  try {
    const response = await fetch("/api/services", { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    services = await response.json();
    serviceSelect.replaceChildren(new Option(t("service_placeholder"), ""));
    for (const service of services) {
      const serviceName = service[`name_${locale}`] || service.name;
      serviceSelect.add(new Option(`${serviceName} · ${euro(service.min_price_eur)}–${euro(service.max_price_eur)}`, service.id));
    }
    if (services.length === 0) {
      serviceSelect.replaceChildren(new Option(t("services_empty"), ""));
      showStatus(t("services_preparing"), "error");
    }
    selectService();
  } catch (error) {
    serviceSelect.replaceChildren(new Option(t("services_failed"), ""));
    selectService();
    showStatus(t("connection_failed"), "error");
    console.error("Service list could not be loaded", error);
  }
}

budgetInput.addEventListener("input", updateBudget);
serviceSelect.addEventListener("change", selectService);

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!form.reportValidity()) return;
  const values = new FormData(form);
  const payload = {
    service_id: Number(values.get("service_id")),
    full_name: String(values.get("full_name")).trim(),
    email: String(values.get("email")).trim(),
    phone: String(values.get("phone")).trim() || null,
    budget_eur: Number(values.get("budget_eur")),
    preferred_date: String(values.get("preferred_date")) || null,
    location: String(values.get("location")).trim() || null,
    preferred_contact: String(values.get("preferred_contact")) || "email",
    reference_url: String(values.get("reference_url")).trim() || null,
    message: String(values.get("message")).trim(),
    contact_consent: values.get("contact_consent") === "on",
    language: locale,
  };

  submitButton.disabled = true;
  submitButton.textContent = t("sending");
  showStatus("");
  try {
    const response = await fetch("/api/applications", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(result.detail || `HTTP ${response.status}`);
    sendMetric("form_submit");
    showStatus(t("sent"), "success");
    form.reset();
    selectService();
  } catch (error) {
    showStatus(t("send_failed"), "error");
    console.error("Application could not be submitted", error);
  } finally {
    submitButton.innerHTML = `${t("send")} <span aria-hidden="true">↗</span>`;
    submitButton.disabled = services.length === 0;
  }
});

loadServices();

const themeToggle = document.querySelector("#theme-toggle");
const themePreference = localStorage.getItem("photography-theme");
const activeTheme = themePreference || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
document.documentElement.dataset.theme = activeTheme;
themeToggle.innerHTML = activeTheme === "dark" ? '<span aria-hidden="true">☀</span>' : '<span aria-hidden="true">☾</span>';
themeToggle.addEventListener("click", (event) => {
  const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.style.setProperty("--theme-x", `${event.clientX || innerWidth - 36}px`);
  document.documentElement.style.setProperty("--theme-y", `${event.clientY || 36}px`);
  const apply = () => {
    document.documentElement.dataset.theme = nextTheme;
    localStorage.setItem("photography-theme", nextTheme);
    themeToggle.innerHTML = nextTheme === "dark" ? '<span aria-hidden="true">☀</span>' : '<span aria-hidden="true">☾</span>';
  };
  if (document.startViewTransition && !matchMedia("(prefers-reduced-motion: reduce)").matches) document.startViewTransition(apply);
  else apply();
});

const analyticsChoice = localStorage.getItem("photography-analytics-consent");
const newAnalyticsId = () => typeof crypto.randomUUID === "function" ? crypto.randomUUID() : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}-${Math.random().toString(36).slice(2)}`;
const analyticsSession = sessionStorage.getItem("photography-analytics-session") || newAnalyticsId();
sessionStorage.setItem("photography-analytics-session", analyticsSession);
let lastCursorAt = 0;
let lastPageEndAt = Date.now();
const sendMetric = (eventName, coordinates = null) => {
  if (localStorage.getItem("photography-analytics-consent") !== "yes") return;
  const payload = { session_id: analyticsSession, event_key: newAnalyticsId(), event_name: eventName, page_path: location.pathname, analytics_consent: true };
  if (coordinates) { payload.x_bucket = coordinates.x; payload.y_bucket = coordinates.y; }
  fetch("/api/metrics", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload), keepalive: true }).catch(() => {});
};
if (analyticsChoice === "yes") sendMetric("page_view");
document.querySelector("#analytics-accept").addEventListener("click", () => { localStorage.setItem("photography-analytics-consent", "yes"); document.querySelector(".analytics-consent").classList.add("accepted"); sendMetric("page_view"); });
document.querySelector("#analytics-decline").addEventListener("click", () => {
  const hadConsented = localStorage.getItem("photography-analytics-consent") === "yes";
  localStorage.setItem("photography-analytics-consent", "no");
  document.querySelector(".analytics-consent").classList.add("declined");
  if (hadConsented) fetch("/api/metrics/withdraw", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ session_id: analyticsSession }) }).catch(() => {});
});
document.addEventListener("pointermove", (event) => {
  const now = Date.now();
  if (now - lastCursorAt < 1200) return;
  lastCursorAt = now;
  sendMetric("cursor", { x: Math.min(19, Math.floor(event.clientX / innerWidth * 20)), y: Math.min(11, Math.floor(event.clientY / innerHeight * 12)) });
}, { passive: true });
setInterval(() => sendMetric("heartbeat"), 30_000);
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible") {
    const elapsed = Math.floor((Date.now() - lastPageEndAt) / 1000);
    if (elapsed > 0 && elapsed < 3600) sendMetric("heartbeat");
    lastPageEndAt = Date.now();
  } else sendMetric("page_end");
});
form.addEventListener("focusin", () => sendMetric("form_start"), { once: true });
serviceSelect.addEventListener("change", () => sendMetric("service_view"));
