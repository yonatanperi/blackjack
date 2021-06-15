from sql import SQLConnection


class ClientRoom:

    def __init__(self, client, server):
        self.server = server
        self.client = client
        self.sql = SQLConnection()

    def authenticate_client(self):

        authentication = self.client.recv_message()  # [username, password, *args]
        lo_re = self.sql.login
        if len(authentication) > 2:
            lo_re = self.sql.register

        if not lo_re(*authentication):
            self.client.send_message(False)
            return self.authenticate_client()

        self.client.username = authentication[0]
        if not self.server.login(self.client):
            self.client.send_message(False)
            return self.authenticate_client()

        self.client.send_message(True)

        # user authenticated!
        """
        if self.sql.get_user_type(self.client.username) == "admin":
            return AdminRoom(self.client, self.server).main_menu()
        """
        return self.main_menu()

    def main_menu(self):

        self.sql = SQLConnection()  # reset sql
        points = self.sql.get_staff_on_user(self.client.username, "score")

        self.client.send_message(f"""Welcome {self.client} to main menu!
You have {points} points!
Wins: {self.sql.get_staff_on_user(self.client.username, "win")}
Losses: {self.sql.get_staff_on_user(self.client.username, "lose")}""")

        if points <= 0:
            return

        else:
            answer = self.client.recv_message()

            if answer == "create":
                self.client.open_game_room()
                self.client.game_room.join(self.client)
            elif answer == "join":
                game_room = self.server.get_game_room(self.client.recv_message())

                self.client.send_message(game_room)
                if not game_room:
                    return self.main_menu()
                game_room.join(self.client)

            elif answer == "logout":
                self.server.clients.remove(self.client)
                print(f"{self.client} loged out!")
                self.authenticate_client()

            return self.main_menu()


class AdminRoom(ClientRoom):
    def __init__(self, client, server):
        super().__init__(client, server)
        self.admin_commands = {  # {command number: (command description, function to activate, print?)}
            1: ("Go to players main menu", super().main_menu, False),
            2: ("Get info on user (syntax: 2, user, *staff)", self.sql.get_staff_on_user, True),
            3: ("Add staff to user (syntax: 3, user, staff, how much)", self.sql.add_staff_2_user, False),
            4: ("Delete user (syntax: 4, user)", self.sql.delete_user, False),
            5: ("Reset database", self.sql.reset_db, False),
            6: ("Execute query (syntax: 6, query, commit db?, print results?)", self.sql.execute_query, True)
        }

    def main_menu(self):
        self.client.send_message(f"Welcome to admin main menu!\nEnter a number of command:\n")
        for command_number, command_description in self.admin_commands.items():
            self.client.send_message(f"{command_number}. {command_description[0]}")

        if self.get_command():
            self.logout()
            return

        self.main_menu()

    def get_command(self):
        command = self.client.recv_message()
        if command in ("quit", "exit"):
            return True
        command_number, args = self.authenticate_command(command)

        try:
            if args:
                returned = self.admin_commands[command_number][1](*args)
            else:
                returned = self.admin_commands[command_number][1]()
        except:
            self.client.send_message(f"Something went wrong...")
            return

        if self.admin_commands[command_number][2]:
            if returned.__class__.__name__ == "str":
                self.client.send_message(returned)
            else:
                str_rows = ""
                for row in returned:
                    str_rows += str(row) + "\n"

                self.client.send_message(str_rows)

        self.client.send_message(f"Done!\n")
        return False

    def authenticate_command(self, command):

        valid = True
        args = []

        if ", " in command:
            command = command.split(", ")
            command_number = self.authenticate_command(command[0])[0]
            args = command[1:]

        elif command.isdigit():
            command_number = int(command[0])

            if command_number not in self.admin_commands.keys():
                valid = False

        else:
            valid = False

        if not valid:
            self.client.send_message("Invalid!")
            return self.main_menu()

        return command_number, args
