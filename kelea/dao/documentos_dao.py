from .db_mongoDAO import BaseMongoDAO
from bson import ObjectId
from datetime import datetime


# Campos requeridos por tipo (además de los comunes)
_CAMPOS_REQUERIDOS = {
    "documento": {"path", "size", "mime_type"},
    "imagen":    {"path", "size", "mime_type"},
    "video":     {"path", "size", "mime_type"},
    "audio":     {"path", "size", "mime_type"},
    "enlace":    {"url"},
}

TIPOS_VALIDOS = set(_CAMPOS_REQUERIDOS.keys())


class DocumentosDAO(BaseMongoDAO):
    """DAO unificado para todos los tipos de documento guardados por un usuario.

    Tipos soportados: "documento", "imagen", "video", "audio", "enlace".

    Esquema común
    -------------
    _id         : ObjectId  (auto)
    email       : str       (propietario)
    tipo        : str       (discriminador)
    titulo      : str       (nombre visible)
    descripcion : str       (opcional)
    keywords    : list[str] (opcional, para búsqueda)
    f_subida    : datetime  (auto)

    Campos adicionales según tipo
    ------------------------------
    documento/imagen/video/audio:
        path      : str   (ruta del fichero en disco)
        size      : int   (tamaño en bytes)
        mime_type : str
        duracion  : float (segundos, solo video/audio, opcional)

    enlace:
        url : str
    """

    def __init__(self):
        super().__init__("documentos")
        self.collection.create_index("email")
        self.collection.create_index("tipo")
        self.collection.create_index("keywords")

    # ------------------------------------------------------------------
    # Inserción
    # ------------------------------------------------------------------

    def insert(self, values: dict) -> ObjectId | None:
        """Inserta un documento de cualquier tipo.

        Parameters
        ----------
        values : dict
            Debe incluir 'email', 'tipo' y los campos requeridos del tipo.

        Returns
        -------
        ObjectId del documento insertado, o None si hay error.

        Raises
        ------
        ValueError si falta algún campo obligatorio o el tipo no es válido.
        """
        tipo = values.get("tipo")
        if tipo not in TIPOS_VALIDOS:
            raise ValueError(f"Tipo '{tipo}' no válido. Opciones: {TIPOS_VALIDOS}")

        if not values.get("email"):
            raise ValueError("El campo 'email' es obligatorio.")

        requeridos = _CAMPOS_REQUERIDOS[tipo]
        faltantes = requeridos - values.keys()
        if faltantes:
            raise ValueError(f"Faltan campos requeridos para tipo '{tipo}': {faltantes}")

        doc = self._build_document(tipo, values)
        return self.insert_one(doc)




    def _build_document(self, tipo: str, values: dict) -> dict:
        """Construye el documento normalizado listo para MongoDB."""
        doc = {
            "email":       values["email"],
            "tipo":        tipo,
            "titulo":      values.get("titulo") or self._titulo_por_defecto(tipo, values),
            "descripcion": values.get("descripcion", ""),
            "keywords":    values.get("keywords", []),
            "f_subida":    datetime.now(),
        }

        if tipo in {"documento", "imagen", "video", "audio"}:
            doc["path"]      = values["path"]
            doc["size"]      = values["size"]
            doc["mime_type"] = values["mime_type"]
            if tipo in {"video", "audio"} and values.get("duracion") is not None:
                doc["duracion"] = values["duracion"]

        elif tipo == "enlace":
            doc["url"] = values["url"]

        return doc

    @staticmethod
    def _titulo_por_defecto(tipo: str, values: dict) -> str:
        if tipo == "enlace":
            return values.get("url", "Enlace sin título")
        return values.get("path", "Archivo sin título").split("/")[-1]

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------

    def get_by_user(self, email: str) -> list:
        """Devuelve todos los documentos del usuario, ordenados por fecha desc."""
        return list(
            self.collection.find({"email": email}).sort("f_subida", -1)
        )

    def get_by_user_and_tipo(self, email: str, tipo: str) -> list:
        """Devuelve los documentos del usuario filtrados por tipo."""
        if tipo not in TIPOS_VALIDOS:
            raise ValueError(f"Tipo '{tipo}' no válido.")
        return list(
            self.collection.find({"email": email, "tipo": tipo}).sort("f_subida", -1)
        )

    def get_by_id(self, doc_id: str | ObjectId) -> dict | None:
        """Devuelve un documento por su _id."""
        return self.find_one({"_id": ObjectId(doc_id)})

    def search(self, email: str, texto: str, tipo: str = None) -> list:
        """Busca en título, descripción y keywords (case-insensitive).

        Parameters
        ----------
        email : str
        texto : str  cadena a buscar
        tipo  : str  filtro de tipo opcional
        """
        regex = {"$regex": texto, "$options": "i"}
        query = {
            "email": email,
            "$or": [
                {"titulo":      regex},
                {"descripcion": regex},
                {"keywords":    {"$elemMatch": regex}},
                {"url":         regex},
            ],
        }
        if tipo:
            if tipo not in TIPOS_VALIDOS:
                raise ValueError(f"Tipo '{tipo}' no válido.")
            query["tipo"] = tipo

        return list(self.collection.find(query).sort("f_subida", -1))


    # ------------------------------------------------------------------
    # Eliminación
    # ------------------------------------------------------------------

    def delete_by_id(self, doc_id: str | ObjectId, email: str) -> int:
        return self.delete_one({"_id": ObjectId(doc_id), "email": email})

    def delete_all_by_user(self, email: str) -> int:
        return self.delete_many({"email": email})

    # ------------------------------------------------------------------
    # Estadísticas
    # ------------------------------------------------------------------

    def count_by_user(self, email: str, tipo: str = None) -> int:
        query = {"email": email}
        if tipo:
            query["tipo"] = tipo
        return self.count(query)

    def stats_by_user(self, email: str) -> dict:
        pipeline = [
            {"$match": {"email": email}},
            {"$group": {"_id": "$tipo", "total": {"$sum": 1}}},
        ]
        resultados = self.aggregate(pipeline)
        stats = {tipo: 0 for tipo in TIPOS_VALIDOS}
        for r in resultados:
            stats[r["_id"]] = r["total"]
        stats["total"] = sum(stats.values())
        return stats
