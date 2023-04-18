import os
import sqlite3

from telegram import (
    Chat,
    ChatMember,
    Update
)
from telegram.ext import (
    ApplicationBuilder,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from dotenv import load_dotenv
import detectlanguage

CURFEW_START_MSG = """
English curfew is now enforced.
Every message sent to this chat that contains non-Latin symbols will be deleted immediately.
Type /stop to end it all.
"""

CURFEW_STOP_MSG = """
English curfew ends now.
Wohl!
"""

HALT_MSG = """
Non-english message deleted. Type /stop to stop.
"""


class DBConnector:
    def __init__(self):
        self.con = sqlite3.connect('chats.db')
        self.curr = self.con.cursor()
        self.curr.execute(
            '''
            CREATE TABLE IF NOT EXISTS chats (
                chat_id INT PRIMARY KEY
            )
            '''
        )

    def add_chat(self, chat_id: str):
        self.curr.execute(
            '''INSERT INTO chats (chat_id)
            VALUES (%s)
            ''' % chat_id
        )
        self.con.commit()

    def remove_chat(self, chat_id: str):
        self.curr.execute(
            """DELETE FROM chats WHERE chat_id = '%s'""" % chat_id
        )
        self.con.commit()

    def drop_chats(self):
        self.curr.execute(
            'DROP TABLE chats'
        )
        self.con.commit()

    def return_all(self):
        self.curr.execute('SELECT * FROM chats')
        return self.curr.fetchall()

    def is_active(self, chat_id: str) -> bool:
        self.curr.execute("SELECT chat_id FROM chats WHERE chat_id = '%s'" % chat_id)
        if self.curr.fetchone():
            return True


async def chat_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    olds, status = update.my_chat_member.difference().get("status", (None, None))
    if status is ChatMember.MEMBER:
        pass


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != Chat.PRIVATE:
        print('Chat %s started' % update.effective_chat.id)
        db.add_chat(str(update.effective_chat.id))
        await update.effective_chat.send_message(CURFEW_START_MSG)


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != Chat.PRIVATE:
        print('Chat %s stopped' % update.effective_chat.id)
        db.remove_chat(str(update.effective_chat.id))
        await update.effective_chat.send_message(CURFEW_STOP_MSG)


async def return_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id == int(os.getenv("OWNER_ID")):
        active_chats_num = len(db.return_all())
        out_str = 'Bot is running.\nChats active: %s' % active_chats_num
        await update.effective_chat.send_message(out_str)


async def curfew_enforcer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if db.is_active(str(update.effective_chat.id)):
        # lang = detectlanguage.simple_detect(update.effective_message.text)
        if detectlanguage.simple_detect(update.effective_message.text) != 'en':
            await update.effective_message.delete()
            await update.effective_chat.send_message(HALT_MSG)


def main():
    detectlanguage.configuration.api_key = os.getenv("TOKEN_LANGUAGE")
    app = ApplicationBuilder().token(os.getenv("TOKEN")).build()
    # app.add_handler(ChatMemberHandler(chat_setup, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('stop', stop))
    app.add_handler(CommandHandler('status', return_all))
    app.add_handler(MessageHandler(filters.TEXT, curfew_enforcer))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    db = DBConnector()
    if load_dotenv():
        main()
        pass
        # detectlanguage.configuration.api_key = os.getenv("TOKEN_LANGUAGE")
        # print(detectlanguage.simple_detect('Hello, how are you?'))
