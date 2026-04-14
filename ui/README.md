# InfraGenie UI Frontends

This directory contains web-based user interfaces for running InfraGenie demos.

## Available UIs

### 1. Streamlit UI (Recommended)
**File:** `streamlit_demo.py`

**Features:**
- Timeline-based view showing all workflow steps
- Professional appearance with gradient styling
- Scroll up to review previous steps
- Interactive approval buttons
- Real-time progress tracking

**Launch:**
```bash
streamlit run ui/streamlit_demo.py
# Or use the helper script:
./scripts/run-streamlit.sh
```

### 2. Gradio UI
**File:** `gradio_demo.py`

**Features:**
- Tab-based interface
- Easy public sharing with --share flag
- Good for ML-focused audiences
- Automatic API generation

**Launch:**
```bash
python ui/gradio_demo.py
# Or use the helper script:
./scripts/run-gradio.sh
```

## Quick Start

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Ensure dependencies are installed
pip install -r requirements.txt

# 3. Launch UI of your choice
streamlit run ui/streamlit_demo.py
# or
python ui/gradio_demo.py
```

## Directory Structure

```
ui/
├── README.md              # This file
├── streamlit_demo.py      # Streamlit web interface
├── gradio_demo.py         # Gradio web interface
└── assets/               # Future: logos, images, CSS
```

## Adding Assets (Future)

To add custom branding:

```
ui/
└── assets/
    ├── logo.png
    ├── favicon.ico
    └── custom.css
```

Then reference in your UI code:
```python
st.image("ui/assets/logo.png")
```

## Development Tips

### Streamlit Auto-reload
```bash
# Streamlit watches for file changes automatically
streamlit run ui/streamlit_demo.py
# Edit the file, it reloads automatically!
```

### Gradio Hot Reload
```python
# In gradio_demo.py, change the launch line to:
demo.launch(debug=True)
```

### Testing Changes
1. Edit UI files in `ui/`
2. Refresh browser (Streamlit auto-reloads)
3. Test workflow end-to-end
4. Commit changes

## Deployment

### Local Network
```bash
streamlit run ui/streamlit_demo.py --server.address 0.0.0.0
# Access from other devices: http://YOUR_IP:8501
```

### Public Sharing (Temporary)
```bash
# Gradio has built-in sharing
python ui/gradio_demo.py --share
# Creates a public URL valid for 72 hours
```

### Production Deployment
See `docs/FRONTEND_OPTIONS.md` for:
- Streamlit Cloud (free hosting)
- AWS EC2 deployment
- Docker containers
- Custom domains

## Troubleshooting

### Port Already in Use
```bash
# Streamlit - use different port
streamlit run ui/streamlit_demo.py --server.port 8502

# Gradio - edit gradio_demo.py and change server_port
```

### Module Not Found
```bash
# Make sure you're in project root
cd /Users/eevangelista/work/infragenie_agentcore_langgraph

# And venv is activated
source .venv/bin/activate
```

### Changes Not Showing
- **Streamlit**: Hard refresh browser (Cmd+Shift+R on Mac)
- **Gradio**: Restart the Python process

## Best Practices

1. **Run from project root** - Always launch UIs from the project root directory
2. **Keep UI logic separate** - Don't mix UI code with agent logic
3. **Test locally first** - Before deploying, test thoroughly locally
4. **Use version control** - Commit UI changes separately from agent code
5. **Document changes** - Update this README when adding new features
