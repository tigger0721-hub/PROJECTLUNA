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

This document is the production deployment and disaster recovery runbook for PROJECTLUNA.

Use this document when the public service URL is unavailable, PM2 processes are stopped, Nginx is failing, the Oracle Autonomous Database is stopped, or firewall rules block public access.

## Current Architecture

PROJECTLUNA runs on Oracle Cloud Infrastructure.

```text
Browser
  -> http://168.107.9.177
  -> Oracle VM
  -> iptables TCP 80
  -> Nginx
  -> Next.js frontend on port 3000
  -> FastAPI backend on port 8000
  -> Oracle Autonomous Database projectluna-db
```

Production components:

- Oracle VM
- PROJECT-LUNA Boot Volume
- Oracle Autonomous Database projectluna-db
- Nginx
- PM2
- Next.js frontend
- FastAPI backend

## Server Paths

Production root:

```text
/home/ubuntu/stock-chart-tutor
```

Development root:

```text
/home/ubuntu/stock-chart-tutor-dev
```

Backend directory:

```text
/home/ubuntu/stock-chart-tutor/backend
```

Frontend directory:

```text
/home/ubuntu/stock-chart-tutor/frontend
```

Backend virtual environment:

```text
/home/ubuntu/stock-chart-tutor/backend/.venv
```

Oracle wallet directory:

```text
/home/ubuntu/stock-chart-tutor/backend/wallet
```

## PM2 Processes

Required production processes:

```text
luna-frontend
luna-backend
```

Development process:

```text
luna-frontend-dev
```

Removed process:

```text
luna-backend-dev
```

`luna-backend-dev` was removed because it caused an operational incident. Do not restore it as a required production process.

## PM2 Operations

List processes:

```bash
pm2 list
```

Check production status:

```bash
pm2 status luna-frontend
pm2 status luna-backend
```

Read recent logs:

```bash
pm2 logs luna-frontend --lines 100
pm2 logs luna-backend --lines 100
```

Restart production processes:

```bash
pm2 restart luna-frontend
pm2 restart luna-backend
pm2 restart luna-frontend luna-backend
```

Save and restore PM2 process list:

```bash
pm2 save
pm2 resurrect
```

## PM2 Process Recreation

Use these commands only if PM2 processes are missing from `pm2 list`.

Recreate production backend:

```bash
cd /home/ubuntu/stock-chart-tutor/backend
pm2 start "bash -lc 'source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000'" --name luna-backend
```

Recreate production frontend:

```bash
cd /home/ubuntu/stock-chart-tutor/frontend
pm2 start "npm run start" --name luna-frontend
```

Save recreated process list:

```bash
pm2 save
```

Do not recreate `luna-backend-dev` as a production requirement.

## Manual Runtime Commands

Manual backend command:

```bash
cd /home/ubuntu/stock-chart-tutor/backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Manual frontend command:

```bash
cd /home/ubuntu/stock-chart-tutor/frontend
npm run start
```

For normal operation, use PM2 instead of foreground manual commands.

## Health Checks

Backend health:

```bash
curl http://127.0.0.1:8000/health
```

Expected:

```json
{"ok":true}
```

DB health:

```bash
curl http://127.0.0.1:8000/health/db
```

Expected:

```json
{"ok":true,"status":"connected"}
```

Nginx through frontend:

```bash
curl -I http://127.0.0.1
```

Frontend direct:

```bash
curl -I http://127.0.0.1:3000
```

Public browser:

```text
http://168.107.9.177
```

## Nginx Configuration

Primary Nginx configuration path:

```text
/etc/nginx/sites-available/default
```

Enabled site path:

```text
/etc/nginx/sites-enabled/default
```

Expected upstream targets:

```text
frontend upstream: http://127.0.0.1:3000
backend upstream: http://127.0.0.1:8000
```

Expected routing basis:

- `/` routes to the frontend upstream on port 3000
- backend API and health routes route to the backend upstream on port 8000
- `/health` routes to `http://127.0.0.1:8000/health`
- `/health/db` routes to `http://127.0.0.1:8000/health/db`

Check Nginx status:

```bash
sudo systemctl status nginx
```

Validate Nginx configuration:

```bash
sudo nginx -t
```

Reload Nginx:

```bash
sudo systemctl reload nginx
```

Restart Nginx:

