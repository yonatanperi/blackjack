from gui_form import GUIForm
from tkinter import *
from tkinter.ttk import *


class Room(GUIForm):
    def __init__(self, socket):
        super().__init__(socket)

        self.welcome_text = StringVar()
        self.welcome_text.set(socket.recv_message())
        Label(self.root, textvariable=self.welcome_text).grid(ipady=20, row=0, columnspan=3)
