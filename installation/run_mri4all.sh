#!/bin/bash
source /opt/mri4all/env/bin/activate
cd /opt/mri4all/console
python run_ui.py
gnome-session-quit --logout --force
