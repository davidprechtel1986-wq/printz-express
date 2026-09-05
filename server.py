from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "anfragen.json"
ADMIN_PIN = "printz"
MAX_LEN = 2000
ALLOWED_TYPES = {"transport", "kontakt", "bewerbung"}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def load_inquiries() -> list:
    if not DATA_FILE.exists():
        return []
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def save_inquiries(items: list) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def clean(value: object, limit: int = 240) -> str:
    text = " ".join(str(value or "").split())
    return text[:limit]


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Admin-Pin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/anfragen":
            pin = self.headers.get("X-Admin-Pin", "")
            query_pin = parse_qs(parsed.query).get("pin", [""])[0]
            if pin != ADMIN_PIN and query_pin != ADMIN_PIN:
                return self.json_response({"ok": False, "error": "Kein Zugriff."}, 401)
            return self.json_response({"ok": True, "items": list(reversed(load_inquiries()))})
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/anfrage":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", "0") or 0)
        if length > 40_000:
            return self.json_response({"ok": False, "error": "Anfrage ist zu groß."}, 400)

        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self.json_response({"ok": False, "error": "Ungültige Anfrage."}, 400)

        if not isinstance(payload, dict):
            return self.json_response({"ok": False, "error": "Ungültige Anfrage."}, 400)

        typ = clean(payload.get("typ"), 40).lower() or "transport"
        if typ not in ALLOWED_TYPES:
            typ = "transport"

        name = clean(payload.get("name"))
        email = clean(payload.get("email"))
        if not name or not EMAIL_RE.match(email):
            return self.json_response({"ok": False, "error": "Bitte Name und gültige E-Mail angeben."}, 400)

        item = {
            "id": datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f"),
            "created": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "typ": typ,
            "name": name,
            "firma": clean(payload.get("firma")),
            "email": email,
            "telefon": clean(payload.get("telefon")),
            "leistung": clean(payload.get("leistung")),
            "abholort": clean(payload.get("abholort")),
            "lieferort": clean(payload.get("lieferort")),
            "ware": clean(payload.get("ware")),
            "menge": clean(payload.get("menge")),
            "termin": clean(payload.get("termin")),
            "position": clean(payload.get("position")),
            "nachricht": clean(payload.get("nachricht") or payload.get("details"), MAX_LEN),
        }

        if typ == "transport" and (not item["abholort"] or not item["lieferort"] or not item["ware"]):
            return self.json_response({"ok": False, "error": "Bitte Abholort, Lieferort und Art der Ware angeben."}, 400)
        if typ == "kontakt" and not item["nachricht"]:
            return self.json_response({"ok": False, "error": "Bitte eine Nachricht eingeben."}, 400)
        if typ == "bewerbung" and (not item["position"] or not item["nachricht"]):
            return self.json_response({"ok": False, "error": "Bitte Position und Kurzvorstellung angeben."}, 400)

        items = load_inquiries()
        items.append(item)
        save_inquiries(items)
        return self.json_response({"ok": True})

    def json_response(self, payload: dict, status: int = 200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        save_inquiries([])
    server = ThreadingHTTPServer(("127.0.0.1", 4173), Handler)
    print("Printz Express läuft unter http://127.0.0.1:4173/")
    print("Anfragen einsehen: http://127.0.0.1:4173/anfragen.html")
    server.serve_forever()
