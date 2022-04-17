from flask_login import UserMixin
import db, json
import psycopg2.extras

class User(UserMixin):
    def __init__(self, id_, code, email):
        self.id = id_
        self.code = code
        self.email = email

    @staticmethod
    def get(user_id):
        with db.con:
            cur = db.con.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("SELECT * FROM users WHERE CAST(id AS INTEGER) = %s", (user_id,))
            db_user = cur.fetchone()
        if not db_user:
            return None
        user = User(id_=db_user['id'], code=db_user['code'], email=db_user['email'])
        return user

    @staticmethod
    def update(code, email):
        with db.con:
            cur = db.con.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            db_user = cur.fetchone()
            if not db_user:
                cur.execute("SELECT max(id) FROM users")
                db_user = cur.fetchone()
                if db_user['max'] is None:
                    id_ = 0
                else:
                    id_ = db_user['max']
                cur.execute("INSERT INTO users (id, code, email) VALUES (%s, %s, %s)", (id_,json.dumps(code),email))
            else:
                id_ = db_user['id']
                cur.execute("UPDATE users SET code = %s WHERE id = %s", (json.dumps(code),id_))
            db.con.commit()
            return id_
