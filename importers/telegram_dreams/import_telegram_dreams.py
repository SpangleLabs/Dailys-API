import sys

import telethon.sync
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsTextItem
from telethon.tl.custom import Message

from data_source import DataSource
from importers.telegram_dreams.sifterUI import SiftCategory, SifterUI

API_ID = 0
API_HASH = ""
CHANNEL_HANDLE = -1001
OLDEST_MESSAGE_ID = 0
STAT_NAME = ""
SOURCE = "Parsed from telegram channel"


def get_client(api_id, api_hash):
    client = telethon.TelegramClient('duplicate_checker', api_id, api_hash)
    client.start()
    return client


def iter_channel_messages(client, channel_handle):
    channel_entity = client.get_entity(channel_handle)
    for message in client.iter_messages(channel_entity):
        yield message


messages = []
t_client = get_client(API_ID, API_HASH)
# Get messages, filter them
for message in iter_channel_messages(t_client, CHANNEL_HANDLE):
    print(message.id)
    if message.id <= OLDEST_MESSAGE_ID:
        break
    if "sploo" not in message.text.lower():
        messages.append(message)
        print(message.date)
        print(message.text)

# Categorise messages, user control
state = {
    "dream_messages": [],
    "related_messages": [],
    "current_date": None
}


data_source = DataSource()


def add_dream(x: Message):
    print("add dream called")
    if state["current_date"] is None:
        state["current_date"] = x.date.date()
    if state["current_date"] != x.date.date():
        extra = [msg.text for dream in state["dream_messages"] for msg in dream["extra"]]
        dailys_data = {
            "dreams": [{"text": d["dream"].text} for d in state["dream_messages"]]
        }
        if extra:
            dailys_data["extra"] = extra
        print("POSTING DATA: "+str(dailys_data))
        current_entry = data_source.get_entries_for_stat_on_date(STAT_NAME, x.date.date())
        if current_entry:
            print("ARGH")
        else:
            data_source.update_entry_for_stat_on_date(STAT_NAME, x.date.date(), dailys_data, SOURCE)
        state["dream_messages"].clear()
    state["current_date"] = x.date.date()
    dream_data = {"dream": x, "extra": state["related_messages"]}
    state["dream_messages"].append(dream_data)
    state["related_messages"].clear()


buttons = [
    SiftCategory(
        "D",
        "Dream",
        add_dream
    ),
    SiftCategory(
        "S",
        "Skip",
        lambda x: print("Skipping: " + x.text)
    ),
    SiftCategory(
        "A",
        "Additional dream data",
        lambda x: state["related_messages"].append(x)
    )
]


def display_text(message, view: QGraphicsView):
    text = QGraphicsTextItem()
    text.setPos(0, 0)
    text.setPlainText(message.text)
    text.setTextWidth(view.width())

    scene = QGraphicsScene()
    scene.addItem(text)
    view.setAlignment(Qt.AlignTop | Qt.AlignLeft)
    view.setScene(scene)


app = QtWidgets.QApplication(sys.argv)
window = SifterUI(messages, buttons, display_text)
window.show()
# sys.exit(app.exec_())
app.exec_()
