import mysql.connector
from mysql.connector import Error

def get_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            port=1106,
            user="pg2",
            password="distri123",
            database="distri_pan_desa"
        )

        return connection

    except Error as e:
        print(f"Error de conexión: {e}")
        return None