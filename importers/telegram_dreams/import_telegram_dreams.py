import sys
import time
from typing import Dict

import telethon.sync
import keyboard
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsTextItem

from importers.telegram_dreams.sifterUI import SiftCategory, SifterUI

API_ID = 0
API_HASH = ""
CHANNEL_HANDLE = -1001
OLDEST_MESSAGE_ID = 0


def get_client(api_id, api_hash):
    client = telethon.TelegramClient('duplicate_checker', api_id, api_hash)
    client.start()
    return client


def iter_channel_messages(client, channel_handle):
    channel_entity = client.get_entity(channel_handle)
    for message in client.iter_messages(channel_entity):
        yield message


def get_key(key_options: Dict[str, str]):
    while True:
        key = keyboard.read_key()
        print(f"Please press a key to categorise: {key_options}")
        if key in key_options.keys():
            return key


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
dream_messages = []
related_messages = []


def add_dream(x):
    dream_data = {"dream": x, "extra": related_messages}
    print(dream_data)
    dream_messages.append(dream_data)
    related_messages.clear()


buttons = [
    SiftCategory(
        "D",
        "Dream",
        add_dream
    ),
    SiftCategory(
        "S",
        "Skip",
        lambda x: print("Skip")
    ),
    SiftCategory(
        "A",
        "Additional dream data",
        lambda x: related_messages.append(x)
    )
]


def display_text(message, view: QGraphicsView):
    text = QGraphicsTextItem()
    text.setPos(0, 0)
    text.setPlainText(message.text)

    scene = QGraphicsScene()
    scene.addItem(text)
    view.setScene(scene)


app = QtWidgets.QApplication(sys.argv)
window = SifterUI(messages, buttons, display_text)
window.show()
sys.exit(app.exec_())

print(len(dream_messages))
