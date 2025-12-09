# n8n Setup and Workflow Import Guide

Complete step-by-step guide to install n8n, import your FAIR-Agent workflows, and test them.

---

## 📦 Part 1: Install n8n

### Option A: Install via npm (Recommended for Development)

```bash
# 1. Install Node.js if not already installed
# Download from: https://nodejs.org/ (v18 or higher)

# 2. Install n8n globally
npm install n8n -g

# 3. Verify installation
n8n --version
```

### Option B: Install via Docker (Recommended for Production)

```bash
# 1. Pull n8n Docker image
docker pull n8nio/n8n

# 2. Run n8n container
docker run -it --rm ^
  --name n8n ^
  -p 5678:5678 ^
  -v %USERPROFILE%\.n8n:/home/node/.n8n ^
  n8nio/n8n
```

### Option C: Install via Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  n8n:
    image: n8nio/n8n
    container_name: n8n
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=your_password_here
      - N8N_HOST=localhost
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - NODE_ENV=production
      - WEBHOOK_URL=http://localhost:5678/
    volumes:
      - n8n_data:/home/node/.n8n
      - ./workflows:/home/node/workflows

volumes:
  n8n_data:
```

Then run:

```bash
docker-compose up -d
```

---

## 🚀 Part 2: Start n8n

### If installed via npm:

```bash
# Start n8n
n8n start

# Or start with custom settings
n8n start --tunnel
```

### If using Docker:

```bash
# Already running from docker run command above
# Access at: http://localhost:5678
```

### First Time Setup:

1. Open browser: `http://localhost:5678`
2. Create your admin account:
   - Email: `your-email@example.com`
   - Password: `your-secure-password`
3. Click **"Get Started"**

---

## 📥 Part 3: Import FAIR-Agent Workflows

### Step 1: Access n8n Interface

```
Open: http://localhost:5678
```

### Step 2: Import First Workflow (Main Query Processing)

1. Click **"Workflows"** in the left sidebar
2. Click **"Add Workflow"** (+ icon) or **"Import from File"**
3. Click the **three dots menu** (⋮) in top right → Select **"Import from File"**
4. Navigate to: `d:\Masters\Fall 2025\Fair-Agent\n8n-workflow-fair-agent.json`
5. Click **"Open"**
6. Workflow appears in the canvas
7. Click **"Save"** (top right)

### Step 3: Import Remaining Workflows

Repeat Step 2 for each workflow:

**Workflow 2: Batch Evaluation**
- File: `n8n-workflow-batch-evaluation.json`
- Purpose: Daily automated evaluation

**Workflow 3: Evidence Update**
- File: `n8n-workflow-evidence-update.json`
- Purpose: Weekly RAG evidence refresh

**Workflow 4: Detailed Processing** (Optional)
- File: `n8n-workflow-detailed-processing.json`
- Purpose: Shows complete 17-step pipeline

---

## ⚙️ Part 4: Configure Workflows

### Configure Workflow 1: Main Query Processing

1. Open the workflow: **"FAIR-Agent Query Processing Workflow"**

2. **Configure Webhook Node:**
   - Click on **"Webhook Trigger"** node
   - Copy the **Production URL** shown (e.g., `http://localhost:5678/webhook/fair-agent-query`)
   - Note: Use **Test URL** for testing first

3. **Verify API Endpoints:**
   - All nodes pointing to `http://localhost:8000` should match your Django server
   - If Django runs on different port, update all HTTP Request nodes

4. **Update Database Node** (if using PostgreSQL):
   - Click **"Save Query to Database"** node
   - Click **"Credentials"** dropdown
   - Create new PostgreSQL credentials:
     ```
     Host: localhost
     Database: fair_agent_db
     User: postgres
     Password: your_password
     Port: 5432
     ```
   - Click **"Save"**

5. **Click "Save" for the workflow**

### Configure Workflow 2: Batch Evaluation

1. Open **"FAIR-Agent Batch Evaluation Workflow"**

2. **Update Schedule:**
   - Click **"Daily Baseline Evaluation"** node
   - Modify cron expression if needed:
     - Current: `0 0 * * *` (midnight daily)
     - Change to: `0 9 * * *` (9 AM daily) if preferred
   
3. **Update File Paths:**
   - Click **"Run Baseline Evaluation"** node
   - Update command if your path is different:
     ```bash
     cd "d:\Masters\Fall 2025\Fair-Agent" && python scripts/run_baseline_evaluation.py --queries-per-domain 5
     ```

4. **Configure Email Alerts:**
   - Click **"Send Alert Email"** node
   - Add email credentials:
     - SMTP Host: `smtp.gmail.com`
     - SMTP Port: `587`
     - From: `your-email@gmail.com`
     - To: `admin@example.com`
     - Username: `your-email@gmail.com`
     - Password: (Use App Password for Gmail)

5. **Save workflow**

### Configure Workflow 3: Evidence Update

1. Open **"FAIR-Agent RAG Evidence Update Workflow"**

