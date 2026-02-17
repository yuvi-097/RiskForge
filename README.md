# 🛡️ RiskForge — Financial Risk & Fraud Detection System

Distributed AI-Powered Financial Risk & Fraud Detection Microservice

RiskForge is a production-grade, microservice-based financial transaction risk engine built using FastAPI, PostgreSQL, Redis, and Celery.
It simulates how fintech systems evaluate transactions in real-time using a hybrid rule-based + machine learning scoring pipeline.

---
🧠 Problem Statement

Financial platforms must instantly determine whether a transaction is:

✅ Safe
⚠ Suspicious
🚫 Fraudulent

Incorrect approvals lead to financial loss.
Incorrect blocks lead to poor user experience.

RiskForge replicates an industry-grade fraud detection backend that:
Accepts transaction data
Evaluates behavioral risk signals
Runs ML-based fraud inference asynchronously
Generates a hybrid risk score
Produces actionable decisions

---
## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client / API Consumer                    │
└──────────────────────────────┬──────────────────────────────────┘
                               │  HTTP (REST)
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                      API GATEWAY (:8000)                         │
│  ┌──────────┐ ┌────────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │   Auth   │ │ Transactions│ │  Alerts  │ │  Rate Limiter    │  │
│  │  (JWT)   │ │  (intake)   │ │ (admin)  │ │  (Redis-backed)  │  │
│  └──────────┘ └─────┬──────┘ └──────────┘ └──────────────────┘  │
└─────────────────────┼───────────────────────────────────────────┘
                      │ Celery .send_task()
                      ▼
┌──────────────────────────────────────────────────────────────────┐
│                    RISK SERVICE (Celery Worker)                   │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────────────┐   │
│  │  ML Model  │  │ Rule Engine │  │  Hybrid Risk Scorer      │   │
│  │ (XGBoost)  │  │ (4 rules)  │  │ 0.7*ML + 0.3*Rules       │   │
│  └────────────┘  └────────────┘  └──────────────────────────┘   │
└──────────┬───────────────────────────────┬──────────────────────┘
           │                               │
           ▼                               ▼
┌──────────────────┐            ┌──────────────────┐
│   PostgreSQL     │            │      Redis       │
│   (persistent)   │            │   (cache/broker) │
36: └──────────────────┘            └──────────────────┘
```

---

## 📂 Project Structure

```
riskforge/
├── api-gateway/
│   ├── app/
│   │   ├── api/           # Route handlers (auth, transactions, alerts, health)
│   │   ├── core/          # Config, database, security, Redis, Celery client
│   │   ├── middleware/    # Rate limiter, request logging
│   │   ├── models/        # SQLAlchemy 2.0 ORM models
│   │   ├── repositories/  # Data access layer
│   │   ├── schemas/       # Pydantic request/response schemas
│   │   ├── services/      # Business logic layer
│   │   └── main.py        # FastAPI app factory
│   ├── alembic/           # Database migrations
│   ├── tests/             # Pytest test suite
│   ├── Dockerfile
│   └── requirements.txt
│
├── risk-service/
│   ├── app/
│   │   ├── ml/            # ML training script, model predictor
│   │   ├── models/        # Sync ORM models (for Celery)
│   │   ├── services/      # Rule engine, risk scorer
│   │   ├── tasks/         # Celery app + risk evaluation task
│   │   └── main.py        # FastAPI health endpoint + model loader
│   ├── tests/             # Rule engine & scoring tests
│   ├── Dockerfile
│   └── requirements.txt
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 📊 ER Diagram

```
┌──────────────────┐       ┌───────────────────────────┐       ┌─────────────────┐
│      users       │       │       transactions         │       │     alerts      │
├──────────────────┤       ├───────────────────────────┤       ├─────────────────┤
│ id (UUID) PK     │──1:N─▶│ id (UUID) PK              │──1:N─▶│ id (UUID) PK    │
│ email (unique)   │       │ user_id (FK → users.id)    │       │ transaction_id  │
│ hashed_password  │       │ amount (NUMERIC)           │       │   (FK → txn.id) │
│ role (ENUM)      │       │ is_active                  │       │ alert_type      │
│                  │       │ currency                   │       │ message         │
│ created_at       │       │ location                   │       │ resolved        │
│ updated_at       │       │ device_id                  │       │ created_at      │
│                  │       │ ip_address                 │       └─────────────────┘
│                  │       │ transaction_time           │
│                  │       │ status (ENUM)              │
│                  │       │ rule_score, ml_score       │
│                  │       │ final_score, risk_level    │
│                  │       │ created_at, updated_at     │
│                  │       └───────────────────────────┘
└──────────────────┘
```
🛠 Tech Stack

