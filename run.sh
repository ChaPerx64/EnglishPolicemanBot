
pkill -f [E]nglishPolicemanBot.py
python3 -m venv venv
source venv/bin/activate
nohup python3 "EnglishPolicemanBot.py" >/dev/null 2>&1 &
