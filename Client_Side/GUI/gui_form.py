from tkinter import *


class GUIForm:

    def __init__(self, socket):
        self.root = Tk()
        self.root.geometry('809x500')
        self.root.title('BlackJack')
        self.socket = socket
