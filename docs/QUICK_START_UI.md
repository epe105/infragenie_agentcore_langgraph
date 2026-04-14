# Quick Start: Professional UI for Customer Demos

Stop using the command line for demos! This guide shows you how to run InfraGenie with a professional web interface that customers will love.

## 🎯 The Problem

Your current demo: `python scripts/run_demo_interactive.py --prompt "create an ec2 and S3 bucket"`

**Customer experience:**
```
$ python scripts/run_demo_interactive.py --prompt "create an ec2 and S3 bucket"
======================================================================
🏗️  INFRAGENIE AGENTCORE DEMO - INTERACTIVE MODE
======================================================================
...
👤 Do you approve this remediation? (yes/no): yes  <-- Confusing!
```

Customers find it **hard to follow** on the command line.

---

## 🚀 The Solution: Streamlit Web UI

With Streamlit, customers see a **beautiful web interface**:

![Demo Flow](https://via.placeholder.com/800x400?text=Professional+Web+Interface)

- ✅ Clear buttons instead of typing yes/no
- ✅ Formatted output with syntax highlighting
- ✅ Visual progress indicators
- ✅ Mobile-friendly design
- ✅ Easy to share via URL

---

## 🎬 3-Minute Setup

### Step 1: Install UI Dependencies

```bash
# Activate your virtual environment
source .venv/bin/activate

# Install Streamlit (takes ~30 seconds)
pip install -r requirements.txt
```

### Step 2: Launch the Web UI

```bash
# Start the Streamlit app
streamlit run ui/streamlit_demo.py

# ✅ Your browser opens automatically at http://localhost:8501
```

### Step 3: Run a Demo

1. **Select Demo Type**: Click "🏗️ Infrastructure Lifecycle"
2. **Review Plan**: Click "✅ Approve & Execute"
3. **Approve Remediation**: Click "✅ Approve Remediation"
4. **Done!** See results in a beautiful format

**That's it! No more command line confusion.**

---

## 📊 What Your Customers See

### Landing Page
```
┌─────────────────────────────────────────────┐
│  🏗️ InfraGenie - Infrastructure Automation │
│                                             │
│  Select Demo Type:                          │
│  ┌─────────────────┐  ┌──────────────────┐ │
│  │ Infrastructure  │  │  Security Scan   │ │
│  │   Lifecycle     │  │                  │ │
│  └─────────────────┘  └──────────────────┘ │
│                                             │
│  Or enter custom prompt:                    │
│  ┌─────────────────────────────────────┐   │
│  │ create an EC2 and S3 bucket         │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  [ ▶️ Run Custom Prompt ]                   │
└─────────────────────────────────────────────┘
```

### Execution Plan
```
┌─────────────────────────────────────────────┐
│  📋 InfraGenie Execution Plan               │
│                                             │
│  Task: Execute infrastructure lifecycle     │
│                                             │
│  Execution Steps:                           │
│    1. [PROVISIONING] Create EC2             │
│       Tool: ansible_mcp | Duration: 3-5 min │
│    2. [STORAGE] Create S3 bucket            │
│       Tool: aws_mcp | Duration: 30 sec      │
│    ...                                      │
│                                             │
│  Risk Assessment: MEDIUM                    │
│  Estimated Time: 10-15 minutes              │
│                                             │
│  [ ✅ Approve & Execute ]  [ ❌ Deny ]      │
└─────────────────────────────────────────────┘
```

### Remediation Approval
```
┌─────────────────────────────────────────────┐
│  🚨 Remediation Approval Request            │
│                                             │
│  📊 Infrastructure Context:                 │
│    • EC2 Instance: i-0123456789abcdef0      │
│    • S3 Bucket: infragenie-backups-4902     │
│                                             │
│  ⚠️  Risk Score: 100/100                    │
│                                             │
│  🔧 Proposed Remediation:                   │
│    • Action: Block all public access        │
│    • Configuration: BlockPublicAcls, ...    │
│                                             │
│  📋 Compliance Frameworks:                  │
│    • CIS AWS Foundations: 2.1.5             │
│    • NIST 800-53: AC-3                      │
│    ...                                      │
│                                             │
│  [ ✅ Approve Remediation ]  [ ❌ Deny ]    │
└─────────────────────────────────────────────┘
```

---

## 🌐 Sharing with Remote Customers

### Option 1: Screen Share (Easiest)
```bash
# Run locally, share your screen on Zoom/Teams
streamlit run ui/streamlit_demo.py
```

### Option 2: Temporary Public URL (ngrok)
```bash
# Install ngrok
brew install ngrok

# Run Streamlit
streamlit run ui/streamlit_demo.py &

# Create public URL
ngrok http 8501

# Share the URL: https://abc123.ngrok.io
# Customers can access from anywhere!
```

### Option 3: Permanent Hosting (Streamlit Cloud - FREE)
```bash
# 1. Push your code to GitHub
git add ui/streamlit_demo.py requirements.txt
git commit -m "Add Streamlit UI"
git push

# 2. Go to https://streamlit.io/cloud
# 3. Sign in with GitHub
# 4. Click "New app"
# 5. Select your repo
# 6. Deploy!

# You get: https://your-app.streamlit.app (permanent!)
```

### Option 4: Deploy on AWS EC2
```bash
# On your EC2 instance
streamlit run ui/streamlit_demo.py --server.address 0.0.0.0 --server.port 80

# Access via: http://your-ec2-public-ip
# Configure security group to allow port 80
```

---

## 🎨 Customization Tips

### Change Colors/Branding

Edit `ui/streamlit_demo.py` (around line 20):

```python
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #YOUR_COLOR1 0%, #YOUR_COLOR2 100%);
    }
</style>
""", unsafe_allow_html=True)
```

### Add Company Logo

```python
# At the top of streamlit_demo.py
st.image("your-logo.png", width=200)
st.markdown('<div class="main-header">🏗️ YourCompany InfraGenie</div>', ...)
```

### Add Authentication

```bash
pip install streamlit-authenticator

# Add to streamlit_demo.py
import streamlit_authenticator as stauth

authenticator = stauth.Authenticate(...)
name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status:
    # Show the demo
    pass
```

---

## 📱 Mobile Support

The Streamlit UI is **fully responsive** and works on:
- 📱 Mobile phones
- 💻 Tablets
- 🖥️ Desktop computers

Your customers can run demos from their phones during meetings!

---

## 🆚 Comparison: CLI vs Web UI

| Aspect | Command Line | Streamlit Web UI |
|--------|-------------|------------------|
| **Customer Experience** | ❌ Confusing | ✅ Clear & intuitive |
| **Visual Appeal** | ❌ Plain text | ✅ Beautiful design |
| **Ease of Use** | ❌ Type yes/no | ✅ Click buttons |
| **Mobile Support** | ❌ No | ✅ Yes |
| **Sharing** | ❌ Screen share only | ✅ Send URL |
| **Professional Look** | ❌ Developer tool | ✅ Production app |
| **Setup Time** | ✅ Already works | ✅ 3 minutes |

---

## 🎯 Demo Script for Customers

Here's what to say during your demo:

### 1. Opening (30 seconds)
*"Today I'll show you InfraGenie - our AI-powered infrastructure automation platform. Instead of complex CLI commands, we have a user-friendly web interface that makes infrastructure management as easy as clicking a button."*

[Show landing page]

### 2. Demo Selection (30 seconds)
*"Let's run an infrastructure lifecycle demo. I'll just click this button..."*

[Click "Infrastructure Lifecycle"]

### 3. Plan Review (1 minute)
*"InfraGenie's AI agent has created an execution plan. Notice it shows exactly what will happen, which tools it will use, estimated time, and risk assessment. This gives you full visibility before any changes are made."*

[Review the plan with them]

### 4. Plan Approval (30 seconds)
*"You have full control - approve or deny the plan. Let's approve and proceed..."*

[Click "Approve & Execute"]

### 5. Execution (2 minutes)
*"Now our multi-agent system is working. Seven specialized agents collaborate to provision infrastructure, scan for security issues, and validate compliance..."*

[Let it run, explain agents as they execute]

### 6. Remediation (1 minute)
*"The system detected a security issue and calculated the risk score. Notice the compliance frameworks it validates against - CIS, NIST, PCI DSS, GDPR. Again, you have full control over the remediation."*

[Click "Approve Remediation"]

### 7. Results (30 seconds)
*"And we're done! The infrastructure is provisioned, secured, and compliant. All with human oversight at critical decision points."*

[Show final results]

**Total demo time: 5-6 minutes**

---

## 🐛 Troubleshooting

### Browser Doesn't Open Automatically
```bash
# Manual: Open http://localhost:8501 in your browser
```

### Port 8501 Already in Use
```bash
# Use a different port
streamlit run ui/streamlit_demo.py --server.port 8502
```

### "Module Not Found" Errors
```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### AgentCore Connection Issues
```bash
# Verify agent is deployed
agentcore status

# Check AWS credentials
aws sts get-caller-identity

# Refresh SSO login if needed
aws sso login
```

### Changes Not Showing
```bash
# Stop Streamlit (Ctrl+C)
# Restart
streamlit run ui/streamlit_demo.py

# Or enable auto-reload:
streamlit run ui/streamlit_demo.py --server.runOnSave true
```

---

## 📚 Next Steps

1. **Run your first demo**
   ```bash
   source .venv/bin/activate
   pip install -r requirements.txt
   streamlit run ui/streamlit_demo.py
   ```

2. **Practice the demo flow** - Get comfortable with the UI

3. **Customize the branding** - Add your company colors/logo

4. **Share with your team** - Get feedback on the experience

5. **Deploy for customers** - Use Streamlit Cloud or EC2

---

## 🎉 Success!

You now have a **professional web interface** for your InfraGenie demos!

No more confusing command line prompts. Just beautiful, intuitive buttons and real-time feedback.

**Your customers will love it.** 🚀

---

## 💡 Pro Tips

1. **Keep a browser tab open** - Streamlit stays running, just refresh
2. **Use fullscreen mode** (F11) - Looks even more professional
3. **Hide the sidebar** - Add `st.set_page_config(initial_sidebar_state="collapsed")`
4. **Add analytics** - Track which demos customers run most
5. **Record videos** - Use the UI for marketing materials

---

## 📞 Need Help?

- **Documentation:** See `docs/FRONTEND_OPTIONS.md` for all options
- **Customization:** Edit `ui/streamlit_demo.py` directly
- **Deployment:** Check deployment section in FRONTEND_OPTIONS.md
- **Issues:** Check troubleshooting section above

---

## 🎊 Bonus: Gradio Alternative

Prefer Gradio? We have that too:

```bash
python ui/gradio_demo.py

# Or with public sharing:
python ui/gradio_demo.py --share
```

Both UIs provide the same great experience. Choose whichever you prefer!
