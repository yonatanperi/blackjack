from threading import Thread
from GUI.room import Room
from gui_form import GUIForm
from tkinter import *
from tkinter.ttk import *
from PIL import Image, ImageTk
import os
import re


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
        Label(self.root, textvariable=self.welcome_text).grid(ipady=20, row=3, columnspan=3)

        self.admin = self.socket.recv_message()  # is admin?
        self.socket.send_message(True)  # ready!
        self.username = self.socket.recv_message()
        self.dealers_hand, self.my_hand = self.socket.recv_message()

        self.my_turn = False
        self.buttons = []  # for when it's your turn

        self.root.geometry('1133x700')
        Thread(target=self.get_staff_from_server).start()

        # dealer's hand
        self.dealers_label_text = StringVar()
        Label(self.root, textvariable=self.dealers_label_text).grid(row=0, column=0)
        self.config_dealers_hand(self.dealers_hand)

        # client's hand
        self.clients_label_text = StringVar()
        Label(self.root, textvariable=self.clients_label_text).grid(row=1, column=0)
        self.config_clients_hand(self.my_hand)

        # config buttons
        # for isn't working...
        self.buttons.append(Button(self.root, text="hit", command=lambda: self.socket.send_message("hit")))
        self.buttons.append(Button(self.root, text="stand", command=lambda: self.socket.send_message("stand")))
        self.buttons.append(Button(self.root, text="double", command=lambda: self.socket.send_message("double")))

        # run everything
        self.root.mainloop()

    def get_img_by_card_num(self, card_with_suit):
        # opens the image
        img = Image.open(rf"{os.path.abspath('GUI/cards_imgs')}\{card_with_suit}.jpg")

        # resize the image and apply a high-quality down sampling filter
        img = img.resize((100, 150), Image.ANTIALIAS)

        # PhotoImage class is used to add image to widgets, icons etc
        img = ImageTk.PhotoImage(img)

        # create a label
        img_label = Label(self.root, image=img)

        # set the image as img
        img_label.image = img
        return img_label

    def config_clients_hand(self, my_hand, row=1, initial_column=1):
        self.clients_label_text.set(f"Your hand:\nSum: {self.my_hand.sum_cards()}")

        self.my_hand = my_hand
        self.config_hand(self.my_hand, row, initial_column)

    def config_dealers_hand(self, dealers_hand, row=0, initial_column=1):
        self.dealers_label_text.set(f"Dealer's hand:\nSum: {self.dealers_hand.sum_cards()}")

        self.dealers_hand = dealers_hand
        self.config_hand(self.dealers_hand, row, initial_column)

    def config_hand(self, hand, row, initial_column):
        for card_with_suit in hand.suit_cards:
            self.get_img_by_card_num(card_with_suit).grid(row=row, column=initial_column)
            initial_column += 1

    def grid_buttons(self, how_much):
        for i in range(how_much):
            self.buttons[i].grid(row=2, column=i, ipady=10)

    def grid_forget_buttons(self):
        for button in self.buttons:
            button.grid_forget()

    def get_staff_from_server(self):
        recved = self.socket.recv_message()

        if self.my_turn and recved.__class__.__name__ == "int":  # need to change the buttons
            self.grid_forget_buttons()
            self.grid_buttons(recved)

        elif self.my_turn and recved.__class__.__name__ == "Hand":  # my hand have changed
            self.config_clients_hand(recved)

        elif recved.__class__.__name__ == "Hand":  # game over! change dealer's hand
            self.config_dealers_hand(recved)

        else:
            self.welcome_text.set(self.welcome_text.get() + recved)

            if self.my_turn and re.search("It's .*'s turn!", recved):  # my turn have passed
                self.my_turn = False
                self.grid_forget_buttons()

            if self.username in recved:  # my turn!
                self.my_turn = True
                self.grid_buttons(self.socket.recv_message())

        self.get_staff_from_server()
