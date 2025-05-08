#!/bin/bash

set -euo pipefail

# Never check pip for new version while running this script
export PIP_DISABLE_PIP_VERSION_CHECK=1

# Check if mypy is installed globally
if ! (poetry run pip list | grep "mypy" > /dev/null); then
    echo
    echo "Installing 'mypy' in current project"
    echo
    poetry add "mypy@*" --group dev
    poetry install
fi

# Install types if not installed
#  - do not use > /dev/null 2>&1 - this will show which packages should by in pyproject.toml
poetry run mypy --install-types --non-interactive

echo
echo "Running Plugin mypy..."
poetry run mypy .
MYPY_STATUS=$?
if [ $MYPY_STATUS -ne 0 ]; then
    echo "mypy check failed."
    exit 1
fi

exit 0 