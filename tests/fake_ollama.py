# tests/fake_ollama.py
# Stub of Ollama's /api/generate that returns canned JSON for each agent prompt.
# Used by the test suite; can also be run on its own to try the app without Ollama:
#   python tests/fake_ollama.py
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

RESPONSES = [
    ("Classify this customer query", {"category": "access", "urgency": "high",
                                      "summary": "User cannot log in to their account", "entities": ["account"]}),
    ("ADK semantic enrichment", {"root_cause_guess": "expired password", "related_issues": ["Account Locked"],
                                 "missing_info": ["error message"], "recommendations": ["reset password"]}),
    ("senior support analyst", {"steps": ["Reset the password", "Clear browser cache", "Try signing in again"]}),
    ("Conceptually execute", {"success": True, "notes": "Login restored",
                              "executed_steps": ["Reset the password", "Clear browser cache", "Try signing in again"]}),
    ("escalation manager", {"escalate": False, "reason": "Resolved by self-service steps"}),
    ("validation assistant", {"hallucination": False, "uncertain_claims": [], "summary": "ok"}),
]

# requests seen by the stub, for assertions
REQUESTS = []


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        REQUESTS.append(body)
        prompt = body.get("prompt", "")
        out = next((r for k, r in RESPONSES if k in prompt), {"note": "unmatched"})
        data = json.dumps({"response": json.dumps(out)}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


def start(port: int = 0) -> ThreadingHTTPServer:
    """Start the stub in a background thread; port 0 picks a free port."""
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


if __name__ == "__main__":
    print("Fake Ollama listening on http://127.0.0.1:11434")
    ThreadingHTTPServer(("127.0.0.1", 11434), Handler).serve_forever()
