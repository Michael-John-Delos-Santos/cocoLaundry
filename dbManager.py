import mysql.connector
from mysql.connector import Error

class DatabaseManager:
    def __init__(self, host='localhost', database='cocobubblewash', user='root', password=''):
        """
        Initialize the database connection parameters.
        Change the 'user' and 'password' if your MySQL setup requires it.
        """
        self.host = host
        self.database = database
        self.user = user
        self.password = password

    def connect(self):
        """Establishes and returns a connection to the database."""
        try:
            conn = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )
            if conn.is_connected():
                return conn
        except Error as e:
            print(f"Database Connection Error: {e}")
            # Returning None allows the UI to handle the error gracefully instead of crashing
            return None

    def execute_query(self, query, params=None):
        """
        Executes INSERT, UPDATE, DELETE queries.
        Returns the last inserted row ID on success, or None on failure.
        """
        conn = self.connect()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
            last_id = cursor.lastrowid
            return last_id
        except Error as e:
            print(f"Query Execution Error: {e}\nQuery: {query}")
            conn.rollback() # Rollback changes on error
            return None
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def fetch_all(self, query, params=None):
        """
        Executes SELECT queries that return multiple rows.
        Returns a list of dictionaries.
        """
        conn = self.connect()
        if not conn:
            return []
            
        try:
            # dictionary=True makes it easier to access columns by name (e.g., row['user_id'])
            cursor = conn.cursor(dictionary=True) 
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            return result
        except Error as e:
            print(f"Fetch All Error: {e}\nQuery: {query}")
            return []
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def fetch_one(self, query, params=None):
        """
        Executes SELECT queries that return a single row.
        Returns a dictionary or None.
        """
        conn = self.connect()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            result = cursor.fetchone()
            return result
        except Error as e:
            print(f"Fetch One Error: {e}\nQuery: {query}")
            return None
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def log_audit(self, user_id, action_type, entity_type, entity_id, description, old_value=None, new_value=None):
        """
        Helper method to insert audit logs easily across the application.
        """
        query = """
            INSERT INTO Audit_Logs 
            (user_id, action_type, entity_type, entity_id, description, old_value, new_value)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (user_id, action_type, entity_type, entity_id, description, old_value, new_value)
        self.execute_query(query, params)