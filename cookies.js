const CONSENT_KEY = "printz_cookie_consent";

function getConsent() {
  try {
    return localStorage.getItem(CONSENT_KEY);
  } catch {
    return null;
  }
}

function saveConsent(value) {
  try {
    localStorage.setItem(CONSENT_KEY, value);
  } catch {
    /* ignore */
  }
  document.cookie = `printz_consent=${encodeURIComponent(value)}; path=/; max-age=31536000; SameSite=Lax`;
}

function hideCookieBanner() {
  document.getElementById("cookie-banner")?.remove();
}

function showCookieBanner() {
  if (document.getElementById("cookie-banner")) return;

  const banner = document.createElement("div");
  banner.id = "cookie-banner";
  banner.className = "cookie-banner";
  banner.setAttribute("role", "dialog");
  banner.setAttribute("aria-labelledby", "cookie-title");
  banner.setAttribute("aria-live", "polite");
  banner.innerHTML = `
    <div class="cookie-inner">
      <div>
        <p class="cookie-kicker">Cookies</p>
        <h2 id="cookie-title">Diese Website verwendet Cookies</h2>
        <p>Wir nutzen technisch notwendige Cookies, damit die Seite zuverlässig funktioniert und Ihre Auswahl gespeichert werden kann. Es werden keine Werbe- oder Tracking-Cookies gesetzt.</p>
        <p><a href="datenschutz.html">Mehr in der Datenschutzerklärung</a></p>
      </div>
      <div class="cookie-actions">
        <button class="btn btn-primary" type="button" data-cookie="all">Alle akzeptieren</button>
        <button class="btn btn-dark" type="button" data-cookie="necessary">Nur notwendige</button>
      </div>
    </div>
  `;
  document.body.appendChild(banner);

  banner.addEventListener("click", (event) => {
    const button = event.target.closest("[data-cookie]");
    if (!button) return;
    saveConsent(button.getAttribute("data-cookie"));
    hideCookieBanner();
  });
}

document.addEventListener("click", (event) => {
  const opener = event.target.closest("[data-cookie-open]");
  if (!opener) return;
  event.preventDefault();
  showCookieBanner();
});

if (!getConsent()) {
  showCookieBanner();
}
