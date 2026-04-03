import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

load_dotenv()

DB_CONFIG = {
    'host' : os.getenv('HOST', 'localhost'),
    'user' : os.getenv('USER', 'root'),
    'password' : os.getenv('PASSWORD'),
    'port' : os.getenv('PORT', 3306)
}


class DBManager:
    """데이터베이스 연결 클래스
        connect
        execute
        query
        close
    """
    def __init__(self, host, user, password, database, port = 3306):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.conn = None
        self.cursor = None

    def DBconnect(self):
        try:
            self.conn = mysql.connector.connect(
                host = self.host,
                user = self.user,
                password = self.password,
                port = self.port
            )
            self.conn.cursor()

            self.cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {self.database}"
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            self.cursor.execute(f"USE {self.database}")
            print("DB연결 완료")
            return True
        
        except Error as e:
            print(f"DB연결 실패 : {e}")
            return False
            
    def DBexecute(self, query, params=None):
        """
        INSERT / UPDATE / DELETE / CREATE 실행
        """
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"실행 실패 : {e}")
            self.conn.rollback()
            return False
            
    def DBSelect(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            print(f"조회 실패 : {e}")
            return False
    
    def DBclose(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("연결 종료")