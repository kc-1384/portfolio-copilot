# AI Portfolio Co-Pilot

**An AI risk co-pilot for investors who hold Indian (NSE/BSE) and US (NYSE/NASDAQ) stocks.**

Upload your portfolio, say how much loss you can afford, and the Co-Pilot watches every holding.
When a stock falls unusually hard, it explains *why* (market, sector or company), estimates the
**probability that it is a temporary dip rather than a lasting decline**, and checks the move against
your personal **loss budget** before suggesting Hold / Average down / Reduce / Exit — with reasons.

> ⚠️ **Disclaimer:** This is an educational research project, not investment advice. It outputs
> probabilities, never certainties. Nothing here is a recommendation to buy or sell any security.
> Personalised investment advice requires SEBI (India) or SEC/state (US) registration.

---

## Why it is different

- **Two markets, one view** — ₹ and $ holdings together, with currency gains shown separately.
- **Dip or decline?** — calibrated recovery probabilities from a model trained on 15–20 years of
  historical falls (delisted stocks included), with plain-language reasons.
- **A personal loss budget** — every alert and suggestion is checked against what *you* can afford to lose.
- **Public track record** — every prediction is logged and never edited, so accuracy can be audited.

## Status

| Phase | What it delivers | Status |
|---|---|---|
| 0 – Setup | Tooling, Docker services, API skeleton, tests | ✅ Done |
| 1 – Foundation | Database, instruments, prices, auth, uploads, P&L, XIRR, dashboard | ⏳ Next |
| 2 – Brain | Drawdown dataset, dip-vs-decline model, company health score | Planned |
| 3 – Guardian | Live monitoring, smart alerts, loss-budget engine, Telegram bot | Planned |
| 4 – Advisor | Portfolio doctor, stress tests, rebalancing, discovery, goal planner | Planned |
| 5 – Complete | Tax assistant, AI chat, paper trading, web + mobile apps | Planned |
| 6 – Launch | Security, compliance, deployment, monitoring | Planned |

## Tech stack

| Layer | Choice |
|---|---|
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic — managed with **uv** |
| Database | PostgreSQL 16 + TimescaleDB, Redis 7 — in Docker |
| Background jobs | Celery + Redis (in Docker) |
| ML | pandas, scikit-learn, LightGBM/XGBoost, Optuna, SHAP, lifelines, MLflow |
| LLM | Anthropic Claude API with tool use |
| Frontend | Next.js + TypeScript, Tailwind, shadcn/ui, TanStack Query |
| Code quality | Ruff, pytest (backend) · Vitest, Playwright (frontend) |

## Project layout

```
copilot/
├── backend/   # FastAPI app (app/) and tests (tests/)
├── ml/        # model training, features, reports
├── workers/   # Celery background tasks
├── infra/     # docker-compose and deployment config
├── docs/      # diary, architecture notes, decision records
├── .env.example
└── README.md
```

## Run it locally (Windows 11)

**You need:** Git, Docker Desktop (Linux containers mode), uv, and Node.js LTS.

1. **Clone and enter the project**
   ```powershell
   git clone <your-repo-url> copilot
   cd copilot
   ```
2. **Create your settings file** and set a strong `POSTGRES_PASSWORD` in it (letters and digits only)
   ```powershell
   Copy-Item .env.example .env
   ```
3. **Start the database and Redis** (Docker Desktop must be running)
   ```powershell
   docker compose -f infra/docker-compose.yml up -d
   docker compose -f infra/docker-compose.yml ps
   ```
   Both containers should show `(healthy)`.
4. **Install backend dependencies and start the API**
   ```powershell
   cd backend
   uv sync
   uv run fastapi dev app/main.py
   ```
   Open <http://localhost:8000/docs> for the interactive API docs.
5. **Run the tests and code checks** (from `backend/`)
   ```powershell
   uv run pytest
   uv run ruff check .
   uv run ruff format --check .
   ```

**Stop the services:** `docker compose -f infra/docker-compose.yml down` (your data is kept in Docker volumes).

### Troubleshooting (Windows)

| Problem | Fix |
|---|---|
| `docker` says it must be run with elevated privileges | Add your account to the `docker-users` group (admin PowerShell: `net localgroup docker-users "<your user>" /add`), then sign out and back in. |
| Docker Desktop shows "Windows containers" | Whale icon / ⋮ menu → **Switch to Linux containers…** |
| A path with a space in it fails | Wrap the whole path in double quotes. |

## Screenshots

_Coming in Phase 1: the portfolio dashboard._

## Roadmap

See the Status table above. Each phase finishes only when its acceptance test passes.

## License

To be decided.
