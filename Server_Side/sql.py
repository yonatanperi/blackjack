import mysql.connector


class SQLConnection:
    DEFAULT_SCORES = 2000

    def __init__(self):
        self.db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="7324545",
            database="blackjack"  # assuming the data base already exists
        )

        self.cursor = self.db.cursor()

    def create_db(self):
        self.cursor.execute("CREATE DATABASE IF NOT EXISTS blackjack")
        self.db.commit()

    def delete_tables(self):
        self.cursor.execute("DROP TABLE users")
        self.cursor.execute("DROP TABLE scores")
        self.db.commit()

    def create_tables(self):
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS users (username VARCHAR(20) PRIMARY KEY, password VARCHAR(100), user_type VARCHAR(20))")
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS scores (username VARCHAR(20) PRIMARY KEY, score BIGINT, win INTEGER, lose INTEGER)")
        self.db.commit()

    def reset_tables(self):
        self.cursor.execute("DELETE FROM users")
        self.cursor.execute("DELETE FROM scores")
        self.db.commit()
        self.register("yonatan", "7324545", "admin")

    def reset_db(self):
        self.create_tables()
        self.reset_tables()

    def register(self, username, password, user_type="client"):
        self.cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        if self.cursor.fetchall():
            return False

        self.cursor.execute("INSERT INTO users (username, password, user_type) VALUES (%s, %s, %s)",
                            (username, password, user_type))
        self.cursor.execute("INSERT INTO scores (username, score, win, lose) VALUES (%s, %s, 0, 0)",
                            (username, SQLConnection.DEFAULT_SCORES))
        self.db.commit()
        return True

    def login(self, username, password):
        self.cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s",
                            (username, password))
        if self.cursor.fetchall():
            return True
        return False

    def add_staff_2_user(self, username, staff, how_much):
        if self.authenticate(username):
            self.cursor.execute(f"UPDATE scores SET {staff} = {staff} + {int(how_much)} WHERE username = %s",
                                (username,))
            self.db.commit()

            return True
        return False

    def get_staff_on_user(self, username, *staff):
        query = "SELECT "
        if len(staff) == 1:
            query += staff[0]
        else:  # list or tuple
            if staff:
                query += str(staff)[1:-1].replace("'", "")
            else:
                return "ERROR"

        self.cursor.execute(
            query + " FROM users JOIN scores ON users.username = scores.username WHERE users.username = %s",
            (username,))

        returned = self.cursor.fetchall()[0]
        if len(returned) == 1:
            return returned[0]

        return returned

    def get_user_type(self, username):
        self.cursor.execute('SELECT user_type FROM users WHERE username = %s', (username,))
        return self.cursor.fetchall()[0][0]

    def execute_query(self, query, commit, get_results):
        yes_values = ['true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'certainly', 'uh-huh']
        self.cursor.execute(query)
        if commit in yes_values:
            self.db.commit()
        if get_results in yes_values:
            return self.cursor.fetchall()
        return "Nothing returned!"

    def delete_user(self, username):
        self.cursor.execute("DELETE FROM users WHERE username = %s", (username,))
        self.cursor.execute("DELETE FROM scores WHERE username = %s", (username,))
        self.db.commit()

    def authenticate(self, username):
        self.cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        if self.cursor.fetchall():
            return True
        return False
