from fastapi.testclient import TestClient
from bot import app, contexts, conversations

client = TestClient(app)

def test_healthz():
    resp = client.get("/v1/healthz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "uptime_seconds" in data
    assert "contexts_loaded" in data
    assert "category" in data["contexts_loaded"]
    assert "merchant" in data["contexts_loaded"]

def test_metadata():
    resp = client.get("/v1/metadata")
    assert resp.status_code == 200
    data = resp.json()
    assert "team_name" in data
    assert "model" in data
    assert "version" in data
    assert "contact_email" in data

def test_context_push_and_idempotency():
    payload = {
        "slug": "test_vertical",
        "voice": {"tone": "clinical"},
        "offer_catalog": []
    }
    
    # 1. First push version 2
    resp = client.post("/v1/context", json={
        "scope": "category",
        "context_id": "test_vertical_idem",
        "version": 2,
        "payload": payload
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["accepted"] is True

    # 2. Re-posting same version 2 -> Idempotent 200 OK
    resp2 = client.post("/v1/context", json={
        "scope": "category",
        "context_id": "test_vertical_idem",
        "version": 2,
        "payload": payload
    })
    assert resp2.status_code == 200
    assert resp2.json()["accepted"] is True

    # 3. Posting older version 1 -> Expect 409 Conflict
    resp3 = client.post("/v1/context", json={
        "scope": "category",
        "context_id": "test_vertical_idem",
        "version": 1,
        "payload": payload
    })
    assert resp3.status_code == 409
    data3 = resp3.json()["detail"]
    assert data3["accepted"] is False
    assert data3["reason"] == "stale_version"

def test_tick_generation():
    # Push test merchant & trigger
    m_id = "m_test_001"
    t_id = "trg_test_001"
    client.post("/v1/context", json={
        "scope": "merchant",
        "context_id": m_id,
        "version": 10,
        "payload": {
            "merchant_id": m_id,
            "category_slug": "dentists",
            "identity": {"name": "Dr. Smile Clinic", "owner_first_name": "Smile", "locality": "Saket", "languages": ["en"]},
            "performance": {"views": 1500, "calls": 30, "ctr": 0.025},
            "offers": [{"id": "off1", "title": "Dental Cleaning @ ₹299", "status": "active"}]
        }
    })

    client.post("/v1/context", json={
        "scope": "trigger",
        "context_id": t_id,
        "version": 10,
        "payload": {
            "id": t_id,
            "scope": "merchant",
            "kind": "research_digest",
            "merchant_id": m_id,
            "payload": {
                "category": "dentists",
                "top_item": {"title": "Fluoride study", "source": "JIDA Oct 2026, p.14", "trial_n": 2100}
            },
            "urgency": 2,
            "suppression_key": "test_suppress_001"
        }
    })

    resp = client.post("/v1/tick", json={
        "now": "2026-04-26T10:00:00Z",
        "available_triggers": [t_id]
    })
    assert resp.status_code == 200
    actions = resp.json()["actions"]
    assert len(actions) == 1
    act = actions[0]
    assert act["merchant_id"] == m_id
    assert act["trigger_id"] == t_id
    assert act["send_as"] == "vera"
    assert "2100" in act["body"]
    assert "JIDA" in act["body"]
    assert act["cta"] in ["open_ended", "binary_yes_no"]

def test_reply_auto_reply_detection():
    resp = client.post("/v1/reply", json={
        "conversation_id": "conv_test_auto",
        "merchant_id": "m_test_001",
        "customer_id": None,
        "from_role": "merchant",
        "message": "Thank you for contacting Dr. Smile Clinic! Our team will respond shortly.",
        "received_at": "2026-04-26T10:05:00Z",
        "turn_number": 2
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "end"
    assert "auto" in data["rationale"].lower() or "canned" in data["rationale"].lower()

def test_reply_intent_transition_action_mode():
    commitment_msg = "Ok lets do it. Whats next?"
    resp = client.post("/v1/reply", json={
        "conversation_id": "conv_test_intent",
        "merchant_id": "m_test_001",
        "customer_id": None,
        "from_role": "merchant",
        "message": commitment_msg,
        "received_at": "2026-04-26T10:10:00Z",
        "turn_number": 2
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "send"
    body_lower = data["body"].lower()

    # Must contain actioning words
    actioning = ["done", "sending", "draft", "here", "confirm", "proceed", "next"]
    assert any(w in body_lower for w in actioning), f"Expected action words in {body_lower}"

    # Must NOT contain qualifying words
    qualifying = ["would you", "do you", "can you tell", "what if", "how about"]
    assert not any(w in body_lower for w in qualifying), f"Qualifying words found in {body_lower}"

def test_reply_hostile_optout():
    hostile_msg = "Stop messaging me. This is useless spam."
    resp = client.post("/v1/reply", json={
        "conversation_id": "conv_test_hostile",
        "merchant_id": "m_test_001",
        "customer_id": None,
        "from_role": "merchant",
        "message": hostile_msg,
        "received_at": "2026-04-26T10:15:00Z",
        "turn_number": 2
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "end"

def test_reply_curveball_redirect():
    curveball_msg = "Can you also help me with my GST filing this month?"
    resp = client.post("/v1/reply", json={
        "conversation_id": "conv_test_curveball",
        "merchant_id": "m_test_001",
        "customer_id": None,
        "from_role": "merchant",
        "message": curveball_msg,
        "received_at": "2026-04-26T10:20:00Z",
        "turn_number": 2
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "send"
    assert "gst" in data["body"].lower() or "accountant" in data["body"].lower()

def test_compose_api():
    from bot import compose
    cat = {"slug": "dentists"}
    merch = {"identity": {"name": "Dr. Smile", "owner_first_name": "Smile", "locality": "Saket"}}
    trg = {"kind": "research_digest", "id": "t1", "payload": {}}
    res = compose(cat, merch, trg)
    assert "body" in res
    assert "cta" in res
    assert "send_as" in res
    assert res["send_as"] == "vera"
    assert "rationale" in res

def test_respond_handler():
    from conversation_handlers import respond
    state = {"conversation_id": "c1", "merchant_id": "m1"}
    res = respond(state, "Stop messaging me")
    assert res["action"] == "end"

    res_action = respond(state, "Ok lets do it. Whats next?")
    assert res_action["action"] == "send"
    assert "done" in res_action["body"].lower() or "draft" in res_action["body"].lower()

if __name__ == "__main__":
    tests = [
        test_healthz,
        test_metadata,
        test_context_push_and_idempotency,
        test_tick_generation,
        test_reply_auto_reply_detection,
        test_reply_intent_transition_action_mode,
        test_reply_hostile_optout,
        test_reply_curveball_redirect,
        test_compose_api,
        test_respond_handler
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"[PASS] {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"[FAIL] {t.__name__}: {e}")
            raise e
    print(f"\nAll {passed}/{len(tests)} tests passed successfully!")

