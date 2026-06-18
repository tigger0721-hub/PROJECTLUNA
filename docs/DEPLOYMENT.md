# PROJECTLUNA Deployment Runbook

## Document Metadata

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

This document is the production deployment and recovery runbook for PROJECTLUNA.

The goal is to restore the service quickly when the Oracle VM, boot volume, database, PM2 process, Nginx, firewall, or public access path fails.

This runbook is based on the production recovery completed on 2026-06-18.

## Current Production Architecture

PROJECTLUNA currently runs on Oracle Cloud Infrastructure.

Production components:

- Oracle VM
- Existing PROJECT-LUNA Boot Volume
- Oracle Autonomous Database
- Nginx
- PM2
- FastAPI backend
- Next.js frontend

Runtime flow:

```text
User browser
  -> http://168.107.9.177
  -> OCI public network
  -> VM iptables port 80
  -> Nginx
  -> Frontend: luna-frontend
  -> Backend: luna-backend
  -> Oracle Autonomous Database: projectluna-db
```

## Directory Layout

Production application directory:

```text
/home/ubuntu/stock-chart-tutor
```

Development application directory:

```text
/home/ubuntu/stock-chart-tutor-dev
```

Production backend directory:

```text
/home/ubuntu/stock-chart-tutor/backend
```

Production frontend directory:

```text
/home/ubuntu/stock-chart-tutor/frontend
```

Production backend virtual environment:

```text
/home/ubuntu/stock-chart-tutor/backend/.venv
```

Production Oracle wallet directory:

```text
/home/ubuntu/stock-chart-tutor/backend/wallet
```

## PM2 Process Model

### Required Production Processes

The following PM2 processes are required for production operation:

```text
luna-frontend
luna-backend
```

### Development Process

The following process is a development frontend process:

```text
luna-frontend-dev
```

### Removed Process

The following process was removed because it caused an operational issue:

```text
luna-backend-dev
```

Do not include `luna-backend-dev` as a required production process.

## PM2 Operations

List all processes:

```bash
pm2 list
```

Check production frontend status:

```bash
pm2 status luna-frontend
```

Check production backend status:

```bash
pm2 status luna-backend
```

Check production frontend logs:

```bash
pm2 logs luna-frontend --lines 100
```

Check production backend logs:

```bash
pm2 logs luna-backend --lines 100
```

Restart production frontend:

```bash
pm2 restart luna-frontend
```

Restart production backend:

```bash
pm2 restart luna-backend
```

Restart all required production processes:

```bash
pm2 restart luna-frontend luna-backend
```

Save PM2 process list:

```bash
pm2 save
```

Restore saved PM2 process list:

```bash
pm2 resurrect
```

## Manual Runtime Commands

These commands are for manual verification or emergency recovery.

### Backend Manual Start

```bash
cd /home/ubuntu/stock-chart-tutor/backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend Manual Start

```bash
cd /home/ubuntu/stock-chart-tutor/frontend
npm run start
```

For normal production operation, prefer PM2 restart commands instead of manual foreground execution.

## Health Checks

### Backend Health

Command:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"ok":true}
```

### Database Health

Command:

```bash
curl http://127.0.0.1:8000/health/db
```

Expected response:

```json
{"ok":true,"status":"connected"}
```

### Nginx Through Frontend

Command:

```bash
curl -I http://127.0.0.1
```

Expected result:

- HTTP response is returned
- no connection refused
- no 502 or 504 error

### Frontend Direct

Command:

```bash
curl -I http://127.0.0.1:3000
```

Expected result:

- HTTP response is returned
- frontend process is reachable directly

### Public Browser

Open:

```text
http://168.107.9.177
```

Expected result:

- PROJECTLUNA frontend loads in browser
- analysis result page works

## Nginx Operations

Check Nginx status:

```bash
sudo systemctl status nginx
```

Expected result:

