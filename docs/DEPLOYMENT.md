# PROJECTLUNA Deployment Runbook

## Metadata

- Last verified: 2026-06-18 KST
- Owner: PROJECTLUNA
- Production IP: 168.107.9.177
- OS user: ubuntu
- Production directory: /home/ubuntu/stock-chart-tutor
- Development directory: /home/ubuntu/stock-chart-tutor-dev
- Backend venv: /home/ubuntu/stock-chart-tutor/backend/.venv
- Wallet directory: /home/ubuntu/stock-chart-tutor/backend/wallet
- DB name: projectluna-db
- PM2 production processes: luna-frontend, luna-backend
- PM2 development process: luna-frontend-dev
- Removed process: luna-backend-dev

## Purpose

Production deployment and recovery runbook for PROJECTLUNA.

## Health Checks

Backend:

```bash
curl http://127.0.0.1:8000/health
```

Expected:

```json
{"ok":true}
```

Database:

```bash
curl http://127.0.0.1:8000/health/db
```

Expected:

```json
{"ok":true,"status":"connected"}
```

## PM2

```bash
pm2 list
pm2 status luna-frontend
pm2 status luna-backend
pm2 logs luna-frontend --lines 100
pm2 logs luna-backend --lines 100
pm2 restart luna-frontend
pm2 restart luna-backend
pm2 save
pm2 resurrect
```

## Nginx

Configuration:

```text
/etc/nginx/sites-available/default
/etc/nginx/sites-enabled/default
```

Upstreams:

```text
frontend -> 127.0.0.1:3000
backend -> 127.0.0.1:8000
```

## Recovery Reference

- Oracle VM
- PROJECT-LUNA Boot Volume
- Oracle Autonomous Database projectluna-db
- Nginx
- PM2
- TCP 80 allowed
- Public URL: http://168.107.9.177
