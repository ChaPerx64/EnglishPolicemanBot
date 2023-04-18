#!/bin/bash
EXECUTABLE="EnglishPolicemanBot.py"
TARDIR="/root/bots/EnglishPolicemanBot"
ssh humble_dunnok "mkdir $TARDIR"
scp *.py ".env" "requirements.txt" "root@188.225.86.226:$TARDIR"
ssh humble_dunnok << EOF
pkill -f "$EXECUTABLE"
cd "$TARDIR"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
nohup python3 "$EXECUTABLE" >/dev/null 2>&1 &
EOF