```text
active (running)
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

If Nginx returns 502 or 504, check whether `luna-frontend` and `luna-backend` are online and reachable on their local ports.

## Firewall Recovery

During the 2026-06-18 recovery, the server was internally healthy but public access was blocked until TCP port 80 was allowed in iptables.

Use the following commands to allow and persist port 80:

```bash
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo apt install -y iptables-persistent
sudo netfilter-persistent save
sudo netfilter-persistent reload
sudo iptables -L -n -v
```

Expected result:

- TCP port 80 is allowed
- the rule remains after reload
- public browser access works

Also verify OCI network security rules if the public URL is still unavailable.

## Environment and Secrets

Environment variables and wallet files must survive VM recovery.

Backend-related values may include:

```text
OPENAI_API_KEY
KIS_APP_KEY
KIS_APP_SECRET
DB_USER
DB_PASSWORD
DB_DSN
DB_WALLET_DIR
DB_WALLET_PASSWORD
```

Frontend-related value may include:

```text
NEXT_PUBLIC_API_BASE
```

Database health depends on valid DB credentials and wallet configuration.

## Recovery Procedure

Follow these steps in order during an outage.

### Step 1. Check Oracle VM Running State

Check command:

```text
OCI Console -> Compute -> Instances
```

Normal criteria:

- Oracle VM exists
- state is Running

If failed:

- create a new Oracle VM
- attach the existing PROJECT-LUNA Boot Volume
- continue with public IP and service checks

### Step 2. Check PROJECT-LUNA Boot Volume Attachment

Check command:

```text
OCI Console -> Compute -> Boot Volumes
```

Normal criteria:

- PROJECT-LUNA Boot Volume exists
- boot volume is attached to the active VM
- production directory exists after SSH login

Verification command after SSH:

```bash
ls -la /home/ubuntu/stock-chart-tutor
```

If failed:

- attach the existing PROJECT-LUNA Boot Volume to the new VM
- boot the VM from the attached volume
- verify application directories

### Step 3. Check Public IP

Check command:

```text
OCI Console -> Instance details -> Public IP
```

Normal criteria:

```text
168.107.9.177
```

If failed:

- assign a public IP to the VM
- update any external references if the IP changes
- verify browser and curl access again

### Step 4. Check Autonomous DB Availability

Check command:

```text
OCI Console -> Oracle Autonomous Database -> projectluna-db
```

Normal criteria:

```text
Available
```

If failed:

- start `projectluna-db`
- wait until state becomes Available
- restart backend if DB connection does not recover automatically

### Step 5. Check SSH Access

Check command:

```bash
ssh ubuntu@168.107.9.177
```

Normal criteria:

- SSH login succeeds as `ubuntu`

If failed:

- verify VM running state
- verify public IP
- verify SSH security rule
- verify key pair
- verify OS user is `ubuntu`

### Step 6. Check PM2 Processes

Check command:

```bash
pm2 list
```

Normal criteria:

- `luna-frontend` is online
- `luna-backend` is online
- `luna-backend-dev` is not required and should not be restored as production

If failed:

```bash
pm2 restart luna-frontend luna-backend
pm2 save
```

If saved processes are missing:

```bash
pm2 resurrect
```

Then check logs:

```bash
pm2 logs luna-frontend --lines 100
pm2 logs luna-backend --lines 100
```

### Step 7. Check Backend Health

Check command:

```bash
curl http://127.0.0.1:8000/health
```

Normal criteria:

```json
{"ok":true}
```

If failed:

- check `pm2 logs luna-backend --lines 100`
- verify backend virtual environment
- verify Python dependencies
- verify import errors
- restart backend

Emergency manual test:

```bash
cd /home/ubuntu/stock-chart-tutor/backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Step 8. Check Database Health

Check command:

```bash
curl http://127.0.0.1:8000/health/db
```

Normal criteria:

```json
{"ok":true,"status":"connected"}
```

If failed:

- confirm `projectluna-db` is Available
- verify wallet directory exists
- verify backend DB environment variables
- restart `luna-backend`
- inspect backend logs

Wallet directory check:

```bash
ls -la /home/ubuntu/stock-chart-tutor/backend/wallet
```

### Step 9. Check Nginx Status

Check command:

```bash
sudo systemctl status nginx
```

Normal criteria:

```text
active (running)
```

If failed:

```bash
sudo nginx -t
sudo systemctl restart nginx
```

Then verify:

```bash
curl -I http://127.0.0.1
```

### Step 10. Check iptables Port 80

Check command:

```bash
sudo iptables -L -n -v
```

Normal criteria:

- TCP port 80 is allowed

If failed:

```bash
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo apt install -y iptables-persistent
sudo netfilter-persistent save
sudo netfilter-persistent reload
sudo iptables -L -n -v
```

### Step 11. Check Browser Access

Check command:

```text
http://168.107.9.177
```

Normal criteria:

- frontend loads
- analysis result page works

If failed:

- check `curl -I http://127.0.0.1`
- check `curl -I http://127.0.0.1:3000`
- check Nginx routing
- check iptables
- check OCI security rules

## 2026-06-18 Recovery History

### Date

2026-06-18 KST

### Impact

- PROJECTLUNA public URL was unavailable
- frontend browser access failed
- service could not be used externally

### Root Cause

