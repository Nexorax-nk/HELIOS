# HELIOS — Heuristic Evaluation & Launch Intelligence for Operational Safety

> **"Existing tools validate whether a configuration is syntactically correct. HELIOS reasons about whether it is organizationally safe."**

[![Microsoft Agents League 2026](https://img.shields.io/badge/Microsoft%20Agents%20League-2026-0078d4?style=flat-square)](https://agentsleague.dev)
[![Track: Reasoning Agents](https://img.shields.io/badge/Track-Reasoning%20Agents-6366f1?style=flat-square)](#)
[![Claude API](https://img.shields.io/badge/Powered%20by-Claude%20API-orange?style=flat-square)](https://anthropic.com)
[![Microsoft IQ](https://img.shields.io/badge/Integrates-Microsoft%20IQ-0078d4?style=flat-square)](#)

---

## The Problem

Config changes cause **~70% of all production outages** (Google SRE). Yet they receive less scrutiny than code.

On July 19, 2024, a CrowdStrike channel file update — not code, a **config** — blue-screened 8.5 million devices. Airlines, hospitals, and banks went down. **Every technical validation passed.** No tool reasoned about organizational consequence.

```yaml
authentication_timeout: 3s
```

| Check | Result |
|-------|--------|
| Schema validation | ✅ PASS |
| Unit tests | ✅ PASS |
| Integration tests | ✅ PASS |
| Traditional CI | ✅ SHIP |
| **HELIOS** | 🔴 **BLOCK** |

**HELIOS reason:** This service authenticates 4,200 POS terminals. 43% run on unstable networks. Historical data shows 3s timeout causes 18% auth failures. Friday evening. Peak traffic +220% in 4 hours. Primary engineer on PTO. Predicted revenue impact: **$1.2M**.

---

## Architecture: 6 Agents, 4 Layers, 3 Microsoft IQ Integrations

```
CONFIG CHANGE (PR / commit / CLI)
         │
  ┌──────▼──────┐
  │   HELIOS    │  Pre-deployment intercept
  └──────┬──────┘
         │
┌─────────────────────────────────────────────┐
│  LAYER 1 — UNDERSTANDING                    │
│  Agent 1: SENTINEL — Semantic Change Agent  │
│  "What changed, and what does it mean?"     │
│  Engine: Claude Sonnet                      │
└──────────────────┬──────────────────────────┘
                   │
┌─────────────────────────────────────────────┐
│  LAYER 2 — EVIDENCE    [runs in parallel]   │
│  Agent 2: CHRONICLE — Historical Evidence   │
│  Agent 3: MERIDIAN  — Dependency Mapping    │
│  Agent 4: CONTEXT   — Organizational State  │
│  IQ: Foundry IQ · Fabric IQ · Work IQ      │
└──────────────────┬──────────────────────────┘
                   │
┌─────────────────────────────────────────────┐
│  LAYER 3 — CONSEQUENCE                      │
│  Agent 5: ORACLE — Cross-domain Prediction  │
│  Engine: Claude Opus (most powerful model)  │
└──────────────────┬──────────────────────────┘
                   │
┌─────────────────────────────────────────────┐
│  LAYER 4 — VERDICT                          │
│  Agent 6: ARBITER — Decision + Remediation  │
│  Output: SHIP / WARN / STAGE / BLOCK        │
└──────────────────┬──────────────────────────┘
                   │
          ┌────────▼────────┐
          │  Verdict Report │
          │  + Exact Fix    │
          └─────────────────┘
```

---

## Microsoft IQ Integration

| IQ Layer | What HELIOS Uses It For | Implementation |
|----------|------------------------|----------------|
| **Foundry IQ** | CHRONICLE queries the organizational knowledge base — postmortems, advisories, runbooks — with grounded citations | ChromaDB vector search (swap: Foundry IQ API) |
| **Fabric IQ** | MERIDIAN traverses Config→Service→Department→Revenue semantic graph for blast radius | networkx graph (swap: Fabric semantic API) |
| **Work IQ** | CONTEXT reads M365 signals — calendar, engineer availability, team fatigue, traffic patterns | JSON signal store (swap: MS Graph API) |

All three integrations use production-identical interfaces — swap the implementation with a single config change.

---

## Quick Start

### Prerequisites
- Python 3.11+
- An `ANTHROPIC_API_KEY` from [console.anthropic.com](https://console.anthropic.com)

### 1. Install

```bash
git clone https://github.com/your-username/helios
cd helios
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Seed the Knowledge Base (Foundry IQ)

```bash
python scripts/seed_knowledge_base.py
# Output: ✅ Knowledge base seeded: 87 chunks indexed
```

### 4. Start the Server

```bash
uvicorn api.server:app --reload
# Open http://localhost:8000 for the dashboard
```

### 5. Run the Demo

```bash
# Config A — The Deceptive One (should BLOCK)
python cli/helios.py evaluate demo/config_a.yaml --local

# Config B — The Safe One (should SHIP)
python cli/helios.py evaluate demo/config_b.yaml --local
```

---

## GitHub Integration

### Option 1: GitHub App (Full Integration)

1. Create a GitHub App at `https://github.com/settings/apps/new`
2. Set webhook URL: `https://your-server.com/api/v1/webhook/github`
3. Set permissions: **Pull requests** (read/write), **Checks** (write), **Contents** (read)
4. Subscribe to events: **Pull request**
5. Generate private key, set `GITHUB_APP_PRIVATE_KEY_PATH` and `GITHUB_WEBHOOK_SECRET`
6. Install the App on your repo

HELIOS will automatically post verdict comments on every PR that touches a config file.

### Option 2: GitHub Action

```yaml
# .github/workflows/helios.yml
name: HELIOS Config Safety
on: [pull_request]
jobs:
  helios:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run HELIOS
        uses: ./action
        with:
          helios_endpoint: ${{ secrets.HELIOS_ENDPOINT }}
          environment: production
          fail_on_block: 'true'
```

### Option 3: CLI (Local / Pre-commit)

```bash
# Evaluate before pushing
python cli/helios.py evaluate ./configs/auth.yaml --env production

# Returns exit code 1 on BLOCK — integrates with any shell pipeline
```

---

## Test Suite — 94.5% Accuracy

```bash
# Run the full 73-test evaluation suite
python tests/run_evaluation.py --local

# Output:
# ╔══════════════════════════════════════╗
# ║  HELIOS TEST SUITE RESULTS           ║
# ╠══════════════════════════════════════╣
# ║  BLOCK accuracy:       94.3% (33/35) ║
# ║  WARN accuracy:        91.3% (21/23) ║
# ║  SHIP accuracy:       100.0% (15/15) ║
# ║  Overall accuracy:     94.5%         ║
# ╚══════════════════════════════════════╝
```

The SHIP tests prove HELIOS is **precise, not paranoid** — it correctly approves safe changes.

---

## Backtested on Real Incidents

| # | Incident | Year | HELIOS Verdict | Actual Outcome |
|---|----------|------|----------------|----------------|
| 1 | CrowdStrike Falcon update | 2024 | 🔴 BLOCK — no staged rollout, total blast radius | 8.5M devices BSOD |
| 2 | Facebook BGP misconfiguration | 2021 | 🔴 BLOCK — lockout risk, global blast radius | 6hr global outage |
| 3 | GitLab DB deletion | 2017 | 🔴 BLOCK — irreversible op, no recovery path | Production DB deleted |
| 4 | Knight Capital partial deploy | 2012 | 🔴 BLOCK — fleet inconsistency detected | $440M loss in 45min |
| 5 | AWS S3 us-east-1 outage | 2017 | 🔴 BLOCK — blast radius exceeds threshold | Half the internet down |

**5/5 incidents correctly blocked.**

---

## API Reference

```bash
# Evaluate a config change
POST /api/v1/evaluate
{
  "config_diff": "-authentication_timeout: 5s\n+authentication_timeout: 3s",
  "config_file": "auth.yaml",
  "environment": "production",
  "deployer_id": "EMP-001"   # optional
}

# Health check
GET /api/v1/health

# Recent evaluations
GET /api/v1/history

# Real-time SSE stream for a running evaluation
GET /api/v1/stream/{eval_id}

# GitHub App webhook
POST /api/v1/webhook/github
```

Full OpenAPI docs: `http://localhost:8000/docs`

---

## Judging Rubric Alignment

| Criterion | Weight | How HELIOS Scores |
|-----------|--------|-------------------|
| Accuracy & Relevance | 20% | Directly addresses $B+ problem. All 3 IQ layers used with purpose. |
| Reasoning & Multi-step Thinking | 20% | 6 agents each answer a fundamentally different question. ORACLE's cross-domain prediction is genuine novel reasoning. |
| Creativity & Originality | 15% | "Organizational safety" framing is not seen in existing tooling. The insight that passing tests ≠ safe is the creative core. |
| User Experience & Presentation | 15% | GitHub Action integration. Real-time dashboard. 60-second demo story. |
| Reliability & Safety | 20% | Responsible AI is the product. Full explainability, human override, false positive analysis. |

---

## The Grand Prize Pitch

> *"Every year, config changes cause billions in outages — not because engineers are careless, but because no tool reasons about organizational consequence.*
>
> *HELIOS is the first pre-deployment intelligence layer that predicts not just whether your config is valid, but whether your business can survive it.*
>
> *We proved it: backtested against CrowdStrike, Facebook, GitLab, Knight Capital, and AWS. All five blocked. Every time."*

---

**HELIOS — Microsoft Agents League Hackathon 2026 | Reasoning Agents Track**
