# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Lemonsqueepy is a Python backend service for account and payment management built on [Lemon Squeezy](https://www.lemonsqueezy.com/). It provides Google OAuth sign-in, order/subscription/license verification, and license activation via REST APIs. It is designed to sit between a frontend app and Lemon Squeezy, handling webhook ingestion and user-facing queries.

## Commands

### Install dependencies
```
pip install pipenv
pipenv install --dev
```

### Run the server locally
```
pipenv run hypercorn app:app
```
The server binds to port 8000 by default (Hypercorn default).

### Run all tests
```
pipenv run pytest
```

### Run a single test file or function
```
pipenv run pytest tests/test_oauth.py
pipenv run pytest tests/test_mongo_db.py::test_convert_id_to_str_in_json
```

### Format code
```
pipenv run autopep8 --in-place <file>
```

### Production process management
PM2 is used in production (`pm2.json`). Nginx reverse-proxies to port 8000 (`lemon.mthli.com.conf`).

## Architecture

### Web Framework
Quart (async Flask-compatible) with Hypercorn ASGI server. CORS is globally enabled. Routes are defined in `app.py`.

### Data Flow
1. **Webhook ingestion** (`POST /api/webhooks/lemonsqueezy`): Lemon Squeezy sends signed webhook events. `lemon.py` verifies the `X-Signature` header, parses the `X-Event-Name`, and dispatches to the appropriate MongoDB insert function based on event prefix (`order_`, `subscription_payment_`, `subscription_`, `license_`).
2. **Check endpoints** (`GET /api/orders/check`, `/api/subscriptions/check`, `/api/licenses/check`): Query MongoDB for the latest matching record and return an `available` boolean plus status/timestamps.
3. **License activation** (`POST /api/licenses/activate`): Calls the Lemon Squeezy API, then retrieves the updated license and returns it.

### Data Layer (`mongo/`)
- `db.py` — Motor (async MongoDB) client, connects to `localhost:27017`, database `lemonsqueezy`. Contains two recursive JSON transformers used on webhook payloads before insertion:
  - `convert_id_to_str_in_json` — coerces int `id`/`*_id` fields to str
  - `convert_at_to_datetime_in_json` — parses ISO-8601 `*_at` string fields to `datetime`
- `users.py`, `orders.py`, `subscriptions.py`, `licenses.py` — each module defines index setup, insert/upsert, query (with `@alru_cache(ttl=10)`), and response conversion functions. Cache is cleared on writes.
- Webhook payloads are stored verbatim (after type conversion) as nested MongoDB documents mirroring the Lemon Squeezy JSON structure (e.g., `data.attributes.status`).

### Configuration and Secrets (`rds.py`)
All secrets are stored in Redis (`localhost:6379`), not in env vars or config files:
- `lemonsqueezy_signing_secret` — 16-char string used both for webhook signature verification and AES-128 user token encryption
- `lemonsqueezy_api_key` — Lemon Squeezy API bearer token
- `google_oauth_client_ids` — Redis SET of allowed Google OAuth client IDs

### Authentication (`oauth.py`)
- **Anonymous users**: `POST /api/user/register` generates a UUID + AES-encrypted token. All subsequent requests use `Authorization: Bearer <token>`.
- **Google OAuth**: `POST /api/user/oauth/google` decodes Google JWT credentials, matches to existing user by token or email, or creates a new user.
- User tokens are AES-128-EAX encrypted JSON containing `user_id` and `generate_timestamp`.

## Key Conventions

- Python 3.14 target (per Pipfile).
- All database/HTTP operations are async (`await`).
- MongoDB query functions use `@alru_cache(ttl=10)` for short-lived caching; cache is explicitly cleared after inserts/upserts.
- Tests in `tests/` use pytest with pytest-asyncio. The `tests/__init__.py` file exists solely to fix `ModuleNotFoundError` with pytest imports.
- Test functions that need secrets (like the signing secret) pass them directly as parameters rather than reading from Redis.

## Required Infrastructure

Running the server locally requires:
- Redis on `localhost:6379` (with the three keys above populated)
- MongoDB on `localhost:27017`
