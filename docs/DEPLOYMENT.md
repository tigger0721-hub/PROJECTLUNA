# PROJECTLUNA Deployment Guide

## Current Production Architecture

- Oracle VM
- Oracle Autonomous Database (projectluna-db)
- Nginx
- PM2
- FastAPI Backend
- Next.js Frontend

Public IP:

`168.107.9.177`

## PM2 Processes

### Production Processes

```text
luna-frontend
luna-backend
```

### Development Process

```text
luna-frontend-dev
```

### Important

`luna-backend-dev` was removed because it caused operational issues and must not be considered a required production process.

### Operations

```bash
pm2 list
pm2 status luna-frontend
pm2 status luna-backend
pm2 logs luna-frontend
pm2 logs luna-backend
pm2 restart luna-frontend
pm2 restart luna-backend
pm2 restart luna-frontend luna-backend
pm2 save
```

## Health Checks

Application:

```text
/health
```

Database:

```text
/health/db
```

Expected:

```json
{"ok": true}
```

## Recovery History (2026-06-18)

- Created new Oracle VM
- Attached existing PROJECT-LUNA Boot Volume
- Assigned Public IP 168.107.9.177
- Started Oracle Autonomous Database projectluna-db
- Verified /health
- Verified /health/db
- Verified Nginx
- Verified frontend browser access
- Opened and saved iptables port 80 rule

## Recovery Procedure

1. Verify Oracle VM state
2. Attach PROJECT-LUNA Boot Volume if VM recreated
3. Start projectluna-db
4. Verify PM2 processes:
   - luna-frontend
   - luna-backend
5. Verify Nginx
6. Verify iptables port 80
7. Verify /health
8. Verify /health/db
9. Verify browser access

## Validation Checklist

- projectluna-db running
- luna-frontend running
- luna-backend running
- Nginx active
- /health OK
- /health/db OK
- Port 80 open
- Frontend accessible
