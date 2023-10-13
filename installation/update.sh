#!/bin/bash
set -euo pipefail

echo ""
echo "## Updating MRI4ALL console software..."
echo ""

cd /opt/mri4all/console
git pull
source /opt/mri4all/env/bin/activate
pip install -r requirements.txt

echo ""
echo "Update complete."
echo ""
