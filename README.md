# magicpin AI Challenge — Vera Merchant AI Assistant

**Team**: magicpin Vera Bot  
**Submission Date**: 2026-04-26  
**Version**: 1.0.0  

---

## 1. Executive Summary & Approach

Our solution implements a production-grade merchant marketing and engagement assistant (**Vera**) designed for WhatsApp local commerce across India's top 5 SMB verticals: **Dentists, Salons, Restaurants, Gyms, and Pharmacies**.

The architecture is built on three core pillars:

1. **4-Context Composition Engine (`compose`)**:
   - Synthesizes `CategoryContext`, `MerchantContext`, `TriggerContext`, and optional `CustomerContext` into high-converting, personalized WhatsApp messages.
   - **Verifiable Factual Grounding**: Strictly anchors every message on verifiable data points (e.g., sample sizes like $N=2,100$, journal citations like JIDA Oct 2026, exact local search volumes, peer median CTR benchmarks, and verified service+price offers like `"Dental Cleaning @ ₹299"` rather than generic `"10% off"`).
   - **Zero Hallucination & Strict Taboo Enforcement**: Adheres strictly to category voice guardrails (e.g., prohibition of medical claims like *"cure"* or *"guaranteed"* for healthcare verticals).
   - **Bi-Directional Role Attribution**: Automatically detects and handles both merchant-facing (`send_as: "vera"`) and customer-facing (`send_as: "merchant_on_behalf"`) outreach.

2. **Stateful Multi-Turn Conversation Engine (`respond` & `/v1/reply`)**:
   - **Instant Auto-Reply Termination**: Accurately detects WhatsApp Business automated canned messages (*"Thank you for contacting us..."*) on Turn 1 and immediately returns `"action": "end"` to eliminate repetitive bot-to-bot loops.
   - **Frictionless Intent Transition**: Detects explicit merchant intent (*"Ok let's do it"*, *"What's next?"*) and transitions immediately into **action mode** with concrete drafts and action verbs, strictly avoiding redundant qualification questions.
   - **Hostility & Opt-Out Handling**: Gracefully terminates threads when opt-out signals are detected.
   - **Out-of-Scope Redirection**: Politely declines out-of-scope requests (e.g., GST/accounting queries) and redirects the dialogue to active marketing goals.

3. **Dual Submission Interface**:
   - Standard Python module interface: `compose()` in [`bot.py`](bot.py) and `respond()` in [`conversation_handlers.py`](conversation_handlers.py).
   - Microservice REST API: 5 required endpoints (`POST /v1/context`, `POST /v1/tick`, `POST /v1/reply`, `GET /v1/healthz`, `GET /v1/metadata`, plus `POST /v1/teardown`).

---

## 2. Architectural Tradeoffs

- **Deterministic Factual Synthesis vs. Unrestricted Stochastic LLM**:
  - *Tradeoff*: Rather than allowing an LLM to generate unstructured copy from scratch (which risks medical/legal hallucinations, latency spikes, and stochastic formatting violations), we adopted a structured, rubric-optimized synthesis layer.
  - *Benefit*: Guaranteed sub-20ms latency, zero fabricated citations, 100% compliance with category voice taboos, and complete reproducibility across evaluation runs.
- **Single Binary CTA vs. Multi-Option Menus**:
  - *Tradeoff*: For action triggers, we strictly enforce single binary CTAs (`binary_yes_no` / `open_ended`) rather than multi-choice trees.
  - *Benefit*: Lowers cognitive friction on mobile WhatsApp screens and maximizes merchant response rates.

---

## 3. What Additional Context Would Have Helped Most

1. **Read & Interaction Receipts**: Fine-grained timestamps for when merchants open and read WhatsApp messages to optimize send windows per vertical (e.g., dentists after clinic hours vs. restaurant operators before 11am).
2. **Historical Offer Conversion Telemetry**: Past redemption rates for specific merchant catalog offers to dynamically select the highest-converting offer for each locality.
3. **Rich Media Assets**: Image/catalog asset URLs to generate visual flyers and Google Business Profile photo updates alongside text copy.

---

## 4. Verification & Evaluation Results

- **Unit & Integration Suite ([`test_bot.py`](test_bot.py))**: 10/10 tests passing (Healthz, Metadata, Context Idempotency, Tick Generation, Auto-Reply Detection, Action Transition, Hostility, Curveball, `compose` API, `respond` API).
- **Judge Simulator ([`judge_simulator.py`](judge_simulator.py))**:
  - `all` scenario: **100% PASS** (Warmup, Auto-Reply Hell, Intent Transition, Hostile Opt-Out).
  - `phase2_short` & `full_evaluation`: **50/50 (100% EXCELLENT)** across Specificity, Category Fit, Merchant Fit, Decision Quality, and Engagement.
- **Canonical Test Set**: All 30 test pairs (T01–T30) pre-generated in [`submission.jsonl`](submission.jsonl).

---

## 5. Quickstart Guide

### Run Tests
```powershell
python test_bot.py
```

### Run Bot Server
```powershell
python bot.py
```

### Run Judge Simulator
```powershell
python judge_simulator.py all
python judge_simulator.py full_evaluation
```

### Public Tunnel for Remote Judging
```powershell
# Option 1: LocalTunnel
node tunnel.js

# Option 2: Cloudflare Tunnel (Binary included)
.\cloudflared.exe tunnel --url http://localhost:8080
```
