import sqlite3

def initialize_database():

    connection = sqlite3.connect("deadlines.db")

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deadlines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_name TEXT NOT NULL,
            assignment_name TEXT NOT NULL,
            due_date TEXT NOT NULL,
            due_time TEXT
        )
    """)

    connection.commit()
    connection.close()

def save_deadline(user_id, course_name, assignment_name, due_date, due_time):

    connection = sqlite3.connect("deadlines.db")
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO deadlines (
            user_id,
            course_name,
            assignment_name,
            due_date,
            due_time
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        user_id,
        course_name,
        assignment_name,
        due_date,
        due_time
    )
    )

    connection.commit()
    connection.close()

def get_deadlines_by_date(due_date):

    connection = sqlite3.connect("deadlines.db")
    cursor = connection.cursor()

    cursor.execute("""
    SELECT user_id, course_name, assignment_name, due_date, due_time
    FROM deadlines
    WHERE due_date = ?
    """, (due_date,)
    )
    deadlines = cursor.fetchall()

    connection.close()

    return deadlines
