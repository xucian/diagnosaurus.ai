#!/bin/bash

# Must be sourced: . _actvenv.sh
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Source this script: . _actvenv.sh"
    exit 1
fi

# Skip if in Docker
if ! grep -Eq "(docker|podman)" /proc/1/cgroup 2>/dev/null && ! grep -q docker /proc/self/mountinfo 2>/dev/null; then
    . ./venv/bin/activate
fi
