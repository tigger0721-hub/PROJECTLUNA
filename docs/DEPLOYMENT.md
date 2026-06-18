# PROJECTLUNA Deployment Guide

## Purpose

This document describes the current production deployment architecture and recovery procedure for PROJECTLUNA.

The goal is to restore PROJECTLUNA quickly when the server, VM, networking, database, reverse proxy, or application process fails.

This document is based on the successful production recovery performed on 2026-06-18.

---

## 1. Current Architecture

PROJECTLUNA currently runs on Oracle Cloud Infrastructure.

### Production Components

- Oracle VM
- Existing PROJECT-LUNA Boot Volume
- Oracle Autonomous Database
- Nginx
- PM2
- FastAPI backend
- Next.js frontend

### Current Public IP

```text
168.107.9.177
```

### Runtime Flow

```text
User Browser
  -> Public IP:80
  -> Nginx
  -> Frontend (Next.js, PM2)
  -> Backend (FastAPI, PM2)
  -> Oracle Autonomous Database projectluna-db
```

---

## 2. Deployment Structure

## 2.1 Oracle VM

The application runs on an Oracle VM.

During the 2026-06-18 recovery, a new Oracle VM was created and the existing PROJECT-LUNA Boot Volume was attached.

The VM is responsible for:

- running frontend and backend processes
- running Nginx
- storing application deployment files from the attached boot volume
- exposing HTTP traffic through port 80

## 2.2 Oracle Autonomous Database

Database service:

```text
projectluna-db
```

The database must be started before validating database-dependent health checks.

Required validation:

```text
/health/db
```

## 2.3 Nginx

Nginx is used as the public reverse proxy.

Nginx must be active and listening behind port 80.

Check status:

```bash
sudo systemctl status nginx
```

Restart Nginx:

```bash
sudo systemctl restart nginx
```

Validate configuration:

```bash
sudo nginx -t
```

Reload configuration:

```bash
sudo systemctl reload nginx
```

## 2.4 PM2

PM2 manages the frontend and backend application processes.

Actual production PM2 process names:

```text
frontend
backend
```

Check PM2 processes:

```bash
pm2 list
```

Check logs:

```bash
pm2 logs
```

Restart frontend:

```bash
pm2 restart frontend
```

Restart backend:

```bash
pm2 restart backend
```

Restart all PROJECTLUNA processes:

```bash
pm2 restart frontend backend
```

Persist PM2 process list:

```bash
pm2 save
```

Enable PM2 startup after reboot:

```bash
pm2 startup
```

---

## 3. Frontend Runtime

The frontend is the user-facing PROJECTLUNA web application.

Expected runtime:

- Next.js
- managed by PM2
- proxied through Nginx

PM2 process name:

```text
frontend
```

Operational checks:

```bash
pm2 status frontend
pm2 logs frontend
```

Browser validation:

- Open the service URL in a browser
- Confirm the frontend page loads
- Confirm search/result flow can be reached

---

## 4. Backend Runtime

The backend is the PROJECTLUNA API service.

Expected runtime:

- FastAPI
- managed by PM2
- proxied through Nginx

PM2 process name:

```text
backend
```

Operational checks:

```bash
pm2 status backend
pm2 logs backend
```

The backend must pass both application and database health checks.

---

## 5. Health Checks

## 5.1 Backend Health

Endpoint:

```text
/health
```

Purpose:

- verifies backend application availability

Expected result:

```json
{
  "ok": true
}
```

Example:

```bash
curl http://localhost/health
```

If Nginx is routing to the backend health endpoint externally, also check:

```bash
curl http://168.107.9.177/health
```

## 5.2 Database Health

Endpoint:

```text
/health/db
```

Purpose:

- verifies backend to Oracle Autonomous Database connectivity

Expected result:

```json
{
  "ok": true
}
```

Example:

```bash
curl http://localhost/health/db
```

If Nginx is routing to the backend database health endpoint externally, also check:

```bash
curl http://168.107.9.177/health/db
```

---

## 6. Firewall and Port 80

PROJECTLUNA currently requires HTTP access through port 80.

During the 2026-06-18 recovery, iptables was updated to allow port 80 and the rule was saved.

Check iptables:

```bash
sudo iptables -L -n
```

Required:

```text
TCP 80 allowed
```

Save iptables rules after modification:

```bash
sudo iptables-save
```

If the server is unreachable from the browser, verify both:

- OCI network security rules
- VM-level iptables rules

---

## 7. Environment Variables

Environment variables must be preserved during server recovery.

Check the currently configured runtime environment before restarting services.

### Backend Environment Variables

Common backend variables include:

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

Database-related variables are required for `/health/db` to pass.

### Frontend Environment Variables

Common frontend variable:

```text
NEXT_PUBLIC_API_BASE
```

This value must point to the active backend API base URL when the frontend calls the backend directly or through configured proxy behavior.

---

## 8. Recovery History

## 8.1 Recovery on 2026-06-18

### Situation

PROJECTLUNA service was unavailable after a long development pause.

### Recovery Result

The service was successfully restored.

### Actions Performed

- Created a new Oracle VM
- Attached the existing PROJECT-LUNA Boot Volume
- Assigned new Public IP: `168.107.9.177`
- Started Oracle Autonomous Database `projectluna-db`
- Verified backend `/health`
- Verified backend `/health/db`
- Verified Nginx
- Verified frontend browser access
- Allowed port 80 through iptables
- Saved iptables configuration

