# http://flask.pocoo.org/docs/1.0/tutorial/database/

import psycopg2
import os

DATABASE_URL = os.environ.get('DATABASE_URL')
con = psycopg2.connect(DATABASE_URL)
print("connected to DB", con)
