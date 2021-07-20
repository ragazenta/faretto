import eel
from database import *

session = {}

conn = create_connection()
cursor = conn.cursor()


@eel.expose
def teacher_login(username, password):
    sql = "SELECT * from teacher_login WHERE username= ? AND password = ?"
    val = [username, password]
    cursor.execute(sql, val)
    result = cursor.fetchall()
    if len(result) == 1:
        global session
        session["auth"] = True
        session["username"] = result[0][1]
        eel.login_success("dashboard.html")

    else:
        eel.login_error("Invalid username or password")


@eel.expose
def logout():
    global session
    session["auth"] = False
    session["username"] = ""
    eel.logout()
