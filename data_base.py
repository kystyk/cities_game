import sqlite3


def change_db(func):
    def wrapper(*args, **kwargs):
        con = sqlite3.connect("data_base.db")
        curs = con.cursor()
        data = func(*args, **kwargs, curs=curs)
        con.commit()
        con.close()
        return data

    return wrapper


@change_db
def create_db(curs):
    curs.execute("CREATE TABLE IF NOT EXIST users(chat_id INT PRIMARY KEY, score INT, cities TEXT)")


@change_db
def insert_data(chat_id, score, cities, curs):
    curs.execute(f"INSERT INTO users(chat_id, score, cities) VALUES({chat_id}, {score}, '{cities}')")


@change_db
def update_data(chat_id, score, cities, curs):
    curs.execute(f"UPDATE users SET score = {score}, cities = '{cities}' WHERE chat_id = {chat_id}")


@change_db
def get_all_data(curs):
    curs.execute("SELECT * FROM users")
    return curs.fetchall()


@change_db
def delete(chat_id, curs):
    curs.execute(f"DELETE FROM users WHERE chat_id = {chat_id}")


@change_db
def get_data(chat_id, curs):
    curs.execute(f"SELECT * FROM users WHERE chat_id = {chat_id}")

    return curs.fetchone()


create_db()