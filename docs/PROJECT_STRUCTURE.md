# InfraGenie Project Structure

This document explains the organization of the InfraGenie project and best practices for adding new components.

## 📁 Directory Structure

```
infragenie_agentcore_langgraph/
│
├── ui/                           # Web-based user interfaces
│   ├── README.md                 # UI documentation
│   ├── streamlit_demo.py         # Streamlit web interface
│   ├── gradio_demo.py            # Gradio web interface
│   └── assets/                   # (Future) Images, CSS, logos
│
├── scripts/                      # Executable scripts & automation
│   ├── run_demo_interactive.py   # CLI demo (terminal-based)
│   ├── run-streamlit.sh          # Launch Streamlit UI
│   └── run-gradio.sh             # Launch Gradio UI
│
├── src/                          # Backend code (deployed to AgentCore)
│   ├── agentcore_main.py         # AgentCore entry point
│   ├── infragenie_langgraph_agent.py  # Main orchestrator
│   ├── planner_agent.py          # Planner component
│   ├── infrastructure_lifecycle_demo.py  # 7-agent workflow
│   ├── security_demo.py          # 5-agent security workflow
│   ├── mcp_tools.py              # Ansible MCP integration
│   ├── aws_mcp_tools.py          # AWS MCP integration
│   └── ...                       # Other agent components
│
├── docs/                         # Documentation
│   ├── ARCHITECTURE.md           # System architecture
│   ├── CODE_WALKTHROUGH.md       # Code explanation
│   ├── FRONTEND_OPTIONS.md       # Frontend comparison & setup
│   ├── QUICK_START_UI.md         # Quick start guide
│   └── PROJECT_STRUCTURE.md      # This file
│
├── tests/                        # Test files
│   ├── test_agentcore_integration.py
│   └── test_mcp_connection.py
│
├── .venv/                        # Virtual environment
├── .env                          # Environment variables
├── .env.example                  # Environment template
├── requirements.txt              # All Python dependencies
├── README.md                     # Main project README
└── .bedrock_agentcore.yaml       # AgentCore configuration

```

## 🎯 Design Principles

### Separation of Concerns

1. **`ui/`** - Web interfaces that users interact with
   - **What goes here:** Streamlit, Gradio, or any web UI framework
   - **What doesn't:** Backend logic, agent code, business logic
   - **Purpose:** User interaction and display only

2. **`scripts/`** - Automation, CLI tools, helper scripts
   - **What goes here:** CLI demos, deployment scripts, automation
   - **What doesn't:** Web UIs, deployed agent code
   - **Purpose:** Command-line tools and automation

3. **`src/`** - Backend code deployed to AgentCore
   - **What goes here:** Agent logic, workflows, MCP integrations
   - **What doesn't:** UI code, test scripts, documentation
   - **Purpose:** The actual AI agent that runs in AWS

4. **`docs/`** - All documentation
   - **What goes here:** Architecture, guides, tutorials, API docs
   - **What doesn't:** Code, configurations
   - **Purpose:** Human-readable documentation

5. **`tests/`** - Test files
   - **What goes here:** Unit tests, integration tests
   - **What doesn't:** Production code
   - **Purpose:** Quality assurance

## 🚀 Execution Methods

### Option 1: Direct Execution (Recommended)

```bash
# From project root
cd /Users/eevangelista/work/infragenie_agentcore_langgraph

# Activate environment
source .venv/bin/activate

# Run UIs
streamlit run ui/streamlit_demo.py
python ui/gradio_demo.py

# Run CLI demo
python scripts/run_demo_interactive.py
```

### Option 2: Helper Scripts (Convenient)

```bash
# From project root
./scripts/run-streamlit.sh
./scripts/run-gradio.sh

# Or from anywhere
cd /Users/eevangelista/work/infragenie_agentcore_langgraph
./scripts/run-streamlit.sh
```

The helper scripts:
- ✅ Activate the virtual environment automatically
- ✅ Check for dependencies
- ✅ Launch from the correct directory
- ✅ Show helpful error messages

### Option 3: Make Shortcuts (Power Users)

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
alias infragenie-ui="cd ~/work/infragenie_agentcore_langgraph && ./scripts/run-streamlit.sh"
alias infragenie-cli="cd ~/work/infragenie_agentcore_langgraph && source .venv/bin/activate && python scripts/run_demo_interactive.py"
```

Then just run:
```bash
infragenie-ui
```

## 📦 Best Practices for Organization

### When Adding a New UI

1. **Create in `ui/` directory**
   ```bash
   touch ui/new_ui_demo.py
   ```

2. **Add launch script in `scripts/`**
   ```bash
   touch scripts/run-new-ui.sh
   chmod +x scripts/run-new-ui.sh
   ```

3. **Update `ui/README.md`** with instructions

4. **Document in main `README.md`**

### When Adding Backend Logic

1. **Create in `src/` directory**
   ```bash
   touch src/new_agent.py
   ```

2. **Import in main agent** (`src/infragenie_langgraph_agent.py`)

3. **Test locally** before deploying

4. **Deploy to AgentCore**
   ```bash
   agentcore deploy
   ```

### When Adding a Script/Tool

1. **Create in `scripts/` directory**
   ```bash
   touch scripts/new_automation.py
   chmod +x scripts/new_automation.py
   ```

2. **Add shebang line**
   ```python
   #!/usr/bin/env python3
   ```

3. **Document in `scripts/README.md`** (create if needed)

### When Adding Documentation

1. **Create in `docs/` directory**
   ```bash
   touch docs/NEW_FEATURE.md
   ```

2. **Link from main README.md**

3. **Use clear markdown formatting**

## 🔄 Development Workflow

### Frontend Development

```bash
# 1. Edit UI file
vim ui/streamlit_demo.py