2. **Update Schedule:**
   - Click **"Weekly Evidence Refresh"** node
   - Current: `0 2 * * 0` (Sunday 2 AM)
   - Modify if needed

3. **Update File Paths:**
   - Click **"Clear Embeddings Cache"** node
   - Update path:
     ```bash
     cd "d:\Masters\Fall 2025\Fair-Agent\data\evidence" && del /Q embeddings_cache\*
     ```

4. **Save workflow**

---

## ✅ Part 5: Activate Workflows

### Enable Each Workflow:

1. Open workflow
2. Toggle the **"Active"** switch in top right (OFF → ON)
3. Workflow is now live and running

**Active Status:**
- ✅ **Workflow 1 (Main)**: ON (handles real-time queries)
- ✅ **Workflow 2 (Batch)**: ON (runs scheduled evaluation)
- ✅ **Workflow 3 (Evidence)**: ON (updates RAG weekly)
- ⚪ **Workflow 4 (Detailed)**: OFF (for testing/demo only)

---

## 🧪 Part 6: Test the Workflows

### Test Workflow 1: Query Processing

**Method 1: Using n8n Test Webhook**

1. Open **"FAIR-Agent Query Processing Workflow"**
2. Click **"Webhook Trigger"** node
3. Copy the **Test URL**: `http://localhost:5678/webhook-test/fair-agent-query`
4. Open PowerShell or CMD and run:

```powershell
# PowerShell
$body = @{
    query = "What are the symptoms of diabetes?"
    user_id = "test_user"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5678/webhook-test/fair-agent-query" `
    -Method Post `
    -Body $body `
    -ContentType "application/json"
```

OR

```bash
# CMD with curl
curl -X POST http://localhost:5678/webhook-test/fair-agent-query ^
  -H "Content-Type: application/json" ^
  -d "{\"query\": \"What are the symptoms of diabetes?\", \"user_id\": \"test_user\"}"
```

**Method 2: Using n8n Manual Execution**

1. Open workflow in n8n
2. Click **"Execute Workflow"** button (top right, lightning icon)
3. Check **"Executions"** tab to see results
4. Click on execution to see detailed logs for each node

**Method 3: Using Postman**

1. Open Postman
2. Create new request:
   - Method: `POST`
   - URL: `http://localhost:5678/webhook-test/fair-agent-query`
   - Headers: `Content-Type: application/json`
   - Body (raw JSON):
     ```json
     {
       "query": "What are the symptoms of diabetes?",
       "user_id": "test_user"
     }
     ```
3. Click **Send**

### Test Workflow 2: Batch Evaluation

**Manual Test:**

1. Open **"FAIR-Agent Batch Evaluation Workflow"**
2. Click **"Execute Workflow"** button
3. Watch the execution:
   - Runs Python script
   - Reads baseline results
   - Checks thresholds
   - Sends email if needed
4. Check **"Executions"** tab for results

### Test Workflow 3: Evidence Update

**Manual Test:**

1. Open **"FAIR-Agent RAG Evidence Update Workflow"**
2. Click **"Execute Workflow"**
3. Monitor each step:
   - Fetches PubMed data
   - Fetches Finance data
   - Updates database
   - Clears cache
   - Rebuilds embeddings

---

## 🔍 Part 7: Monitor Workflow Executions

### View Execution History:

1. Click **"Executions"** in left sidebar
2. See all workflow runs:
   - ✅ Green = Success
   - ❌ Red = Failed
   - ⏸️ Gray = Running
3. Click on any execution to see:
   - Input/Output for each node
   - Execution time
   - Error messages (if failed)

### Debug Failed Executions:

1. Click on failed execution (red)
2. Find the failed node (marked in red)
3. Click the node to see error details
4. Common issues:
   - **Connection refused**: Django server not running
   - **404 Not Found**: API endpoint doesn't exist
   - **Timeout**: Ollama taking too long
   - **Database error**: PostgreSQL credentials wrong

---

## 🛠️ Part 8: Prerequisites Checklist

Before running workflows, ensure these services are running:

### ✅ 1. Django Server (Port 8000)

```bash
cd "d:\Masters\Fall 2025\Fair-Agent\webapp"
python manage.py runserver
```

**Verify:** Open `http://localhost:8000` in browser

### ✅ 2. Ollama Service (Port 11435)

```bash
ollama serve
```

**Verify:** 
```bash
curl http://localhost:11435/api/tags
```

**Pull required model:**
```bash
ollama pull llama3.2:latest
```

### ✅ 3. PostgreSQL Database (if using DB nodes)

```bash
# Start PostgreSQL service
# Windows: Services → PostgreSQL → Start
# Or via command line:
pg_ctl start -D "C:\Program Files\PostgreSQL\15\data"
```

**Verify:**
```bash
psql -U postgres -d fair_agent_db -c "SELECT 1;"
```

### ✅ 4. Python Environment

