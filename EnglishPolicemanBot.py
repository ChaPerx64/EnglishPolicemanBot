import os
import sqlite3
from datetime import datetime, timedelta
from itertools import repeat
from zoneinfo import ZoneInfo

from telegram import (
    Chat,
    Update
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from dotenv import load_dotenv
import detectlanguage
from ai import check_grammar_with_ai

CURFEW_START_MSG = """
English curfew is now enforced.
Every message sent to this chat that contains non-Latin symbols will be deleted immediately.
Type /stop to end it all.
"""

CURFEW_STOP_MSG = """
English curfew ends now.
"""

HALT_MSG = """
Non-english message deleted. Type /stop to stop.
"""

CURFEW_SET_MSG = """
Curfew set. It will be enforced every day from {} until {}.
"""

CURFEW_ALLCLEARED_MSG = """
Schedule cleared of all curfews.
"""

STATUS_MSG = """
Curfew is now {}.
Scheduled curfews:
{}
"""

TZ = ZoneInfo('Europe/Belgrade')


class DBConnector:
    def __init__(self):
        self.con = sqlite3.connect('chats.db')
        self.curr = self.con.cursor()
        self.init_tables()

    def init_tables(self):
        self.curr.execute(
            '''
            CREATE TABLE IF NOT EXISTS chats_active (
                chat_id INTEGER UNIQUE,
                curfew_id INTEGER,
                FOREIGN KEY (curfew_id) REFERENCES curfews (curfew_id)
            )
            '''
        )
        self.curr.execute(
            '''
            CREATE TABLE IF NOT EXISTS curfews (
                curfew_id INTEGER PRIMARY KEY,
                chat_id INTEGER NOT NULL,
                time_start TEXT NOT NULL,
                time_end TEXT NOT NULL
            )
            '''
        )
        self.con.commit()

    def dropcreate(self):
        self.curr.execute('DROP TABLE IF EXISTS curfews')
        self.curr.execute('DROP TABLE IF EXISTS active_curfews')
        self.con.commit()

    def add_chat(self, chat_id: str, curfew_id: int | None = None):
        self.curr.execute(
            '''INSERT INTO chats_active (chat_id, curfew_id)
            VALUES (%s, %s)
            ''' % (chat_id, curfew_id)
        )
        self.con.commit()

    def remove_chat(self, chat_id: int):
        self.curr.execute(
            """DELETE FROM chats_active WHERE chat_id = %s""" % chat_id
        )
        self.con.commit()

    def clear_chat_curfews(self, chat_id: int):
        self.curr.execute(
            """DELETE FROM curfews WHERE chat_id = %s""" % chat_id
        )
        self.con.commit()

    def show_status(self, chat_id: int) -> (tuple, bool | None):
        self.curr.execute(
            """SELECT time_start, time_end FROM curfews WHERE chat_id={}""".format(
                chat_id)
        )
        sched = self.curr.fetchall()
        self.curr.execute(
            """SELECT * FROM chats_active WHERE chat_id={}""".format(chat_id)
        )
        if self.curr.fetchall():
            active = True
        else:
            active = None
        return sched, active

    def drop_active_curfews(self):
        self.curr.execute(
            'DROP TABLE active_curfews'
        )
        self.con.commit()

    def drop_curfews(self):
        self.curr.execute(
            'DROP TABLE curfews'
        )
        self.con.commit()

    def return_all(self):
        self.curr.execute('SELECT * FROM chats_active')
        return self.curr.fetchall()

    def all_tables(self):
        self.curr.execute('SELECT * FROM dba_tables')
        return self.curr.fetchall()

    def is_active(self, chat_id: str) -> bool:
        self.curr.execute(
            "SELECT chat_id FROM chats_active WHERE chat_id = '%s'" % chat_id)
        if self.curr.fetchone():
            return True

    def add_curfew(self, chat_id: int, t_start: str, t_end: str):
        sql = '''
            INSERT INTO curfews (chat_id, time_start, time_end)
            VALUES (%s, '%s', '%s')
            ''' % (chat_id, t_start, t_end)
        self.curr.execute(sql)
        self.con.commit()

    def switch_due(self, time: datetime.time) -> (tuple, tuple):
        time_str = str(time)
        self.curr.execute(
            '''
            SELECT chat_id, curfew_id FROM curfews 
            WHERE
                (time_start < '%s' AND time_end > '%s')
                OR
                (time_start > time_end AND (time_start < '%s' OR time_end > '%s'))
            EXCEPT
            SELECT chat_id, curfew_id FROM chats_active
            ''' % tuple(repeat(time_str, 4))
        )
        to_activate = self.curr.fetchall()
        self.curr.execute(
            '''
            SELECT chat_id FROM chats_active WHERE curfew_id IS NOT NULL
            EXCEPT
            SELECT chat_id FROM curfews 
            WHERE
                (time_start < '%s' AND time_end > '%s')
                OR
                (time_start > time_end AND (time_start < '%s' OR time_end > '%s'))
            ''' % tuple(repeat(time_str, 4))
        )
        to_disactivate = self.curr.fetchall()
        return to_activate, to_disactivate


async def set_curfew(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != Chat.PRIVATE:
        msg_lines = str(update.effective_message.text).split('\n')
        s_time = datetime.strptime(msg_lines[1], '%H:%M').time()
        e_time = datetime.strptime(msg_lines[2], '%H:%M').time()
        db.add_curfew(update.effective_chat.id, str(s_time), str(e_time))
        await update.effective_chat.send_message(CURFEW_SET_MSG.format(s_time, e_time))


async def clear_curfews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != Chat.PRIVATE:
        db.clear_chat_curfews(update.effective_chat.id)
        await update.effective_chat.send_message(text=CURFEW_ALLCLEARED_MSG)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != Chat.PRIVATE:
        await start_curfew(context, update.effective_chat.id)


async def start_curfew(context: ContextTypes.DEFAULT_TYPE, chat_id: int, curfew_id=None):
    db.add_chat(str(chat_id), curfew_id)
    print('Chat %s started' % chat_id)
    await context.bot.send_message(text=CURFEW_START_MSG, chat_id=chat_id)


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != Chat.PRIVATE:
        await stop_curfew(context, update.effective_chat.id)


async def stop_curfew(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    db.remove_chat(chat_id)
    print('Chat %s stopped' % chat_id)
    await context.bot.send_message(text=CURFEW_STOP_MSG, chat_id=chat_id)


async def check_schedule(context: ContextTypes.DEFAULT_TYPE):
    act, deact = db.switch_due(datetime.now(TZ).strftime('%H:%M:%S'))
    for chat_id, curfew_id in act:
        await start_curfew(context, chat_id=chat_id, curfew_id=curfew_id)
    for chat_id in deact:
        await stop_curfew(context, chat_id=chat_id[0])


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id == int(os.getenv("OWNER_ID")):
        active_chats_num = len(db.return_all())
        out_str = 'Bot is running.\nChats active: %s' % active_chats_num
        await update.effective_chat.send_message(out_str)
    elif update.effective_chat.type != Chat.PRIVATE:
        s, a = db.show_status(update.effective_chat.id)
        if a:
            a = 'active'
        else:
            a = 'inactive'
        out_str = ''
        i = 1
        if s:
            for item in s:
                out_str += '{}. Starts {}, ends {}\n'.format(i, *item)
                i += 1
        else:
            out_str = 'None'
        await update.effective_chat.send_message(STATUS_MSG.format(a, out_str))


async def curfew_enforcer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if db.is_active(str(update.effective_chat.id)):
        if detectlanguage.simple_detect(update.effective_message.text) != 'en':
            await update.effective_message.delete()
            await update.effective_chat.send_message(HALT_MSG)


async def check_grammar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != Chat.PRIVATE:
        if "/check" in update.effective_message.text:
            feedback = check_grammar_with_ai(
                text=update.effective_message.text)
            await update.effective_message.reply_text(feedback)


async def startup_msg(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(str(os.getenv('OWNER_ID')), 'EnglishPolicemanBot is up and running!')


def main():
    detectlanguage.configuration.api_key = os.getenv("TOKEN_LANGUAGE")
    app = ApplicationBuilder().token(os.getenv("TOKEN")).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('stop', stop))
    app.add_handler(CommandHandler('status', status))
    app.add_handler(CommandHandler('setcurfew', set_curfew))
    app.add_handler(CommandHandler('clear', clear_curfews))
    app.add_handler(MessageHandler(filters.COMMAND, check_grammar))
    app.add_handler(MessageHandler(filters.TEXT, curfew_enforcer))
    app.job_queue.run_repeating(check_schedule, timedelta(seconds=10))
    app.job_queue.run_once(startup_msg, 0)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    db = DBConnector()
    if load_dotenv():
        main()
