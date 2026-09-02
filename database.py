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

    cursor.execute("PRAGMA table_info(deadlines)")

    columns = [column[1] for column in cursor.fetchall()]

    if "canvas_uid" not in columns:
        cursor.execute("""
            ALTER TABLE deadlines
            ADD COLUMN canvas_uid TEXT
        """)

    if "d2l_uid" not in columns:
        cursor.execute("""
            ALTER TABLE deadlines
            ADD COLUMN d2l_uid TEXT
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS canvas_feeds (
            user_id INTEGER PRIMARY KEY,
            calendar_url TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS d2l_feeds (
            user_id INTEGER PRIMARY KEY,
            calendar_url TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()

def save_canvas_feed(user_id, calendar_url):

    connection = sqlite3.connect("deadlines.db")
    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO canvas_feeds (
            user_id,
            calendar_url
        )
        VALUES (?, ?)
    """, (
        user_id,
        calendar_url
    ))

    connection.commit()
    connection.close()

def get_canvas_feeds():

    connection = sqlite3.connect("deadlines.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT user_id, calendar_url
        FROM canvas_feeds
    """)

    feeds = cursor.fetchall()

    connection.close()

    return feeds

def save_canvas_deadline(
    user_id,
    course_name,
    assignment_name,
    due_date,
    due_time,
    canvas_uid
):

    connection = sqlite3.connect("deadlines.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM deadlines
        WHERE user_id = ?
        AND canvas_uid = ?
    """, (
        user_id,
        canvas_uid
    ))

    existing_deadline = cursor.fetchone()

    if existing_deadline:

        cursor.execute("""
            UPDATE deadlines
            SET course_name = ?,
                assignment_name = ?,
                due_date = ?,
                due_time = ?
            WHERE id = ?
        """, (
            course_name,
            assignment_name,
            due_date,
            due_time,
            existing_deadline[0]
        ))

    else:

        cursor.execute("""
            INSERT INTO deadlines (
                user_id,
                course_name,
                assignment_name,
                due_date,
                due_time,
                canvas_uid
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            course_name,
            assignment_name,
            due_date,
            due_time,
            canvas_uid
        ))

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

def save_d2l_feed(user_id, calendar_url):

    connection = sqlite3.connect("deadlines.db")
    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO d2l_feeds (
            user_id,
            calendar_url
        )
        VALUES (?, ?)
    """, (
        user_id,
        calendar_url
    ))

    connection.commit()
    connection.close()


def get_d2l_feeds():

    connection = sqlite3.connect("deadlines.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT user_id, calendar_url
        FROM d2l_feeds
    """)

    feeds = cursor.fetchall()

    connection.close()

    return feeds


def save_d2l_deadline(
    user_id,
    course_name,
    assignment_name,
    due_date,
    due_time,
    d2l_uid
):

    connection = sqlite3.connect("deadlines.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM deadlines
        WHERE user_id = ?
        AND d2l_uid = ?
    """, (
        user_id,
        d2l_uid
    ))

    existing_deadline = cursor.fetchone()

    if existing_deadline:

        cursor.execute("""
            UPDATE deadlines
            SET course_name = ?,
                assignment_name = ?,
                due_date = ?,
                due_time = ?
            WHERE id = ?
        """, (
            course_name,
            assignment_name,
            due_date,
            due_time,
            existing_deadline[0]
        ))

    else:

        cursor.execute("""
            INSERT INTO deadlines (
                user_id,
                course_name,
                assignment_name,
                due_date,
                due_time,
                d2l_uid
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            course_name,
            assignment_name,
            due_date,
            due_time,
            d2l_uid
        ))

    connection.commit()
    connection.close()

def get_upcoming_deadlines(user_id, start_date, end_date):

    connection = sqlite3.connect("deadlines.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT course_name, assignment_name, due_date, due_time
        FROM deadlines
        WHERE user_id = ?
        AND due_date BETWEEN ? AND ?
        ORDER BY due_date, due_time
    """, (
        user_id,
        start_date,
        end_date
    ))

    deadlines = cursor.fetchall()

    connection.close()

    return deadlines

def delete_user_data(user_id):

    connection = sqlite3.connect("deadlines.db")
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM deadlines
        WHERE user_id = ?
    """, (user_id,))

    print("Deadlines deleted:", cursor.rowcount)

    cursor.execute("""
        DELETE FROM canvas_feeds
        WHERE user_id = ?
    """, (user_id,))

    print("Canvas feeds deleted:", cursor.rowcount)

    cursor.execute("""
        DELETE FROM d2l_feeds
        WHERE user_id = ?
    """, (user_id,))

    print("D2L feeds deleted:", cursor.rowcount)

    connection.commit()
    connection.close()