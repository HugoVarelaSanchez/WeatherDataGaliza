import os
from psycopg2 import pool
from dotenv import load_dotenv

class BaseDAO:
    """Clase base para gestionar la conexión a PostgreSQL"""
    

    # Cargar variables de entorno de .env
    _connection_pool = None
    
    load_dotenv()

    _credentials = {"dbname": os.getenv("dbname"),
                       "user": os.getenv("user"),
                       "password": os.getenv("password"),
                       "host": os.getenv("host"),
                       "port": os.getenv("port")}





    #Inicializacion del pool de conexion
    @classmethod
    def init_connection_pool(cls, minconn:int=1, maxconn:int=100):
        """Inicializar la conexión pool.

        
        Permite crear una caché de conexiones de 
        la base de datos para que se puedan reutilizar
        y así ahorrar tiempo.

        
        Parameters
        ----------
        minconn: int
            Conexiones mínimas
        maxconn: int
            Conexiones máximas
        """
        if cls._connection_pool is None:
            try:
                cls._connection_pool = pool.ThreadedConnectionPool(
                    minconn, 
                    maxconn,
                    **cls._credentials
                )
            except Exception as e:
                print(f"Error al crear el pool de conexiones: {e}")
                
    



    def __init__(self):
        self.connection = None
        self.cursor = None
    




    def get_connection(self):
        """Obtiene una conexión del pool.
        
        Busca si existe una conexión ya creada 
        en el pool de conexiones.
        """
        if BaseDAO._connection_pool is None:
            raise Exception("El pool de conexiones no ha sido inicializado")
        
        self.connection = BaseDAO._connection_pool.getconn()
        return self.connection
    




    def return_connection(self):
        """Devuelve la conexión al pool
        
        Una vez utilizado la conexión se 
        retorna al pool
        """
        if self.connection: #Activated
            BaseDAO._connection_pool.putconn(self.connection)
            self.connection = None
    




    def execute_query(self, query:str, params:list|tuple=None, fetch=True):
        """Ejecuta una consulta SQL o una operación DDL 
        
        Según el tipo de operación puede devolver un resultado
        o modificar el estado de la base de datos.

        Parameters
        ----------
        query: str
            Consulta a ejecutar
        params: list | tuple
            Parámetros 
        
        """
        try:
            self.connection = self.get_connection()
            self.cursor = self.connection.cursor()
            self.cursor.execute(query, params)
            
            if fetch: # Recuperar
                result = self.cursor.fetchall()
                if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                    self.connection.commit()  # Esta es la línea añadida
                return result
            
            self.connection.commit()
            return True
        except Exception as e:
            if self.connection:
                self.connection.rollback()
            print(f"Error al ejecutar consulta: {e}")
        finally: # Kill cursor and return connection
            if self.cursor:
                self.cursor.close()
            self.return_connection()