### Validation Result

Successful validation:

- Oracle VM running
- Existing boot volume attached
- Oracle Autonomous Database running
- backend `/health` normal
- backend `/health/db` normal
- Nginx normal
- frontend accessible in browser
- iptables port 80 rule applied and saved

---

## 9. Recovery Procedure

Use this procedure when PROJECTLUNA becomes unavailable.

## Step 1. Confirm Failure Scope

Check from local machine:

```bash
curl http://168.107.9.177
curl http://168.107.9.177/health
curl http://168.107.9.177/health/db
```

Classify the failure:

- browser unavailable
- frontend unavailable
- backend unavailable
- database unavailable
- Nginx unavailable
- network/firewall unavailable

## Step 2. Verify Oracle VM

In OCI console:

- confirm VM exists
- confirm VM is running
- confirm public IP assignment
- confirm boot volume attachment

If the VM is unrecoverable:

1. create a new Oracle VM
2. attach the existing PROJECT-LUNA Boot Volume
3. assign a new Public IP
4. update any DNS or external references if needed

## Step 3. Start Oracle Autonomous Database

In OCI console:

- locate `projectluna-db`
- start the database if stopped
- wait until status becomes available

Then validate from the application server:

```bash
curl http://localhost/health/db
```

## Step 4. Verify PM2 Processes

SSH into the VM and run:

```bash
pm2 list
```

Required processes:

```text
frontend
backend
```

Restart if needed:

```bash
pm2 restart frontend backend
```

Check logs:

```bash
pm2 logs frontend
pm2 logs backend
```

Save PM2 process state:

```bash
pm2 save
```

## Step 5. Verify Backend Health

Run locally on the VM:

```bash
curl http://localhost/health
```

Expected:

```json
{
  "ok": true
}
```

Then verify database health:

```bash
curl http://localhost/health/db
```

Expected:

```json
{
  "ok": true
}
```

If `/health` fails:

- check PM2 backend logs
- check backend runtime errors
- check missing environment variables
- restart backend process

If `/health/db` fails:

- confirm `projectluna-db` is running
- check DB credentials
- check wallet configuration if used
- check backend logs

## Step 6. Verify Nginx

Check status:

```bash
sudo systemctl status nginx
```

Validate configuration:

```bash
sudo nginx -t
```

Restart if needed:

```bash
sudo systemctl restart nginx
```

## Step 7. Verify Port 80

Check iptables:

```bash
sudo iptables -L -n
```

Ensure TCP 80 is allowed.

If port 80 is not allowed, add the rule according to the server firewall policy and save it:

```bash
sudo iptables-save
```

Also verify OCI security rules allow inbound HTTP traffic.

## Step 8. Verify Frontend

Open the service in a browser:

```text
http://168.107.9.177
```

Validate:

- homepage loads
- analysis flow starts
- result page renders
- backend requests succeed

## Step 9. Final Validation Checklist

Before declaring recovery complete, confirm:

- Oracle VM is running
- Public IP is attached
- PROJECT-LUNA Boot Volume is attached
- Oracle Autonomous Database `projectluna-db` is running
- `pm2 list` shows `frontend` and `backend`
- `/health` returns ok
- `/health/db` returns ok
- Nginx is active
- port 80 is open
- iptables rules are saved
- frontend loads in browser

---

## 10. Common Failure Candidates

## 10.1 Oracle VM Failure

Symptoms:

- SSH unavailable
- public IP unreachable
- all services unavailable

Recovery:

- create new VM
- attach existing PROJECT-LUNA Boot Volume
- assign public IP
- verify PM2, Nginx, and firewall

## 10.2 Autonomous Database Stopped

Symptoms:

- `/health` passes
- `/health/db` fails
- backend logs show database connection errors

Recovery:

- start `projectluna-db`
- verify DB credentials and wallet settings
- restart backend if needed

## 10.3 PM2 Process Down

Symptoms:

- Nginx running
- process-specific route fails
- PM2 status shows stopped or errored process

Recovery:

```bash
pm2 restart frontend backend
pm2 save
```

## 10.4 Nginx Failure

Symptoms:

- PM2 processes running
- localhost health checks pass
- browser access fails

Recovery:

```bash
sudo nginx -t
sudo systemctl restart nginx
```

## 10.5 Firewall Failure

Symptoms:

- services run locally
- browser access fails externally
- public IP does not respond on port 80

Recovery:

- verify OCI security rules
- verify iptables
- allow TCP 80
- save iptables rules

---

## 11. Operations Checklist

Use this quick checklist after reboot or recovery:

```bash
pm2 list
pm2 status frontend
pm2 status backend
curl http://localhost/health
curl http://localhost/health/db
sudo systemctl status nginx
sudo iptables -L -n
```

Browser check:

```text
http://168.107.9.177
```

---

## 12. Future Improvements

Recommended improvements:

- document exact application directory paths
- document exact PM2 start commands
- document Nginx site configuration path
- add automated uptime monitoring
- add deployment automation
- add backup and restore checklist
- add DNS management notes if domain is introduced
- add HTTPS setup with certificate renewal procedure

---

## Last Updated

2026-06-18 KST

## Owner

PROJECTLUNA
