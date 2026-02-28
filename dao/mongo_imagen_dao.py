from .db_mongoDAO import BaseMongoDAO
from datetime import datetime


class ImageDAO(BaseMongoDAO):

    def __init__(self):
        super().__init__("documentos")
        self.collection.create_index("email")
        self.collection.create_index("keywords")


    def insert_imagen(self, imagen_values: dict):
        document = {
            "email":       imagen_values["email"],
            "path":        imagen_values["path"],
            "descripcion": imagen_values.get("descripcion", ""),
            "size":        imagen_values["size"],
            "f_creacion":  imagen_values["f_creacion"],
            "f_subida":    datetime.now(),
            "keywords":    imagen_values.get("keywords", []),
        }
        return self.insert_one(document)


    def get_by_user(self, email: str):
        return self.find_many({"email": email})


    def filter_by_word(self, keyword: str):
        return self.find_many({"keywords": keyword})