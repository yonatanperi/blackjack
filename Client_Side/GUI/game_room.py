from threading import Thread
from GUI.room import Room
from gui_form import GUIForm
from tkinter import *
from tkinter.ttk import *
from PIL import Image, ImageTk
import random
import os


class GameRoom(Room):

    def __init__(self, socket):
        super().__init__(socket)
        self.bet = StringVar()

        Label(self.root, text="Enter bet:").grid(row=1, column=1)
        Entry(self.root, textvariable=self.bet).grid(row=1, column=2)
        Button(self.root, text="Ready!", command=self.place_bet).grid(row=1, column=3)

        self.please_wait_label = Label(self.root, text="Please wait to the game to start!")

        # run everything
        self.root.mainloop()

    def place_bet(self):
        self.socket.send_message(self.bet.get())
        self.please_wait_label.grid(row=2, columnspan=3)
        if self.socket.recv_message():  # is vailed
            self.root.destroy()
            _StartGame(self.socket)


class _StartGame(GUIForm):
    def __init__(self, socket):
        super().__init__(socket)

        self.welcome_text = StringVar()
        self.welcome_text.set(socket.recv_message())
        # Label(self.root, text=self.welcome_text.get()).grid(ipady=20, row=0, column=0, sticky=W)

        self.admin = self.socket.recv_message()  # is admin?
        self.socket.send_message(True)  # ready!
        self.username = self.socket.recv_message()
        self.dealers_hand, self.my_hand = self.socket.recv_message()

        self.my_turn = False
        self.dealers_column_index = self.clients_column_index = 2

        self.root.geometry('1133x700')
        Thread(target=self.get_staff_from_server).start()

        Label(self.root, text="Dealer's hand:").grid(row=1, column=1)
        for i in range(2):
            self.get_img_by_card_num(self.dealers_hand.cards[i]).grid(row=1, column=self.dealers_column_index)
            self.clients_column_index += 1

        Label(self.root, text="Your hand:").grid(row=2, column=1)
        for i in range(2):
            self.get_img_by_card_num(self.my_hand.cards[i]).grid(row=2, column=self.clients_column_index)
            self.clients_column_index += 1

        # run everything
        self.root.mainloop()

    def get_img_by_card_num(self, card_num):
        # opens the image
        img = Image.open(rf"{os.path.abspath('GUI/cards_imgs')}\{card_num}{random.choice(('C', 'H', 'S', 'D'))}.jpg")

        # resize the image and apply a high-quality down sampling filter
        img = img.resize((100, 150), Image.ANTIALIAS)

        # PhotoImage class is used to add image to widgets, icons etc
        img = ImageTk.PhotoImage(img)

        # create a label
        img_label = Label(self.root, image=img)

        # set the image as img
        img_label.image = img
        return img_label

    def get_staff_from_server(self):
        recved = self.socket.recv_message()
        self.welcome_text.set(self.welcome_text.get() + "\n----------\n" + recved)
        if self.username in recved:  # my turn!
            self.my_turn = True
        return self.get_staff_from_server
