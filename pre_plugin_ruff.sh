#!/bin/bash

set -euo pipefail

# Never check pip for new version while running this script
export PIP_DISABLE_PIP_VERSION_CHECK=1

# Check if ruff is installed globally
if ! (poetry run pip list | grep "ruff" > /dev/null); then
    echo
    echo "Installing 'ruff' in current project"
    echo
    poetry add "ruff@*" --group dev
    poetry install
fi

echo
echo "Running Plugin ruff..."
poetry run ruff check --fix
RUFF_STATUS=$?
if [ $RUFF_STATUS -ne 0 ]; then
    echo "ruff check failed."
    exit 1
fi

exit 0 