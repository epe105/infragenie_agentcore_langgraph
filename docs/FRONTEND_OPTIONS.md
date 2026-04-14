# Frontend Options for InfraGenie Demos

This guide explains different ways to run InfraGenie demos with a professional UI instead of the command line.

## 🎯 Quick Answer

**Can you run through AgentCore Sandbox?**

AWS Bedrock AgentCore **does not** currently have a built-in web UI or "test sandbox" interface that supports:
- Multi-step workflows with state
- Human approval gates
- Interactive prompts

However, you have several excellent options below that provide professional frontends for customer demos.

---

## Option 1: Streamlit UI (Recommended) ⭐

**Best for:** Customer demos, live presentations, professional appearance

### Features
- ✅ Clean, modern web interface
- ✅ Step-by-step workflow visualization
- ✅ Interactive approval buttons
- ✅ Real-time status updates
- ✅ Mobile-responsive design
- ✅ Easy to customize branding

### Setup & Run

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Install UI dependencies
pip install -r requirements.txt

# 3. Run Streamlit app
streamlit run ui/streamlit_demo.py

# The app will open automatically at http://localhost:8501
```

### Features Demo Flow

1. **Landing Page** - Select demo type (Infrastructure/Security/Custom)
2. **Plan Creation** - View AI-generated execution plan
3. **Plan Approval** - Approve/Deny with clear buttons
4. **Execution** - Real-time workflow execution
5. **Remediation Approval** - Review and approve security fixes
6. **Results** - View final outcomes with formatted output

### Customization

Edit `streamlit_demo.py` to:
- Change colors/branding (CSS in markdown)
- Add company logo
- Modify approval workflows
- Add analytics tracking

### Share with Remote Team

```bash
# Option 1: Use Streamlit Cloud (free)
streamlit run ui/streamlit_demo.py --server.address 0.0.0.0

# Option 2: Use ngrok for external access
# Install: brew install ngrok
ngrok http 8501
# Share the ngrok URL with customers
```

---

## Option 2: Gradio UI

**Best for:** Quick demos, ML-focused audiences, simple deployment

### Features
- ✅ Automatic API generation
- ✅ Built-in sharing capabilities
- ✅ Tab-based interface
- ✅ Easy to deploy
- ✅ Good for technical audiences

### Setup & Run

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Install UI dependencies (if not already done)
pip install -r requirements.txt

# 3. Run Gradio app
python ui/gradio_demo.py

# App opens at http://localhost:7860
```

### Share Publicly

```bash
# Run with sharing enabled (creates temporary public URL)
python ui/gradio_demo.py --share

# You'll get a URL like: https://xxxxx.gradio.live
# Share this URL with customers (valid for 72 hours)
```

---

## Option 3: LangGraph Studio

**Best for:** Development, debugging, workflow visualization

### What is LangGraph Studio?

A desktop application that provides visual debugging and interaction with LangGraph workflows.

### Features
- ✅ Visual graph display
- ✅ State inspection
- ✅ Time-travel debugging
- ✅ Thread management
- ✅ Checkpoint viewing

### Limitations for Your Use Case

❌ **Not ideal for customer demos:**
- Desktop application (not web-based)
- Requires LangGraph Cloud or local server setup
- More technical/development-focused
- Doesn't integrate well with deployed AgentCore agents

### Setup (if you want to try)

```bash
# Install LangGraph CLI
pip install langgraph-cli

# Create langgraph.json config
cat > langgraph.json << EOF
{
  "graphs": {
    "infrastructure": "./src/infrastructure_lifecycle_demo.py:graph",
    "security": "./src/security_demo.py:graph"
  },
  "env": ".env"
}
EOF

# Launch Studio
langgraph dev
```

**Note:** This would require refactoring your AgentCore integration to work with LangGraph Studio's local server mode.

---

## Option 4: Custom React/Next.js Frontend

**Best for:** Production deployment, custom branding, enterprise customers

### When to Choose This

- Need custom branding/UI
- Enterprise deployment
- Want mobile app compatibility
- Need advanced features (user auth, logging, etc.)

### Architecture

```
┌─────────────┐
│  React UI   │
│  (Browser)  │
└──────┬──────┘
       │ HTTP/WebSocket
       │
┌──────▼──────────────┐
│  FastAPI Backend    │
│  (Python)           │
└──────┬──────────────┘
       │
┌──────▼──────────────┐
│  AgentCore Invoke   │
│  (Your Agent)       │
└─────────────────────┘
```

### Example Backend (FastAPI)

```python
# api.py
from fastapi import FastAPI, WebSocket
import subprocess
import json

app = FastAPI()

@app.post("/api/create-plan")
async def create_plan(request: dict):
    prompt = request.get("prompt")
    # Call agentcore invoke...
    return {"plan": result}

@app.post("/api/execute")
async def execute(request: dict):
    # Execute workflow...
    return {"status": "running"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Real-time updates
    pass
```

