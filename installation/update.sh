#!/bin/bash
set -euo pipefail

echo ""
echo "## Updating MRI4ALL console software..."
echo ""

cd /opt/mri4all/console
git pull
source /opt/mri4all/env/bin/activate
pip install -r requirements.txt

if [ ! -e "/opt/mri4all/console/external/marcos_client/local_config.py" ]; then
  cp /opt/mri4all/console/external/marcos_client/local_config.py.example /opt/mri4all/console/external/marcos_client/local_config.py
fi

echo ""
echo "Update complete."
echo ""
