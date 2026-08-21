"""Smoke test. Execute after `pip install -r requirements.txt`."""
import os
import tempfile

fd, path = tempfile.mkstemp(suffix=".db")
os.close(fd)
os.environ["DATABASE_URL"] = "sqlite:///" + path
os.environ["DEV_BYPASS_AUTH"] = "1"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["COOKIE_SECURE"] = "0"

from app import app  # noqa: E402

app.config.update(TESTING=True)
client = app.test_client()

r = client.get("/dev-login?email=teste1@lmtech.local&name=Teste+1", follow_redirects=True)
assert r.status_code == 200

boot = client.get("/api/bootstrap?month=2026-08")
assert boot.status_code == 200
initial = boot.get_json()
assert len(initial["leads"]) >= 70

lead = client.post("/api/leads", json={"name":"Lead Teste","phone":"11999999999","grade":"A","score":99}).get_json()
assert lead["name"] == "Lead Teste"

meeting = client.post("/api/meetings", json={
    "leadId": lead["id"], "startAt":"2026-08-25T14:00", "title":"Reunião Teste"
})
assert meeting.status_code == 201

contract = client.post("/api/contracts", json={
    "leadId": lead["id"], "clientName":"Lead Teste", "title":"Site", "value":"3500,00", "closedAt":"2026-08-25", "status":"Fechado"
})
assert contract.status_code == 201
assert contract.get_json()["valueCents"] == 350000

goal = client.post("/api/goals", json={
    "month":"2026-08", "scope":"team", "revenueTarget":"10000,00", "contractsTarget":4, "meetingsTarget":10
})
assert goal.status_code == 200

boot2 = client.get("/api/bootstrap?month=2026-08").get_json()
assert boot2["team"]["stats"]["revenueCents"] >= 350000
assert boot2["team"]["goal"]["revenueProgress"] >= 35
print("SMOKE TEST OK")