```bash
sudo systemctl restart nginx
```

## Firewall Recovery

During the 2026-06-18 recovery, the server was healthy internally but public access was blocked until TCP port 80 was allowed in iptables.

Allow and persist TCP port 80:

```bash
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo apt install -y iptables-persistent
sudo netfilter-persistent save
sudo netfilter-persistent reload
sudo iptables -L -n -v
```

Normal criteria:

- TCP port 80 is allowed
- the rule remains after reload
- public browser access works

If public access still fails, verify OCI security rules as well.

## Recovery Procedure

Follow the steps in order.

### Step 1. Oracle VM Running

Check command:

```text
OCI Console -> Compute -> Instances
```

Normal criteria:

- Oracle VM exists
- state is Running

Failure action:

- create a new Oracle VM
- attach the existing PROJECT-LUNA Boot Volume
- assign a public IP

### Step 2. Boot Volume PROJECT-LUNA Attached

Check command:

```text
OCI Console -> Compute -> Boot Volumes
```

Normal criteria:

- PROJECT-LUNA Boot Volume exists
- boot volume is attached to the active VM

Server verification:

```bash
ls -la /home/ubuntu/stock-chart-tutor
```

Failure action:

- attach PROJECT-LUNA Boot Volume to the active VM
- boot from the attached volume
- verify the production directory

### Step 3. Public IP Assigned

Check command:

```text
OCI Console -> Instance details -> Public IP
```

Normal criteria:

```text
168.107.9.177
```

Failure action:

- assign a public IP
- update any external references if the IP changes

### Step 4. Autonomous DB Available

Check command:

```text
OCI Console -> Oracle Autonomous Database -> projectluna-db
```

Normal criteria:

```text
Available
```

Failure action:

- start `projectluna-db`
- wait until Available
- restart `luna-backend` if DB health still fails

### Step 5. SSH Access

Check command:

```bash
ssh ubuntu@168.107.9.177
```

Normal criteria:

- SSH login succeeds as `ubuntu`

Failure action:

- verify VM state
- verify public IP
- verify SSH security rules
- verify SSH key

### Step 6. PM2 Processes

Check command:

```bash
pm2 list
```

Normal criteria:

- `luna-frontend` is online
- `luna-backend` is online
- `luna-backend-dev` is not required

Failure action:

```bash
pm2 restart luna-frontend luna-backend
pm2 resurrect
```

If processes do not exist, recreate them:

```bash
cd /home/ubuntu/stock-chart-tutor/backend
pm2 start "bash -lc 'source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000'" --name luna-backend
cd /home/ubuntu/stock-chart-tutor/frontend
pm2 start "npm run start" --name luna-frontend
pm2 save
```

### Step 7. Backend Health

Check command:

```bash
curl http://127.0.0.1:8000/health
```

Normal criteria:

```json
{"ok":true}
```

Failure action:

```bash
pm2 logs luna-backend --lines 100
pm2 restart luna-backend
```

If needed, run manual backend test:

