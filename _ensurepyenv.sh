#!/bin/bash

set -eou pipefail

# Check if pyenv is installed
if ! command -v pyenv &> /dev/null; then
    echo "pyenv not found. Install it first:"
    echo "  macOS: brew install pyenv"
    echo "  Linux: curl https://pyenv.run | bash"
    echo ""
    echo "Then add to ~/.zshrc or ~/.bashrc:"
    echo '  export PATH="$HOME/.pyenv/bin:$PATH"'
    echo '  eval "$(pyenv init -)"'
    exit 1
fi

echo "✓ pyenv is ready"
