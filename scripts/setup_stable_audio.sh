#!/bin/bash
set -e

# --- Helper Functions ---
echo_info() {
    echo "INFO: $1"
}

echo_success() {
    echo "✅ SUCCESS: $1"
}

echo_warn() {
    echo "⚠️ WARNING: $1"
}

echo_error() {
    echo "❌ ERROR: $1" >&2
    exit 1
}

# --- Main Script ---

# 1. Check for Python 3.10+
if ! command -v python3 &> /dev/null; then
    echo_error "Python 3 is not installed. Please install Python 3.10 or later."
fi

# A simple version check
python3 -c 'import sys; sys.exit(0) if sys.version_info >= (3, 10) else sys.exit(1)' || echo_error "Python 3.10 or later is required."

echo_info "Python 3.10+ found."

# 2. Create Python virtual environment
VENV_DIR=".venv"
if [ -d "$VENV_DIR" ]; then
    echo_info "Virtual environment '$VENV_DIR' already exists."
else
    echo_info "Creating Python virtual environment in '$VENV_DIR'..."
    python3 -m venv "$VENV_DIR"
    echo_success "Virtual environment created."
fi

# 3. Activate virtual environment and install dependencies
echo_info "Installing dependencies..."
# Sourcing in a script only affects the script's subshell, which is fine here.
source "$VENV_DIR/bin/activate"
pip install -q requests pydub
deactivate
echo_success "Dependencies (requests, pydub) installed."

# 4. Ensure .gitignore is set up correctly
GITIGNORE_FILE=".gitignore"
if [ ! -f "$GITIGNORE_FILE" ]; then
    echo_info "Creating .gitignore file..."
    touch "$GITIGNORE_FILE"
fi

# Add .venv/ to .gitignore if not present
if ! grep -q -x "^\.venv/$" "$GITIGNORE_FILE"; then
    echo_info "Adding .venv/ to .gitignore..."
    echo ".venv/" >> "$GITIGNORE_FILE"
fi

echo_success "Setup complete! To activate the environment, run: source .venv/bin/activate"
