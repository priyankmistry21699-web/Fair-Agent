# FAIR-Agent n8n Workflows

This directory contains n8n workflow JSON files for automating various aspects of the FAIR-Agent system.

## Available Workflows

### 1. Main Query Processing Workflow (`n8n-workflow-fair-agent.json`)
**Purpose**: Complete end-to-end query processing pipeline

**Features**:
- Webhook trigger for incoming queries
- Domain classification (Medical/Finance)
- Intelligent routing to appropriate agent
- FAIR metrics calculation
- Safety alert system
- Database persistence
- Response formatting

**Endpoints**:
- Webhook: `POST /webhook/fair-agent-query`
- Local FAIR-Agent API: `http://localhost:8000`
- Ollama: `http://localhost:11435`

**Flow**:
1. Receive query via webhook
2. Extract and validate query data
3. Classify domain (medical/finance)
4. Route to appropriate agent
5. Calculate FAIR metrics
6. Check safety thresholds
7. Save to database
8. Return formatted response

### 2. Batch Evaluation Workflow (`n8n-workflow-batch-evaluation.json`)
**Purpose**: Automated daily baseline evaluation and monitoring

**Features**:
- Scheduled daily execution (midnight)
- Runs baseline evaluation script
- Parses and analyzes results
- Threshold checking
- Email alerts for low scores
- Database logging

**Schedule**: Daily at 00:00 (customizable via cron expression)

**Alert Conditions**:
- Faithfulness < 50%
- Adaptability < 50%
- Safety < 50%

### 3. RAG Evidence Update Workflow (`n8n-workflow-evidence-update.json`)
**Purpose**: Weekly refresh of evidence sources and embeddings

**Features**:
- Fetches latest PubMed medical articles
- Retrieves updated finance resources
- Updates evidence database
- Clears embedding cache
- Rebuilds embeddings for improved RAG performance

**Schedule**: Weekly on Sunday at 02:00

**Sources**:
- PubMed API (medical evidence)
- GitHub API (finance resources)
- Custom evidence sources (configurable)

## Installation

### 1. Install n8n

```bash
# Via npm
npm install n8n -g

# Or via Docker
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

### 2. Start n8n

```bash
n8n start

# Or with Docker
docker-compose up -d
```

Access n8n at: `http://localhost:5678`

### 3. Import Workflows

1. Open n8n web interface
2. Click **Workflows** → **Import**
3. Select JSON files:
   - `n8n-workflow-fair-agent.json`
   - `n8n-workflow-batch-evaluation.json`
   - `n8n-workflow-evidence-update.json`
4. Activate workflows

## Configuration

### Prerequisites

Ensure the following services are running:

1. **FAIR-Agent Django Server**
   ```bash
   cd webapp
   python manage.py runserver
   ```

2. **Ollama Service**
   ```bash
   ollama serve
   ```

3. **PostgreSQL Database** (if using database nodes)

### Environment Variables

Create `.env` file in n8n directory:

```env
# FAIR-Agent Configuration
FAIR_AGENT_URL=http://localhost:8000
OLLAMA_URL=http://localhost:11435

# Email Alerts (for batch evaluation)
EMAIL_FROM=fair-agent@notifications.com
EMAIL_TO=admin@fairagent.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fair_agent_db
DB_USER=postgres
DB_PASSWORD=your-password
```

### Webhook URLs

After importing workflows, n8n will generate webhook URLs:

**Production URL**:
```
https://your-n8n-instance.com/webhook/fair-agent-query
```

**Test URL**:
```
http://localhost:5678/webhook-test/fair-agent-query
```

## Usage

### Testing Query Processing Workflow

```bash
# Send test query
curl -X POST http://localhost:5678/webhook/fair-agent-query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the symptoms of diabetes?",
    "domain": "medical",
    "user_id": "test_user"
  }'
```

### Manual Trigger Workflows

1. Open workflow in n8n editor
2. Click **Execute Workflow** button
3. View execution logs and results

### Monitoring

- View execution history: **Executions** tab
- Check logs: Click on individual executions
- Error tracking: Failed executions highlighted in red

## Customization

### Modify Schedules

Edit cron expressions in Schedule Trigger nodes:

```
0 0 * * *     # Daily at midnight
0 2 * * 0     # Weekly Sunday at 2 AM
*/15 * * * *  # Every 15 minutes
```

### Add Custom Nodes

1. Medical query preprocessing
2. Custom FAIR metric calculators
3. Additional evidence sources
4. Slack/Discord notifications
5. Advanced analytics

### API Endpoints to Add

Extend workflows with these FAIR-Agent endpoints:

- `/api/models/list/` - Available models
- `/api/query/history/` - Query history
- `/api/evaluation/detailed/` - Detailed metrics
- `/api/safety/check/` - Safety validation

## Troubleshooting

### Workflow Fails to Execute

1. Check FAIR-Agent server is running: `http://localhost:8000`
2. Verify Ollama service: `http://localhost:11435/api/tags`
3. Review node credentials
4. Check execution logs

### Webhook Not Receiving Requests

1. Verify webhook URL is correct
2. Check firewall settings
3. Enable webhook in workflow settings
4. Test with n8n test URL first

### Database Connection Errors

1. Verify PostgreSQL is running
2. Check credentials in n8n settings
3. Ensure database exists
4. Update connection parameters

## Performance Optimization

### For High-Volume Queries

1. Enable workflow queue mode
2. Increase n8n worker threads
3. Use Redis for queue management
4. Enable result caching

```bash
# Start n8n with queue mode
N8N_QUEUE_MODE=bull n8n start
```

### Memory Management

```bash
# Increase Node.js memory
NODE_OPTIONS="--max-old-space-size=4096" n8n start
```

## Integration Examples

### Slack Integration

Add Slack node to send notifications:
- Low safety scores
- Evaluation completions
- Error alerts

### Webhook to Multiple Services

Chain workflows:
1. FAIR-Agent processing
2. Save to database
3. Notify Slack
4. Log to analytics platform
5. Update dashboard

## Security

### Webhook Authentication

Add authentication to webhook nodes:

```javascript
// In Function node before processing
const authHeader = $node["Webhook Trigger"].json.headers.authorization;
const expectedToken = "your-secret-token";

if (authHeader !== `Bearer ${expectedToken}`) {
  throw new Error("Unauthorized");
}
```

### API Key Management

Store sensitive keys in n8n credentials:
- OpenAI API keys
- Database passwords
- Email credentials
- External API tokens

## Contributing

To add new workflows:

1. Create workflow in n8n editor
2. Test thoroughly
3. Export as JSON
4. Add to this repository
5. Update documentation

## License

MIT License - Same as FAIR-Agent project

## Support

For issues or questions:
- GitHub Issues: [Fair-Agent Repository]
- n8n Documentation: https://docs.n8n.io
- FAIR-Agent Docs: See main README.md
