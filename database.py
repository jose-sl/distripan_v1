import mysql.connector
from mysql.connector import Error

from config import MYSQL_HOST, MYSQL_PORT, \
    MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB_NAME

def get_connection():
    try:
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            port=int(MYSQL_PORT),
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB_NAME
        )

        return connection

    except Error as e:
        print(f"Error de conexión: {e}")
        raise