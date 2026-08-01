# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Three independent FastAPI microservices (`user-service`, `order-service`, `notification-service`) wired together by Kafka, with Postgres per service and Redis for caching. There is no shared library or monorepo tooling — each service has its own `requirements.txt`, `Dockerfile`, and `.venv/`, and duplicates the `app/{api,core,db,schemas,services}` layout.

Comments and print statements throughout the codebase are in Russian; match that when editing existing files.

This is a personal learning project for practicing microservice patterns — not production code. Favor the canonical, idiomatic way of doing something over a clever shortcut, and explain the reasoning behind architectural changes rather than just applying them. Don't add production hardening (rate limiting, retries, observability) unless asked, but do call out real-world concerns as you go.

## Commands

Everything runs through Docker Compose from the repo root:

```bash
docker compose up --build        # all services + postgres x2 + redis + kafka
docker compose up -d kafka redis users_db orders_db   # infra only, for local service runs
docker compose logs -f order_service
```

Running a single service locally (each service has its own venv):

```bash
cd order-service && source .venv/bin/activate
uvicorn app.main:app --reload --port 8002    # user-service: 8001, notification-service: 8003
```

Alembic migrations exist **only for order-service** and must be run from `order-service/` (paths in `alembic.ini` are relative to it):

```bash
cd order-service
alembic revision --autogenerate -m "message"
alembic upgrade head
```

`user-service` has no migrations directory; its schema comes from `create_db_and_tables()` in `app/db/session.py`, which is currently commented out of the lifespan in `app/main.py` — the `users` table must be created by hand or by re-enabling that call.

No test suite or linter is configured (pytest is not in any `requirements.txt`).

Ports: user 8001, order 8002, notification 8003, users_db 5432, orders_db **5433**, redis 6379, kafka 9092 (in-cluster) / 9094 (from host).

## Architecture

**Event flow.** `POST /orders/` writes the order to Postgres, then `app/services/kafka_producer.py` publishes to the topic `orders.v1.created`. `notification-service` consumes that topic in a background asyncio task started from its lifespan (`consume_notifications`, group `notification_group`, `auto_offset_reset=earliest`) and fakes an email send. This topic name is the only contract between the two services — changing the payload in `order-service/app/api/orders.py` requires updating `notification-service/app/services/kafka_consumer.py`.

**Resource lifecycle.** Redis and Kafka clients are module-level globals initialized in each service's `lifespan` (`init_redis`/`init_kafka`) and accessed via `get_redis()` / the `kafka_producer` global. They are `None` outside an app lifespan, so any script or test touching them must run the lifespan or set them explicitly.

**Caching.** `GET /orders/{id}` reads `order:{id}` from Redis first and returns the raw parsed JSON on a hit; on a miss it queries Postgres and writes back with a 300s TTL. Nothing invalidates this key — order mutations must delete it explicitly.

**Auth.** `user-service` uses `fastapi-users` with UUID ids and a JWT bearer backend (`app/core/auth.py`). Routers are mounted in `app/api/auth.py` with prefixes on the *nested* routers only (`auth_route` itself has no prefix) — adding one there would produce `/auth/auth/jwt/login`. Tokens are signed with the shared root `JWT_SECRET`; other services are meant to verify with the same secret, but **no order-service endpoint currently checks auth** — `user_id` arrives unvalidated in the request body.

**Config.** Each service has its own `pydantic-settings` `Settings` in `app/core/config.py`, and the `env_file` paths are inconsistent: order-service uses `.env`, user/notification use `../.env`. Since they resolve against the process CWD, only the root `.env` is picked up when running from a service directory, and order-service silently falls back to its in-code defaults (`localhost:5433`, `localhost:9094`) — those defaults are what make local non-Docker runs work. In Compose, config comes from explicit `environment:` blocks instead.

**Known rough edges.** `order-service/app/db/session.py` imports `python-dotenv`, which is not in its `requirements.txt` (works in the venv, breaks in a clean Docker build). `OrderResponse` omits `created_at`, and `Order.status` uses `create_type=False`, so the `orderstatus` Postgres enum must already exist when the initial migration runs.
