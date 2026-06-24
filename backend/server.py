import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from ai_service import detect_emotion, extract_order_no, format_handoff_reply, generate_reply, is_handoff_request
from config import CHATBOT_HOST, CHATBOT_PORT
from database import (
    create_demo_order,
    create_handoff_ticket,
    create_knowledge,
    delete_knowledge,
    ensure_session,
    get_demo_order,
    init_db,
    list_demo_orders,
    list_demo_products,
    list_handoff_tickets,
    list_knowledge,
    list_messages,
    list_sessions,
    recent_messages,
    save_message,
    update_knowledge,
)


class ApiHandler(BaseHTTPRequestHandler):
    server_version = "SalesCareAI/1.0"

    def log_message(self, fmt, *args):
        print("%s - - [%s] %s" % (self.client_address[0], self.log_date_time_string(), fmt % args))

    def _set_common_headers(self, status=200, content_type="application/json; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def send_json(self, payload, status=200):
        self._set_common_headers(status)
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw)

    def do_OPTIONS(self):
        self._set_common_headers(204)

    def do_GET(self):
        path, query = self.route()
        if path == "/api/health":
            self.send_json({"ok": True, "service": "salescare-ai", "version": "1.0"})
            return

        if path == "/api/knowledge":
            self.send_json({"items": list_knowledge()})
            return

        if path == "/api/sessions":
            limit = int(query.get("limit", ["20"])[0])
            self.send_json({"items": list_sessions(limit=min(limit, 100))})
            return

        if path == "/api/demo-orders":
            limit = int(query.get("limit", ["10"])[0])
            self.send_json({
                "items": list_demo_orders(limit=min(limit, 50)),
                "products": list_demo_products(),
            })
            return

        if path == "/api/handoff-tickets":
            limit = int(query.get("limit", ["20"])[0])
            self.send_json({"items": list_handoff_tickets(limit=min(limit, 100))})
            return

        if path.startswith("/api/sessions/") and path.endswith("/messages"):
            parts = path.strip("/").split("/")
            if len(parts) == 4:
                self.send_json({"items": list_messages(parts[2])})
                return

        self.send_json({"error": "not_found", "message": "API route not found"}, status=404)

    def do_POST(self):
        path, _query = self.route()
        try:
            payload = self.read_json()
        except json.JSONDecodeError:
            self.send_json({"error": "bad_json", "message": "Invalid JSON body"}, status=400)
            return

        if path == "/api/chat":
            message = str(payload.get("message", "")).strip()
            if not message:
                self.send_json({"error": "empty_message", "message": "message is required"}, status=400)
                return
            session_id = ensure_session(payload.get("session_id"))
            history = recent_messages(session_id)
            save_message(session_id, "user", message)
            if is_handoff_request(message):
                ticket = create_handoff_ticket(session_id=session_id, reason=message)
                answer = format_handoff_reply(ticket)
                metadata = {
                    "intent": "转人工",
                    "emotion": detect_emotion(message),
                    "sources": [],
                    "ticket": ticket,
                    "model_mode": "human-handoff",
                }
                result = {
                    "answer": answer,
                    "intent": "转人工",
                    "emotion": metadata["emotion"],
                    "sources": [],
                    "model_mode": "human-handoff",
                    "metadata": metadata,
                }
                save_message(
                    session_id,
                    "assistant",
                    answer,
                    intent=result["intent"],
                    metadata=metadata,
                )
                self.send_json({**result, "session_id": session_id})
                return
            order_no = extract_order_no(message)
            order = get_demo_order(order_no) if order_no else None
            result = generate_reply(message, list_knowledge(), history, order=order, order_no=order_no)
            save_message(
                session_id,
                "assistant",
                result["answer"],
                intent=result["intent"],
                metadata=result["metadata"],
            )
            self.send_json({**result, "session_id": session_id})
            return

        if path == "/api/knowledge":
            try:
                created = create_knowledge(payload)
            except ValueError as exc:
                self.send_json({"error": "validation_error", "message": str(exc)}, status=400)
                return
            self.send_json({"item": created}, status=201)
            return

        if path == "/api/demo-orders/create":
            created = create_demo_order(payload.get("product_name"))
            self.send_json({"item": created}, status=201)
            return

        if path == "/api/handoff-tickets/create":
            session_id = ensure_session(payload.get("session_id"))
            created = create_handoff_ticket(
                session_id=session_id,
                reason=payload.get("reason"),
                customer_name=payload.get("customer_name"),
                priority=payload.get("priority"),
            )
            self.send_json({"item": created, "session_id": session_id}, status=201)
            return

        self.send_json({"error": "not_found", "message": "API route not found"}, status=404)

    def do_PUT(self):
        path, _query = self.route()
        try:
            payload = self.read_json()
        except json.JSONDecodeError:
            self.send_json({"error": "bad_json", "message": "Invalid JSON body"}, status=400)
            return

        item_id = self.knowledge_id_from_path(path)
        if item_id is None:
            self.send_json({"error": "not_found", "message": "API route not found"}, status=404)
            return

        try:
            item = update_knowledge(item_id, payload)
        except ValueError as exc:
            self.send_json({"error": "validation_error", "message": str(exc)}, status=400)
            return
        if item is None:
            self.send_json({"error": "not_found", "message": "Knowledge item not found"}, status=404)
            return
        self.send_json({"item": item})

    def do_DELETE(self):
        path, _query = self.route()
        item_id = self.knowledge_id_from_path(path)
        if item_id is None:
            self.send_json({"error": "not_found", "message": "API route not found"}, status=404)
            return
        deleted = delete_knowledge(item_id)
        if not deleted:
            self.send_json({"error": "not_found", "message": "Knowledge item not found"}, status=404)
            return
        self.send_json({"ok": True})

    def route(self):
        parsed = urlparse(self.path)
        return parsed.path.rstrip("/") or "/", parse_qs(parsed.query)

    def knowledge_id_from_path(self, path):
        parts = path.strip("/").split("/")
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "knowledge":
            try:
                return int(parts[2])
            except ValueError:
                return None
        return None


def main():
    init_db()
    httpd = ThreadingHTTPServer((CHATBOT_HOST, CHATBOT_PORT), ApiHandler)
    print(f"SalesCare AI API running at http://{CHATBOT_HOST}:{CHATBOT_PORT}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
