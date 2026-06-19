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

## PM2 Process Recreation

Use this section only when production PM2 processes are missing from `pm2 list`.

Recreate backend:

```bash
cd /home/ubuntu/stock-chart-tutor/backend
pm2 start "bash -lc 'source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000'" --name luna-backend
```

Recreate frontend:

```bash
cd /home/ubuntu/stock-chart-tutor/frontend
pm2 start "npm run start" --name luna-frontend
```

Save PM2 process list:

```bash
pm2 save
```

Do not recreate `luna-backend-dev` as a required production process.

## Recovery Procedure

### Step 1. Oracle VM

Check command:

```text
OCI Console -> Compute -> Instances
```

Normal criteria:

- Oracle VM exists
- VM state is Running

Failure action:

- Create a new Oracle VM
- Attach the existing PROJECT-LUNA Boot Volume
- Assign a public IP

### Step 2. Boot Volume

Check command:

```text
OCI Console -> Compute -> Boot Volumes
```

Normal criteria:

- PROJECT-LUNA Boot Volume exists
- Boot Volume is attached to the active VM

Failure action:

- Attach PROJECT-LUNA Boot Volume to the active VM
- Boot from the attached volume
- Verify production directory after SSH login

### Step 3. SSH

Check command:

```bash
ssh ubuntu@168.107.9.177
```

Normal criteria:

- SSH login succeeds as `ubuntu`

Failure action:

- Verify VM state
- Verify public IP
- Verify SSH security rule
- Verify SSH key

### Step 4. Oracle Autonomous Database

Check command:

```text
OCI Console -> Oracle Autonomous Database -> projectluna-db
```

Normal criteria:

```text
Available
```

Failure action:

- Start `projectluna-db`
- Wait until status is Available
- Restart `luna-backend` if DB health does not recover

### Step 5. PM2 Processes

Check command:

```bash
pm2 list
```

Normal criteria:

- `luna-frontend` is online
- `luna-backend` is online

Failure action:

```bash
pm2 restart luna-frontend luna-backend
pm2 resurrect
```

If processes are missing, use `PM2 Process Recreation`.

### Step 6. Backend Health

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

### Step 7. DB Health

Check command:

```bash
curl http://127.0.0.1:8000/health/db
```

Normal criteria:

```json
{"ok":true,"status":"connected"}
```

Failure action:

- Confirm `projectluna-db` is Available
- Verify wallet directory `/home/ubuntu/stock-chart-tutor/backend/wallet`
- Verify DB environment variables
- Restart `luna-backend`

### Step 8. Nginx

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

### Step 9. Firewall

Check command:

```bash
sudo iptables -L -n -v
```

Normal criteria:

- TCP port 80 is allowed

Failure action:

```bash
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo apt install -y iptables-persistent
sudo netfilter-persistent save
sudo netfilter-persistent reload
sudo iptables -L -n -v
```

### Step 10. Browser

Check command:

```text
http://168.107.9.177
```

Normal criteria:

- Frontend loads
- Analysis result page works

Failure action:

```bash
curl -I http://127.0.0.1
curl -I http://127.0.0.1:3000
curl http://127.0.0.1:8000/health
```

## Recovery History: 2026-06-18

### Date

2026-06-18 KST

### Impact

- Public service URL was unavailable
- Frontend browser access failed
- PROJECTLUNA could not be used externally

### Root Cause

- Oracle VM instance was not listed in OCI
- Only PROJECT-LUNA Boot Volume remained
- Oracle Autonomous Database `projectluna-db` was Stopped
- Server internals became healthy after VM recovery
- Public access was blocked by iptables until TCP port 80 was allowed

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
10. Installed and used persistent iptables saving

### Validation Evidence

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/health/db
curl -I http://127.0.0.1
curl -I http://127.0.0.1:3000
```

Public browser:

```text
http://168.107.9.177
```

### Remaining Risks

- Public IP may change if VM is recreated
- PM2 process list must be saved after process recreation
- Firewall persistence must be verified after reboot
- Monitoring and alerting are not automated

### Prevention and Follow-up

- Keep this runbook updated
- Add uptime monitoring
- Add HTTPS and DNS documentation
- Document future PM2 and Nginx changes

### Related PR

- #80

## Failure Scenario Table

| Case | Symptom | Check command | Possible cause | Action |
|---|---|---|---|---|
| Public URL unavailable | Browser cannot open service | `curl -I http://168.107.9.177` | VM down, Nginx down, port 80 blocked, OCI rule missing | Check VM, Nginx, iptables, OCI security rules |
| Nginx 502 or 504 | Gateway error | `sudo systemctl status nginx` | Frontend or backend upstream down | Restart PM2 processes and reload Nginx |
| PM2 process stopped | PM2 shows stopped or errored | `pm2 list` | Crash, missing env, manual stop | Restart or recreate `luna-frontend` and `luna-backend` |
| Backend health fails | `/health` is not OK | `curl http://127.0.0.1:8000/health` | Backend down, import error, venv issue | Check backend logs and restart backend |
| DB health fails | `/health/db` is not connected | `curl http://127.0.0.1:8000/health/db` | DB stopped, wallet error, DB env error | Start DB, verify wallet and env, restart backend |
| Oracle DB stopped | DB is Stopped in OCI | OCI DB status | Autonomous DB stopped | Start `projectluna-db` |
| Port 80 blocked | Local checks pass but public URL fails | `sudo iptables -L -n -v` | iptables blocks TCP 80 | Add TCP 80 rule and save persistently |
| Frontend direct 3000 OK but public URL fails | Port 3000 works but browser fails | `curl -I http://127.0.0.1:3000` | Nginx or firewall issue | Check Nginx config and port 80 |
| Backend dependency import failure | Backend exits or restarts | `pm2 logs luna-backend --lines 100` | Missing package, wrong venv, broken import | Activate venv and run manual uvicorn test |
| Development backend restart loop | Dev backend repeatedly restarts | `pm2 list` | `luna-backend-dev` restored | Stop or delete `luna-backend-dev` |

## Post-recovery Checklist

- [ ] `http://168.107.9.177` is accessible
- [ ] `curl http://127.0.0.1:8000/health` returns `{"ok":true}`
- [ ] `curl http://127.0.0.1:8000/health/db` returns `{"ok":true,"status":"connected"}`
- [ ] `pm2 list` shows `luna-frontend` online
- [ ] `pm2 list` shows `luna-backend` online
- [ ] Nginx is active
- [ ] iptables allows TCP port 80
- [ ] Oracle DB `projectluna-db` is Available
- [ ] Analysis result page works
