import time

from GUI.game_room import GameRoom
from GUI.room import Room
from tkinter import *
from tkinter.ttk import *


class ClientRoom(Room):

    def __init__(self, socket, LoRe):
        super().__init__(socket)
        self.LoRe = LoRe  # to avoid circular import
        self.user2join = StringVar()
        self.create_button = Button(self.root, text="Create Game", command=self.create_game)
        self.create_button.grid(row=1, column=0)
        Button(self.root, text="Join Game", command=self.join_game).grid(row=1, column=1)
        Button(self.root, text="Logout", command=self.logout).grid(row=1, column=2)

        self.join_label = Label(self.root, text="User to join:")
        self.join_entry = Entry(self.root, textvariable=self.user2join)

        # run everything
        self.root.mainloop()

    def create_game(self):
        self.socket.send_message("create")
        self.root.destroy()
        GameRoom(self.socket)

    def join_game(self):
        entry_text = self.user2join.get()
        if entry_text == "":
            self.join_label.grid(row=2, column=0)
            self.join_entry.grid(row=2, column=1)
            self.create_button.grid_forget()
        else:
            self.socket.send_message("join")
            time.sleep(1)
            if self.socket.get_answer(entry_text):  # is vailed
                self.root.destroy()
                GameRoom(self.socket)

    def logout(self):
        self.socket.send_message("logout")
        self.root.destroy()
        self.LoRe(self.socket)