```bash
cd /home/ubuntu/stock-chart-tutor/backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Step 8. DB Health

Check command:

```bash
curl http://127.0.0.1:8000/health/db
```

Normal criteria:

```json
{"ok":true,"status":"connected"}
```

Failure action:

- confirm `projectluna-db` is Available
- verify DB environment variables
- verify wallet directory
- restart `luna-backend`

Wallet check:

```bash
ls -la /home/ubuntu/stock-chart-tutor/backend/wallet
```

### Step 9. Nginx Status

Check command:

```bash
sudo systemctl status nginx
```

Normal criteria:

```text
active (running)
```

Failure action:

```bash
sudo nginx -t
sudo systemctl restart nginx
```

### Step 10. iptables Port 80

Check command:

```bash
sudo iptables -L -n -v
```

Normal criteria:

- TCP 80 is allowed

Failure action:

```bash
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo apt install -y iptables-persistent
sudo netfilter-persistent save
sudo netfilter-persistent reload
sudo iptables -L -n -v
```

### Step 11. Browser Access

Check command:

```text
http://168.107.9.177
```

Normal criteria:

- frontend loads
- analysis result page works

Failure action:

```bash
curl -I http://127.0.0.1
curl -I http://127.0.0.1:3000
curl http://127.0.0.1:8000/health
```

Then check Nginx, PM2, iptables, and OCI security rules.

## Recovery History: 2026-06-18

### Date

2026-06-18 KST

### Impact

- Public service URL was unavailable
- Frontend browser access failed
- PROJECTLUNA could not be used externally

### Root Cause

- Oracle VM instance was not listed in OCI
- only the PROJECT-LUNA Boot Volume remained
- Oracle Autonomous Database `projectluna-db` was Stopped
- server internals were healthy after VM recovery
- public access was still blocked by iptables until TCP port 80 was allowed

### Recovery Actions

1. Created a new Oracle VM
2. Attached existing PROJECT-LUNA Boot Volume
3. Assigned public IP `168.107.9.177`
4. Started Oracle Autonomous Database `projectluna-db`
5. Verified backend `/health`
6. Verified backend `/health/db`
7. Verified Nginx
8. Verified frontend browser access
9. Allowed TCP port 80 through iptables
10. Installed iptables persistence
11. Saved and reloaded firewall rules

### Validation Evidence

Backend health:

```bash
curl http://127.0.0.1:8000/health
```

Expected:

```json
{"ok":true}
```

DB health:

```bash
curl http://127.0.0.1:8000/health/db
```

Expected:

```json
{"ok":true,"status":"connected"}
```

Nginx frontend:

```bash
curl -I http://127.0.0.1
```

Frontend direct:

```bash
curl -I http://127.0.0.1:3000
```

Public browser:

```text
http://168.107.9.177
```

### Remaining Risks

- public IP may change if VM is recreated
- Nginx config must be checked after manual edits
- PM2 process list must be saved after process recreation
- firewall persistence must be checked after reboot
- monitoring and alerting are not automated

### Prevention and Follow-up

- keep this runbook updated
- add uptime monitoring
- add HTTPS and DNS documentation
- add backup and restore checklist
- document any future PM2 or Nginx config change

### Related PR

- #80

## Failure Scenario Table

| Case | Symptom | Check command | Possible cause | Action |
|---|---|---|---|---|
| Public URL unavailable | Browser cannot open service | `curl -I http://168.107.9.177` | VM down, Nginx down, port 80 blocked, OCI rule missing | Check VM, Nginx, iptables, OCI security rules |
| Nginx 502 or 504 | Gateway error | `sudo systemctl status nginx` | frontend or backend upstream down | Restart PM2 processes and reload Nginx |
| PM2 process stopped | PM2 shows stopped or errored | `pm2 list` | crash, missing env, manual stop | Restart or recreate `luna-frontend` and `luna-backend` |
| Backend health fails | `/health` is not OK | `curl http://127.0.0.1:8000/health` | backend down, import error, venv issue | Check backend logs and restart backend |
| DB health fails | `/health/db` is not connected | `curl http://127.0.0.1:8000/health/db` | DB stopped, wallet error, DB env error | Start DB, verify wallet and env, restart backend |
| Oracle DB stopped | DB is Stopped in OCI | OCI DB status | Autonomous DB stopped | Start `projectluna-db` |
| Port 80 blocked | local checks pass but public URL fails | `sudo iptables -L -n -v` | iptables blocks TCP 80 | Add TCP 80 rule and save persistently |
| Frontend direct 3000 OK but public URL fails | port 3000 works but browser fails | `curl -I http://127.0.0.1:3000` | Nginx or firewall issue | Check Nginx config and port 80 |
| Backend dependency import failure | backend exits or restarts | `pm2 logs luna-backend --lines 100` | missing package, wrong venv, broken import | Activate venv, install dependencies, run manual uvicorn test |
| Development backend restart loop | dev backend repeatedly restarts | `pm2 list` | `luna-backend-dev` restored | Stop or delete `luna-backend-dev`; do not treat it as production |

## Post-Recovery Checklist

- [ ] `http://168.107.9.177` is accessible
- [ ] `curl http://127.0.0.1:8000/health` returns `{"ok":true}`
- [ ] `curl http://127.0.0.1:8000/health/db` returns `{"ok":true,"status":"connected"}`
- [ ] `pm2 list` shows `luna-frontend` online
- [ ] `pm2 list` shows `luna-backend` online
- [ ] Nginx is active
- [ ] iptables allows TCP 80
- [ ] Oracle DB `projectluna-db` is Available
- [ ] Analysis result page works
