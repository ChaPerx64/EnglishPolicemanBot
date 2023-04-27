#!/bin/bash
SRVR="root@188.225.86.226"
EXECUTABLE="EnglishPolicemanBot.py"
TARDIR="/root/bots/EnglishPolicemanBot"
ssh $SRVR "mkdir $TARDIR"
scp *.py "requirements.txt" "$SRVR:$TARDIR"
ssh $SRVR << EOF
cd "$TARDIR"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
EOF
bash run.sh
