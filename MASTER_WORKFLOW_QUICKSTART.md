# 🚀 Quick Start Guide: Master All-in-One Workflow

## ✅ Fixed Issues:
1. ✅ Connected local evidence nodes to database update
2. ✅ Fixed Ollama port: 11435 → 11434
3. ✅ Removed external API dependencies (PubMed, GitHub)

---

## 📋 Prerequisites (Start These First!)

### 1. Start Ollama
```cmd
ollama serve
```
**Wait until you see:** "Ollama is running on http://localhost:11434"

### 2. Verify Ollama has the model
```cmd
ollama list
```
**Should show:** `llama3.2:latest`

If not, pull it:
```cmd
ollama pull llama3.2:latest
```

### 3. Start Django
```cmd
cd "d:\Masters\Fall 2025\Fair-Agent\webapp"
python manage.py runserver
```
**Wait until you see:** "Starting development server at http://127.0.0.1:8000/"

---

## 🔧 Import & Setup Workflow

### Step 1: Import Updated Workflow
1. **Delete old workflow** in n8n (if exists)
2. Import fresh: `n8n-workflow-master-all-in-one.json`
3. Click **Save**

### Step 2: Verify Connections
In n8n, check these nodes are connected:

**Evidence Update Chain:**
```
Schedule: Weekly Evidence Update
  ├─> 1a. Use Local Medical Evidence ─┐
  └─> 1b. Use Local Finance Evidence ─┴─> 1c. Update Evidence Database
                                           └─> 1d. Clear Embeddings Cache
                                                └─> 1e. Rebuild Embeddings
```

**Query Processing Chain:**
```
Webhook: Receive Query
  └─> 3a. Classify Domain
       └─> 3b. Generate Baseline (Ollama)
            └─> 3c. Retrieve Evidence (RAG)
                 └─> 3d. Complete Processing
                      └─> 3e. Send Response
```

### Step 3: Activate Workflow
Toggle **"Active"** switch (should turn green)

---

## 🧪 Testing

### Test 1: Check Ollama Connection
```powershell
curl http://localhost:11434/api/tags
```
**Expected:** JSON response with models list

### Test 2: Check Django Connection
```powershell
curl http://localhost:8000/api/health/
```
**Expected:** `{"status": "ok"}` or similar

### Test 3: Test Query Processing
```powershell
curl -X POST http://localhost:5678/webhook/fair-agent-query `
  -H "Content-Type: application/json" `
  -d '{\"query\": \"What are symptoms of diabetes?\", \"user_id\": \"test\"}'
```

**Expected Response:**
```json
{
  "query": "What are symptoms of diabetes?",
  "domain": "medical",
  "answer": "...",
  "confidence": 0.85,
  "fair_scores": {
    "faithfulness": 87.5,
    "adaptability": 75.0,
    ...
  }
}
```

---

## 🐛 Troubleshooting

### Error: "ECONNREFUSED ::1:11435"
**Cause:** Ollama not running OR wrong port
**Fix:**
1. Start Ollama: `ollama serve`
2. Verify it's on port **11434** (not 11435)
3. Re-import updated workflow

### Error: "ENOTFOUND api.pubmed.ncbi.nlm.nih.gov"
**Cause:** Old workflow with external APIs
**Fix:** Use the updated `n8n-workflow-master-all-in-one.json` (now uses local evidence)

### Error: Nodes not connected
**Cause:** Broken connections in JSON
**Fix:** Re-import the updated workflow (connections are now fixed)

### Error: Django endpoint 404
**Fix:** Update URLs in these nodes:
- `1c. Update Evidence Database` → Change to your actual endpoint
- `2d. Log to Database` → Change to your actual endpoint
- `3c. Retrieve Evidence (RAG)` → `http://localhost:8000/api/evidence/retrieve/`
- `3d. Complete Processing` → `http://localhost:8000/api/query/process-complete/`

---

## 📊 Running Each Section

### Section 1: Evidence Update (Run Once)
1. Find node: **"Schedule: Weekly Evidence Update"**
2. Click **"Execute Node"**
3. Watch the execution flow through all 5 steps
4. Should complete in ~30 seconds

### Section 2: Baseline Evaluation (Daily)
1. Find node: **"Schedule: Daily Evaluation"**
2. Click **"Execute Node"**
3. Wait ~2-5 minutes (runs Python script)
4. Check `results/baseline_scores.json` for output

### Section 3: Query Processing (Always Active)
- Automatically active once workflow is enabled
- Listens on webhook URL
- Test with curl command above

---

## ✅ Success Checklist

- [ ] Ollama running on port 11434
- [ ] Django running on port 8000
- [ ] n8n running on port 5678
- [ ] Workflow imported and **Active**
- [ ] Evidence update completed successfully
- [ ] Query test returns valid JSON response
- [ ] Baseline evaluation completes without errors

---

## 🎯 What's Next?

1. **Test with various queries:**
   - Medical: "What is hypertension?"
   - Finance: "What is a bull market?"
   - Cross-domain: "How does stress affect financial decisions?"

2. **Monitor executions:**
   - Click **"Executions"** in n8n to see history
   - Check for errors in failed runs

3. **Schedule automatic runs:**
   - Evidence Update: Weekly (Sundays 2 AM)
   - Baseline Eval: Daily (Midnight)

---

## 📞 Quick Reference

| Service | URL | Check Command |
|---------|-----|---------------|
| Ollama | http://localhost:11434 | `curl http://localhost:11434/api/tags` |
| Django | http://localhost:8000 | `curl http://localhost:8000/` |
| n8n | http://localhost:5678 | Open in browser |
| Webhook | http://localhost:5678/webhook/fair-agent-query | Test with curl |

---

**Everything should work now!** 🎉

Re-import the workflow and start Ollama before testing.
