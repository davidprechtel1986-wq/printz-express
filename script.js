const year = document.getElementById("year");
if (year) year.textContent = String(new Date().getFullYear());

const toggle = document.querySelector(".nav-toggle");
const nav = document.getElementById("nav-menu");

if (toggle && nav) {
  toggle.addEventListener("click", () => {
    const open = nav.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(open));
    toggle.setAttribute("aria-label", open ? "Menü schließen" : "Menü öffnen");
  });

  nav.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      nav.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
    });
  });
}

function formToObject(form) {
  const data = Object.fromEntries(new FormData(form).entries());
  data.typ = form.dataset.typ || "transport";
  return data;
}

function bindForm(formId, statusId) {
  const form = document.getElementById(formId);
  const status = document.getElementById(statusId);
  if (!form || !status) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const missing = [...form.querySelectorAll("[required]")].some((field) => !String(field.value).trim());

    if (missing) {
      status.classList.add("error");
      status.textContent = "Bitte füllen Sie alle Pflichtfelder aus.";
      return;
    }

    const button = form.querySelector("button[type='submit']");
    if (button) button.disabled = true;
    status.classList.remove("error");
    status.textContent = "Anfrage wird gesendet…";

    try {
      const payload = formToObject(form);
      const response = await fetch("/api/anfrage", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const result = await response.json();

      if (!response.ok || !result.ok) {
        throw new Error(result.error || "Senden fehlgeschlagen.");
      }

      form.reset();
      status.classList.remove("error");
      status.textContent = "Vielen Dank. Ihre Anfrage ist bei uns eingegangen. Wir melden uns schnellstmöglich.";
    } catch (error) {
      const payload = formToObject(form);
      const body = Object.entries(payload)
        .filter(([, value]) => String(value).trim())
        .map(([key, value]) => `${key}: ${value}`)
        .join("\n");
      window.location.href = `mailto:?subject=${encodeURIComponent("Anfrage Printz Express")}&body=${encodeURIComponent(body)}`;
      form.reset();
      status.classList.remove("error");
      status.textContent = "Vielen Dank. Ihr E-Mail-Programm öffnet sich mit der Anfrage. Alternativ erreichen Sie uns unter +49 173 7712504.";
    } finally {
      if (button) button.disabled = false;
    }
  });
}

bindForm("transport-form", "transport-status");
bindForm("contact-form", "contact-status");
bindForm("job-form", "job-status");
