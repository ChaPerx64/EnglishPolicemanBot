
pkill -f [E]nglishPolicemanBot.py
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
nohup python3 "EnglishPolicemanBot.py" >/dev/null 2>&1 &