# 2. Test immediately (Streamlit auto-reloads)
streamlit run ui/streamlit_demo.py

# 3. Commit changes
git add ui/streamlit_demo.py
git commit -m "Update: improved timeline view"
```

### Backend Development

```bash
# 1. Edit agent code
vim src/infragenie_langgraph_agent.py

# 2. Test locally (if possible)
python src/infragenie_langgraph_agent.py

# 3. Deploy to AgentCore
agentcore deploy

# 4. Test via UI or CLI
streamlit run ui/streamlit_demo.py
```

### Documentation Updates

```bash
# 1. Edit docs
vim docs/ARCHITECTURE.md

# 2. Preview (optional, if using markdown previewer)
# No need to deploy - docs are just files

# 3. Commit
git add docs/ARCHITECTURE.md
git commit -m "Docs: updated architecture diagram"
```

## 🎨 Why This Structure?

### Advantages

1. **Clear Separation** - Easy to find files
   - Need to update UI? Look in `ui/`
   - Need to fix agent logic? Look in `src/`
   - Need to run something? Look in `scripts/`

2. **Deployment Clarity**
   - Only `src/` gets deployed to AgentCore
   - `ui/` stays local or deployed separately
   - No confusion about what goes where

3. **Scalability**
   - Easy to add more UIs (`ui/react_demo/`, `ui/vue_demo/`)
   - Easy to add more scripts (`scripts/monitoring/`, `scripts/deploy/`)
   - Easy to add more docs (`docs/tutorials/`, `docs/api/`)

4. **Team Collaboration**
   - Frontend developers work in `ui/`
   - Backend developers work in `src/`
   - DevOps works in `scripts/`
   - Tech writers work in `docs/`
   - Minimal merge conflicts

5. **Professional Standards**
   - Follows industry conventions
   - Easy for new team members to understand
   - Looks professional to customers/stakeholders

## 🚫 Anti-Patterns to Avoid

### ❌ Don't Do This

```
# Bad: UI files in project root
infragenie_agentcore_langgraph/
├── streamlit_demo.py          # ❌ Clutters root
├── gradio_demo.py             # ❌ Clutters root
├── app.py                     # ❌ Unclear purpose
└── main.py                    # ❌ What does this do?
```

```
# Bad: Mixed responsibilities
src/
├── agent.py
├── streamlit_ui.py            # ❌ UI in src/
└── deployment_script.sh       # ❌ Script in src/
```

```
# Bad: No organization
everything_in_root/
├── file1.py
├── file2.py
├── script.py
├── ui.py
└── ... (50 more files)        # ❌ Impossible to navigate
```

### ✅ Do This

```
# Good: Clear organization
infragenie_agentcore_langgraph/
├── ui/
│   ├── streamlit_demo.py      # ✅ UI in ui/
│   └── gradio_demo.py         # ✅ UI in ui/
├── src/
│   └── agent.py               # ✅ Agent code in src/
└── scripts/
    └── deploy.sh              # ✅ Scripts in scripts/
```

## 📚 Quick Reference

| I want to... | Go to... | Command |
|-------------|----------|---------|
| Run web UI | `ui/` | `streamlit run ui/streamlit_demo.py` |
| Run CLI demo | `scripts/` | `python scripts/run_demo_interactive.py` |
| Edit agent logic | `src/` | `vim src/infragenie_langgraph_agent.py` |
| Add documentation | `docs/` | `vim docs/NEW_GUIDE.md` |
| Create automation | `scripts/` | `vim scripts/new_tool.py` |
| Add new UI | `ui/` | `vim ui/new_frontend.py` |
| Run tests | `tests/` | `python tests/test_*.py` |

## 🎓 Learning Resources

- **UI Development**: See `ui/README.md`
- **Agent Development**: See `docs/CODE_WALKTHROUGH.md`
- **Architecture**: See `docs/ARCHITECTURE.md`
- **Quick Start**: See `docs/QUICK_START_UI.md`
- **Frontend Options**: See `docs/FRONTEND_OPTIONS.md`

## 🤝 Contributing

When adding new features:

1. **Follow the structure** - Put files in the right directory
2. **Update documentation** - Document your changes
3. **Add helper scripts** - Make it easy to use
4. **Test thoroughly** - Don't break existing functionality
5. **Keep it clean** - Remove unused files

## 📞 Questions?

- **Structure questions**: This file
- **UI questions**: `ui/README.md`
- **Agent questions**: `docs/CODE_WALKTHROUGH.md`
- **Setup questions**: `README.md`
