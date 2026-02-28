import os
import sqlite3
from dotenv import load_dotenv

class BaseDAO:
    """Clase base para gestionar la conexión a SQLite3"""

    load_dotenv()

    # Path to SQLite database file
    _db_path = os.getenv("DB_PATH", "data/hackudc.db")

    @classmethod
    def init_connection_pool(cls):
        """Inicializar la base de datos SQLite.

        Crea el archivo de base de datos si no existe
        y aplica el schema inicial.
        """
        try:
            # Create data directory if it doesn't exist
            db_dir = os.path.dirname(cls._db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)

            # Initialize database with schema if it doesn't exist
            if not os.path.exists(cls._db_path):
                cls._initialize_schema()
                print(f"Base de datos SQLite creada en: {cls._db_path}")
            else:
                print(f"Conectado a base de datos SQLite: {cls._db_path}")
        except Exception as e:
            print(f"Error al inicializar la base de datos: {e}")

    @classmethod
    def _initialize_schema(cls):
        """Crea el schema inicial de la base de datos"""
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'create_schema.sql')

        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                schema_sql = f.read()

            conn = sqlite3.connect(cls._db_path)
            try:
                conn.executescript(schema_sql)
                conn.commit()
                print("Schema de base de datos creado exitosamente")
            except Exception as e:
                print(f"Error al crear schema: {e}")
            finally:
                conn.close()

    def __init__(self):
        self.connection = None
        self.cursor = None

    def get_connection(self):
        """Obtiene una conexión a SQLite.

        Crea una nueva conexión a la base de datos SQLite.
        """
        self.connection = sqlite3.connect(BaseDAO._db_path)
        # Enable foreign keys
        self.connection.execute("PRAGMA foreign_keys = ON")
        return self.connection

    def return_connection(self):
        """Cierra la conexión a la base de datos"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def execute_query(self, query:str, params:list|tuple=None, fetch=True):
        """Ejecuta una consulta SQL o una operación DDL

        Según el tipo de operación puede devolver un resultado
        o modificar el estado de la base de datos.

        Parameters
        ----------
        query: str
            Consulta a ejecutar (usar ? como placeholder para SQLite)
        params: list | tuple
            Parámetros

        """
        try:
            self.connection = self.get_connection()
            self.cursor = self.connection.cursor()
            self.cursor.execute(query, params if params else ())

            if fetch: # Recuperar
                result = self.cursor.fetchall()
                if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                    self.connection.commit()
                return result

            self.connection.commit()
            return True
        except Exception as e:
            if self.connection:
                self.connection.rollback()
            print(f"Error al ejecutar consulta: {e}")
            raise
        finally: # Kill cursor and return connection
            if self.cursor:
                self.cursor.close()
            self.return_connection()