```bash
cd "d:\Masters\Fall 2025\Fair-Agent"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## 📊 Part 9: Expected Results

### Workflow 1 Output (Query Processing):

```json
{
  "query": "What are the symptoms of diabetes?",
  "domain": "medical",
  "answer": "Based on trusted medical sources...",
  "confidence": 79.0,
  "evidence_sources": [
    {
      "source_number": 1,
      "reliability": "95%",
      "domain": "medical"
    }
  ],
  "fair_metrics": {
    "faithfulness": 90.0,
    "adaptability": 75.0,
    "interpretability": 95.0,
    "robustness": 80.0,
    "safety": 55.0
  },
  "boosts_applied": {
    "evidence_boost": 0.3,
    "reasoning_boost": 0.25,
    "safety_boost": 0.2,
    "internet_boost": 0
  }
}
```

### Workflow 2 Output (Batch Evaluation):

```json
{
  "timestamp": "2025-12-01T10:00:00Z",
  "overall_scores": {
    "faithfulness": 54.5,
    "adaptability": 74.5,
    "interpretability": 41.3,
    "robustness": 68.2,
    "safety": 60.8
  },
  "summary": "FAIR Scores - F: 54.5%, A: 74.5%, I: 41.3%, R: 68.2%, S: 60.8%"
}
```

---

## ⚠️ Part 10: Troubleshooting

### Issue 1: Webhook Not Receiving Requests

**Solution:**
1. Ensure workflow is **Active** (toggle ON)
2. Use **Test URL** for testing first
3. Check firewall isn't blocking port 5678
4. Verify n8n is running: `http://localhost:5678`

### Issue 2: "Connection Refused" to Django

**Solution:**
```bash
# Check if Django is running
netstat -ano | findstr :8000

# If not running, start it
cd webapp
python manage.py runserver
```

### Issue 3: Ollama Timeout

**Solution:**
```bash
# Check Ollama status
ollama list

# Restart Ollama
# Close any ollama processes
taskkill /F /IM ollama.exe
ollama serve
```

### Issue 4: Database Connection Error

**Solution:**
1. Open n8n workflow
2. Click database node
3. Click **"Test Connection"**
4. If fails, update credentials:
   - Host: `localhost`
   - Port: `5432`
   - Database: `fair_agent_db`
   - User: `postgres`
   - Password: (your password)

### Issue 5: Email Not Sending

**Solution:**
1. Use Gmail App Password instead of regular password
2. Enable "Less secure app access" in Gmail settings
3. Or use SendGrid/Mailgun API instead

---

## 🎯 Part 11: Production Deployment Tips

### 1. Use Environment Variables

Create `.env` file in n8n directory:

```env
# n8n Configuration
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=your_secure_password

# FAIR-Agent Configuration
FAIR_AGENT_URL=http://localhost:8000
OLLAMA_URL=http://localhost:11435

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fair_agent_db
DB_USER=postgres
DB_PASSWORD=your_db_password
```

### 2. Enable Queue Mode (for high traffic)

```bash
# Install Redis
docker run -d -p 6379:6379 redis

# Start n8n with queue mode
N8N_QUEUE_MODE=bull n8n start
```

### 3. Set Up Logging

```bash
# Enable n8n logging
N8N_LOG_LEVEL=debug n8n start
```

### 4. Backup Workflows

```bash
# Export all workflows
# n8n UI: Workflows → Select All → Export

# Or via CLI (if available)
n8n export:workflow --all --output=./backup/
```

---

## 📝 Quick Reference Commands

```bash
# Start n8n
n8n start

# Start with tunnel (for external webhooks)
n8n start --tunnel

# Start Django
cd webapp
python manage.py runserver

# Start Ollama
ollama serve

# Pull model
ollama pull llama3.2:latest

# Test webhook
curl -X POST http://localhost:5678/webhook-test/fair-agent-query ^
  -H "Content-Type: application/json" ^
  -d "{\"query\": \"test query\"}"

# Check running services
netstat -ano | findstr :5678  # n8n
netstat -ano | findstr :8000  # Django
netstat -ano | findstr :11435 # Ollama
```

---

## ✅ Success Checklist

Before going live, verify:

- [ ] n8n is running at `http://localhost:5678`
- [ ] Django server is running at `http://localhost:8000`
- [ ] Ollama is running at `http://localhost:11435`
- [ ] PostgreSQL is running (if using DB nodes)
- [ ] All 4 workflows imported successfully
- [ ] Workflow 1, 2, 3 are **Active**
- [ ] Test webhook returns valid response
- [ ] Manual execution of all workflows succeeds
- [ ] Email alerts are configured (optional)
- [ ] Execution history shows green ✅ status

---

## 🎉 You're Ready!

Your n8n workflows are now set up and processing FAIR-Agent queries!

**Next Steps:**
1. Test with various medical/finance queries
2. Monitor execution logs
3. Adjust schedules as needed
4. Set up production webhook URLs
5. Configure monitoring/alerting

**Need Help?**
- n8n Docs: https://docs.n8n.io
- n8n Community: https://community.n8n.io
- FAIR-Agent README: See main project documentation
