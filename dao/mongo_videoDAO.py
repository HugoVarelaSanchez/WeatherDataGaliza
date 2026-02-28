from .db_mongoDAO import BaseMongoDAO
from datetime import datetime


class videoDAO(BaseMongoDAO):

    def __init__(self):
        super().__init__("documentos")
        self.collection.create_index("email")
        self.collection.create_index("keywords")


    def insert_video(self, video_values: dict):
        document = {
            "email":       video_values["email"],
            "path":        video_values["path"],
            "descripcion": video_values.get("descripcion", ""),
            "size":        video_values["size"],
            "duracion":    video_values["duracion"],
            "f_creacion":  video_values["f_creacion"],
            "f_subida":    datetime.now(),
            "keywords":    video_values.get("keywords", []),
        }
        return self.insert_one(document)


    def get_by_user(self, email: str):
        return self.find_many({"email": email})


    def filter_by_word(self, keyword: str):
        return self.find_many({"keywords": keyword})