**Effort:** High (1-2 weeks development)
**Cost:** Development time
**Benefits:** Full control, production-ready

---

## Comparison Table

| Feature | Streamlit | Gradio | LangGraph Studio | Custom React |
|---------|-----------|--------|------------------|--------------|
| **Setup Time** | 5 min | 5 min | 30 min | 2 weeks |
| **Professional Look** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Customer Demo** | ✅ Excellent | ✅ Good | ❌ Dev tool | ✅ Excellent |
| **Easy Sharing** | ✅ Yes | ✅ Yes | ❌ Desktop | ✅ Yes |
| **Customization** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Mobile Support** | ✅ Yes | ✅ Yes | ❌ No | ✅ Yes |
| **Production Ready** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ❌ No | ⭐⭐⭐⭐⭐ |

---

## Recommended Approach for Your Use Case

### For Customer Demos: **Use Streamlit** ✅

```bash
# Quick start
source .venv/bin/activate
pip install -r requirements.txt
streamlit run ui/streamlit_demo.py
```

**Why Streamlit?**
1. **Professional appearance** - Customers will be impressed
2. **Easy to follow** - Clear step-by-step flow
3. **Interactive** - Click buttons instead of typing yes/no
4. **Real-time updates** - Shows progress visually
5. **Easy sharing** - One command to share externally
6. **No command line confusion** - Everything in the browser

### Workflow in Streamlit

```
Customer sees:
1. Landing page with 3 big buttons:
   [Infrastructure Lifecycle] [Security Scan] [Custom Prompt]

2. Plan creation screen:
   "⏳ Creating plan..."
   Shows formatted plan in a nice box

3. Approval screen:
   Plan details in formatted markdown
   [✅ Approve & Execute] [❌ Deny]

4. Execution screen:
   "⏳ Running workflow..."
   Shows agent progress

5. Remediation approval:
   Risk score, compliance frameworks
   [✅ Approve Remediation] [❌ Deny]

6. Results screen:
   Final summary with insights
   [🔄 Run Another Demo]
```

---

## About AgentCore "Sandbox"

**Common Misconception:** AWS Bedrock AgentCore has a "test sandbox" UI

**Reality:**
- AgentCore provides CLI tools (`agentcore invoke`)
- No built-in web UI for testing agents
- AWS Console shows agent status but can't run interactive workflows
- Your agents run as deployed services, not in an interactive sandbox

**What AWS Provides:**
- ✅ CLI for invoking agents
- ✅ CloudWatch logs for debugging
- ✅ Console for deployment status
- ❌ No interactive web UI
- ❌ No built-in approval gates UI
- ❌ No conversation interface

**This is why custom UIs (like Streamlit) are necessary for demos!**

---

## Deployment Options

### Local (Your Laptop)
```bash
streamlit run ui/streamlit_demo.py
# Share screen during Zoom/Teams call
```

### Cloud VM (AWS EC2)
```bash
# On EC2 instance
streamlit run ui/streamlit_demo.py --server.address 0.0.0.0 --server.port 80

# Access via: http://your-ec2-ip
```

### Streamlit Cloud (Free Hosting)
```bash
# 1. Push code to GitHub
git add ui/streamlit_demo.py requirements.txt
git commit -m "Add Streamlit UI"
git push

# 2. Go to streamlit.io/cloud
# 3. Connect GitHub repo
# 4. Deploy with one click
# 5. Get permanent URL: https://your-app.streamlit.app
```

### Docker Container
```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

CMD ["streamlit", "run", "ui/streamlit_demo.py", "--server.address", "0.0.0.0"]
```

---

## Next Steps

1. **Try Streamlit UI** (recommended for your use case)
   ```bash
   source .venv/bin/activate
   pip install -r requirements.txt
   streamlit run ui/streamlit_demo.py
   ```

2. **Customize branding** - Edit the CSS in `streamlit_demo.py`

3. **Practice demo** - Run through the full workflow

4. **Deploy for customer access** - Use Streamlit Cloud or EC2

5. **Gather feedback** - Iterate based on customer responses

---

## Troubleshooting

### Port Already in Use
```bash
# Streamlit
streamlit run ui/streamlit_demo.py --server.port 8502

# Gradio
python ui/gradio_demo.py --server_port 7861
```

### AgentCore Not Found
```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Verify agentcore is installed
which agentcore
```

### UI Dependencies Missing
```bash
pip install -r requirements.txt
```

### Can't Share Externally
```bash
# Option 1: Use ngrok
brew install ngrok
streamlit run ui/streamlit_demo.py &
ngrok http 8501

# Option 2: Deploy to Streamlit Cloud (see Deployment section)
```

---

## Questions?

- **Need help customizing?** Edit the CSS in the `st.markdown()` sections
- **Want different colors?** Modify the gradient colors in the style blocks
- **Need authentication?** Add Streamlit authentication library
- **Want to track usage?** Add Google Analytics to the app

