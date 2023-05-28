
pkill -f [E]nglishPolicemanBot.py
git pull origin main
git status
python3 -m venv venv
source venv/bin/activate
nohup python3 "$EXECUTABLE" >/dev/null 2>&1 &
