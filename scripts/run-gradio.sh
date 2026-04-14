#!/bin/bash
#
# Launch Gradio UI for InfraGenie
# This script activates the virtual environment and launches the Gradio interface
#

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Error: Virtual environment not found"
    echo "Please run: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Check if gradio is installed
if ! python -c "import gradio" 2>/dev/null; then
    echo "❌ Error: Gradio not installed"
    echo "Please run: pip install -r requirements.txt"
    exit 1
fi

# Launch Gradio
echo "🚀 Launching Gradio UI..."
echo "📱 Browser will open at: http://localhost:7860"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python ui/gradio_demo.py "$@"
