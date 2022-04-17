import db, json
import psycopg2.extras

class dc():
    def __init__(self):
        pass

    # Get all found anomalies from anomaly DB
    @staticmethod
    def add_config(user_id, account_id, property_id, view_id):
        with db.con:
            cur = db.con.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("INSERT INTO config (id, account, property, view) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING", (user_id, account_id, property_id, view_id))
            db.con.commit()

    @staticmethod
    def get_config(user_id):
        with db.con:
            cur = db.con.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("SELECT * FROM config WHERE id = %s", (user_id,))
            config = cur.fetchall()
            db.con.commit()
            return config