FastAPI
PostgreSQL
SQLAlchemy 2.0
Redis
Celery
Docker + Docker Compose
Pytest
Scikit-learn (Logistic Regression)
Alembic (Migrations)
JWT (OAuth2)
Pydantic BaseSettings
---

## 🚀 Quick Start

### 1. Clone & Configure

```bash
git clone https://github.com/your-repo/riskforge.git
cd riskforge
cp .env.example .env
# Edit .env — change JWT_SECRET_KEY and database passwords
```

### 2. Train the ML Model

```bash
cd risk-service
pip install -r requirements.txt
python -m app.ml.train_model

📊 Hybrid Risk Scoring Model
RiskForge combines:
ML-based fraud probability
Deterministic rule-based risk scoring
Final Risk Formula
final_score = 0.7 * ml_score + 0.3 * normalized_rule_score

```

### 3. Launch with Docker Compose

```bash
cd ..
docker-compose up --build -d
```
Services:
API Gateway
Authentication (JWT)
User management
Transaction intake
Rate limiting (Redis-based)
Risk Service
ML inference
Rule-based scoring
Hybrid risk computation
Alert generation
Infrastructure
PostgreSQL
Redis

### 4. Run Database Migrations

```bash
docker-compose exec api-gateway alembic upgrade head
```

### 5. Run Tests

```bash
# API Gateway tests
cd api-gateway && pip install -r requirements.txt && pytest -v --tb=short

# Risk Service tests
cd risk-service && pip install -r requirements.txt && pytest -v --tb=short
```

---

## 📡 API Endpoints

### Authentication
| Method | Endpoint               | Description           | Auth     |
|--------|------------------------|-----------------------|----------|
| POST   | `/api/v1/auth/register`| Register new user     | None     |
| POST   | `/api/v1/auth/login`   | Login, get JWT        | None     |
| GET    | `/api/v1/auth/me`      | Current user profile  | Bearer   |

### Transactions
| Method | Endpoint                      | Description                | Auth     |
|--------|-------------------------------|----------------------------|----------|
| POST   | `/api/v1/transactions/`       | Submit transaction         | Bearer   |
| GET    | `/api/v1/transactions/{id}`   | Get transaction (cached)   | Bearer   |
| GET    | `/api/v1/transactions/`       | List user transactions     | Bearer   |

### Alerts (Admin only)
| Method | Endpoint                          | Description            | Auth   |
|--------|-----------------------------------|------------------------|--------|
| GET    | `/api/v1/alerts/`                 | List unresolved alerts | Admin  |
| PATCH  | `/api/v1/alerts/{id}/resolve`     | Resolve an alert       | Admin  |

### Health
| Method | Endpoint    | Description           |
|--------|-------------|-----------------------|
| GET    | `/health`   | System health check   |

---

## 📋 Example API Calls

### Register
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "SecureP@ss123"}'
```

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=alice@example.com&password=SecureP@ss123"
```

### Submit Transaction
```bash
curl -X POST http://localhost:8000/api/v1/transactions/ \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 75000.00,
    "currency": "USD",
    "location": "Lagos, Nigeria",
    "device_id": "new-device-xyz",
    "ip_address": "203.0.113.42",
    "transaction_time": "2025-06-15T02:30:00Z"
  }'
```

---

## ⚙️ Environment Variables

| Variable                          | Description                      | Default                |
|-----------------------------------|----------------------------------|------------------------|
| `DATABASE_URL`                    | Async PostgreSQL connection      | See `.env.example`     |
| `DATABASE_URL_SYNC`               | Sync PostgreSQL (Celery)         | See `.env.example`     |
| `REDIS_URL`                       | Redis connection URL             | `redis://redis:6379/0` |
| `JWT_SECRET_KEY`                  | JWT signing secret               | **CHANGE ME**          |
| `CELERY_BROKER_URL`               | Celery broker (Redis)            | `redis://redis:6379/1` |
| `CELERY_RESULT_BACKEND`           | Celery result backend            | `redis://redis:6379/2` |

---

## 🏭 Deployment (Render)

Deploy easily using `render.yaml`. See deployment guide.
