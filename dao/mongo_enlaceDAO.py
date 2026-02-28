from .db_mongoDAO import BaseMongoDAO
from datetime import datetime

# Cuando llamamos referencia, nos referimos a lo que lleva el enlace

class urlDAO(BaseMongoDAO):

    def __init__(self):
        super().__init__("documentos")
        self.collection.create_index("email")
        self.collection.create_index("referencia")


    def insert_url(self, url_values: dict):
        document = {
            "email":       url_values["email"],
            "url":        url_values["url"],
            "descripcion": url_values.get("descripcion", ""),
            "f_subida":    datetime.now(),
            "referencia":    url_values.get("referencia", []),
        }
        return self.insert_one(document)


    def get_by_user(self, email: str):
        return self.find_many({"email": email})


    def filter_by_reference(self, referencia: str):
        return self.find_many({"referencia": referencia})