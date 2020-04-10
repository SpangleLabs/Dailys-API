import json
import sys
from datetime import date
from typing import Dict, Union, List, Any, Optional

import telethon.sync
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsTextItem
from telethon.tl.custom import Message

from data_source import DataSource
from importers.telegram_dreams.sifterUI import SiftCategory, SifterUI

with open("telegram_config.json", "r") as f:
    T_CONFIG = json.load(f)

API_ID = T_CONFIG["api_id"]
API_HASH = T_CONFIG["api_hash"]
CHANNEL_HANDLE = T_CONFIG["channel_handle"]
OLDEST_MESSAGE_ID = 8194
STAT_NAME = "dreams"
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
}  # type: Dict[str, Union[List[Any], Optional[date]]]


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
        current_entry = data_source.get_entries_for_stat_on_date(STAT_NAME, state["current_date"])
        if current_entry:
            print("OVERWRITING ENTRY: " + str(current_entry))
            with open("overwritten_entries.txt", "a") as f:
                f.write(STAT_NAME)
                f.write(state["current_date"].isoformat())
                f.write(json.dumps(current_entry))
                f.write("\n\n\n")
        data_source.update_entry_for_stat_on_date(STAT_NAME, state["current_date"], dailys_data, SOURCE)
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