- Oracle VM instance was not listed in OCI
- only the existing PROJECT-LUNA Boot Volume remained
- Oracle Autonomous Database `projectluna-db` was stopped
- server internals became healthy after recovery, but public access was still blocked
- TCP port 80 was blocked by iptables until explicitly allowed

### Recovery Actions

1. Created a new Oracle VM
2. Attached the existing PROJECT-LUNA Boot Volume
3. Assigned new Public IP `168.107.9.177`
4. Started Oracle Autonomous Database `projectluna-db`
5. Verified backend health
6. Verified database health
7. Verified Nginx status
8. Verified frontend browser access
9. Allowed TCP port 80 through iptables
10. Installed and used persistent iptables saving
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

Database health:

```bash
curl http://127.0.0.1:8000/health/db
```

Expected:

```json
{"ok":true,"status":"connected"}
```

Nginx frontend check:

```bash
curl -I http://127.0.0.1
```

Frontend direct check:

```bash
curl -I http://127.0.0.1:3000
```

Public browser:

```text
http://168.107.9.177
```

### Remaining Risks

- exact PM2 startup commands are not yet documented in this repository
- Nginx site configuration path is not yet documented in this repository
- public IP may change if a new VM is created again
- monitoring and alerting are not automated yet
- firewall persistence must be verified after reboot

### Prevention and Follow-up

- keep this runbook updated after every infrastructure change
- add exact PM2 start commands
- add Nginx configuration path and expected upstreams
- add uptime monitoring
- add backup and restore checklist
- consider HTTPS and DNS setup

### Related PR

- #80

## Failure Scenario Response Table

| Case | Symptom | Check command | Possible cause | Action |
|---|---|---|---|---|
| Public URL unavailable | Browser cannot open `http://168.107.9.177` | `curl -I http://168.107.9.177` | VM down, Nginx down, port 80 blocked, OCI rule missing | Check VM, Nginx, iptables, OCI security rules |
| Nginx 502 or 504 | Public URL returns gateway error | `sudo systemctl status nginx` and `pm2 list` | upstream frontend or backend is down | Restart `luna-frontend` and `luna-backend`, then reload Nginx |
| PM2 process stopped | PM2 shows stopped or errored process | `pm2 list` | process crash, dependency error, manual stop | `pm2 restart luna-frontend luna-backend` and inspect logs |
| Backend `/health` failure | Backend health does not return ok | `curl http://127.0.0.1:8000/health` | backend process down, import failure, venv issue | Check `pm2 logs luna-backend --lines 100`, verify venv, restart backend |
| `/health/db` failure | DB health does not return connected | `curl http://127.0.0.1:8000/health/db` | DB stopped, wallet issue, DB env issue | Start `projectluna-db`, verify wallet and env, restart backend |
| Oracle DB stopped | DB status is Stopped in OCI | OCI Console DB status | Autonomous DB not running | Start `projectluna-db` and wait for Available |
| Port 80 blocked | Local services work but public URL fails | `sudo iptables -L -n -v` | iptables does not allow TCP 80 | Add TCP 80 rule and save with netfilter-persistent |
| Frontend direct 3000 OK but public URL fail | `127.0.0.1:3000` works but public URL fails | `curl -I http://127.0.0.1:3000` and `curl -I http://127.0.0.1` | Nginx or firewall issue | Check Nginx config, restart Nginx, verify port 80 |
| Backend dependency import failure | backend process restarts or exits | `pm2 logs luna-backend --lines 100` | missing package, wrong venv, broken import | Activate `.venv`, install dependencies, run manual uvicorn test |
| Development backend restart loop | PM2 repeatedly restarts dev backend | `pm2 list` | `luna-backend-dev` restored or misconfigured | Delete or stop `luna-backend-dev`; do not include it as required production process |

## Post-Recovery Checklist

Before declaring the service recovered, confirm every item below.

- [ ] `http://168.107.9.177` is accessible
- [ ] `curl http://127.0.0.1:8000/health` returns `{"ok":true}`
- [ ] `curl http://127.0.0.1:8000/health/db` returns `{"ok":true,"status":"connected"}`
- [ ] `pm2 list` shows `luna-frontend` online
- [ ] `pm2 list` shows `luna-backend` online
- [ ] Nginx is active
- [ ] iptables allows TCP port 80
- [ ] Oracle DB `projectluna-db` is Available
- [ ] Analysis result page works

## Future Improvements

- document exact PM2 start commands
- document Nginx site configuration path
- add server reboot validation steps
- add uptime monitoring
- add alerting
- add HTTPS and certificate renewal procedure
- add DNS procedure if a domain is introduced
