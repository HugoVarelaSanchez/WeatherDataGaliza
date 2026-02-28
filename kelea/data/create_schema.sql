-- Base de datos relacional relacionada con los usuarios
-- SQLite3 compatible schema

DROP TABLE IF EXISTS token_login;
DROP TABLE IF EXISTS usuario;


CREATE TABLE usuario(
    email VARCHAR(50) NOT NULL,
    nombre VARCHAR(50) NOT NULL, 
    contrasenha_hash TEXT NOT NULL,
    telefono INTEGER,

    CONSTRAINT PK_usuario PRIMARY KEY (email)
);


CREATE TABLE token_login(
    token VARCHAR(564) NOT NULL,
    email VARCHAR(50) NOT NULL,
    f_creacion TIMESTAMP NOT NULL,
    f_expiracion TIMESTAMP NOT NULL,

    CONSTRAINT PK_token_login PRIMARY KEY (token, email),

    CONSTRAINT FK_tokenL_usuario FOREIGN KEY (email)
    REFERENCES usuario(email)
    ON DELETE CASCADE
);
