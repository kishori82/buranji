import psycopg2
from psycopg2 import sql
from flask import current_app
from models import db, Person
import os

def batch_upload(data):
    # Get the database connection parameters from Flask configuration
    host = os.environ['DATABASE_HOST']
    port = os.environ['DATABASE_PORT']
    user = os.environ['DATABASE_USER']
    password = os.environ['DATABASE_PASSWORD']
    database = os.environ['DATABASE_NAME']

    # Connect to the database
    conn = psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database
    )

    # Create a cursor
    cur = conn.cursor()

    # Build the SQL statement to insert the data
    #values = [Person(*row) for row in data if row]
    values = []
    for row in data:
       if len(row) == 2:
           values.append(Person(*row))

    #values = [Person(*row) for row in data if row]
    db.session.bulk_save_objects(values)
    db.session.commit()

    # Commit the transaction and close the cursor and connection
    cur.close()
    conn.close()

