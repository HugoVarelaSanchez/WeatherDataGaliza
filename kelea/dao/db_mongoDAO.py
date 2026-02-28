import os
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv


class BaseMongoDAO:
    """Clase base para gestionar la conexion a MongoDB"""

    _client = None
    _db = None

    load_dotenv()

    _credentials = {
        "host": os.getenv("MONGO_HOST", "localhost"),
        "port": int(os.getenv("MONGO_PORT", 27017)),
        "username": os.getenv("MONGO_USER", None),
        "password": os.getenv("MONGO_PASSWORD", None),
    }

    _db_name = os.getenv("MONGO_DB", "mydb")
#~

    @classmethod
    def init_connection(cls):
        """Inicializa el cliente MongoDB.

        Crea una unica instancia del cliente (patron singleton)
        que reutiliza la conexion interna de pymongo, la cual
        ya gestiona un pool de conexiones internamente.
        """
        if cls._client is None:
            try:
                cls._client = MongoClient(
                    host=cls._credentials["host"],
                    port=cls._credentials["port"],
                    username=cls._credentials["username"],
                    password=cls._credentials["password"],
                )
                cls._db = cls._client[cls._db_name]
                # Verificar conexion
                cls._client.admin.command("ping")
                print("Conexion a MongoDB establecida correctamente")
            except PyMongoError as e:
                print(f"Error al conectar a MongoDB: {e}")
                cls._client = None


    @classmethod
    def get_db(cls):
        """Devuelve la instancia de la base de datos."""
        if cls._db is None:
            raise Exception("La conexion a MongoDB no ha sido inicializada")
        return cls._db


    @classmethod
    def close_connection(cls):
        """Cierra la conexion con MongoDB."""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None


    def __init__(self, collection_name: str):
        """
        Parameters
        ----------
        collection_name: str
            Nombre de la coleccion MongoDB a usar en este DAO
        """
        self.collection = self.get_db()[collection_name]


    def insert_one(self, document: dict):
        """Inserta un documento en la coleccion.

        Parameters
        ----------
        document: dict
            Documento a insertar

        Returns
        -------
        InsertedId o None si hay error
        """
        try:
            result = self.collection.insert_one(document)
            return result.inserted_id
        except PyMongoError as e:
            print(f"Error al insertar documento: {e}")
            return None


    def insert_many(self, documents: list):
        """Inserta multiples documentos en la coleccion.

        Parameters
        ----------
        documents: list
            Lista de documentos a insertar
        """
        try:
            result = self.collection.insert_many(documents)
            return result.inserted_ids
        except PyMongoError as e:
            print(f"Error al insertar documentos: {e}")
            return None


    def find_one(self, query: dict, projection: dict = None):
        """Busca un unico documento que coincida con el filtro.

        Parameters
        ----------
        query: dict
            Filtro de busqueda
        projection: dict
            Campos a incluir/excluir (opcional)
        """
        try:
            return self.collection.find_one(query, projection)
        except PyMongoError as e:
            print(f"Error al buscar documento: {e}")
            return None


    def find_many(self, query: dict = None, projection: dict = None):
        """Busca todos los documentos que coincidan con el filtro.

        Parameters
        ----------
        query: dict
            Filtro de busqueda (None devuelve todos)
        projection: dict
            Campos a incluir/excluir (opcional)
        """
        try:
            return list(self.collection.find(query or {}, projection))
        except PyMongoError as e:
            print(f"Error al buscar documentos: {e}")
            return []


    def update_one(self, query: dict, update: dict, upsert: bool = False):
        """Actualiza un documento que coincida con el filtro.

        Parameters
        ----------
        query: dict
            Filtro para encontrar el documento
        update: dict
            Operacion de actualizacion (ej: {"$set": {...}})
        upsert: bool
            Si True, inserta si no existe
        """
        try:
            result = self.collection.update_one(query, update, upsert=upsert)
            return result.modified_count
        except PyMongoError as e:
            print(f"Error al actualizar documento: {e}")
            return 0


    def delete_one(self, query: dict):
        """Elimina el primer documento que coincida con el filtro.

        Parameters
        ----------
        query: dict
            Filtro para encontrar el documento
        """
        try:
            result = self.collection.delete_one(query)
            return result.deleted_count
        except PyMongoError as e:
            print(f"Error al eliminar documento: {e}")
            return 0


    def delete_many(self, query: dict):
        """Elimina todos los documentos que coincidan con el filtro.

        Parameters
        ----------
        query: dict
            Filtro para encontrar los documentos
        """
        try:
            result = self.collection.delete_many(query)
            return result.deleted_count
        except PyMongoError as e:
            print(f"Error al eliminar documentos: {e}")
            return 0


    def count(self, query: dict = None):
        """Cuenta los documentos que coincidan con el filtro.

        Parameters
        ----------
        query: dict
            Filtro (None cuenta todos)
        """
        try:
            return self.collection.count_documents(query or {})
        except PyMongoError as e:
            print(f"Error al contar documentos: {e}")
            return 0


    def aggregate(self, pipeline: list):
        """Ejecuta un pipeline de agregacion.

        Parameters
        ----------
        pipeline: list
            Lista de etapas del pipeline de agregacion
        """
        try:
            return list(self.collection.aggregate(pipeline))
        except PyMongoError as e:
            print(f"Error al ejecutar agregacion: {e}")
            return []