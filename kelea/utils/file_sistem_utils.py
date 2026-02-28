import os, re


def crear_directorio(path: str, mode: int = 0o750):

    try:
        os.makedirs(path, mode=mode, exist_ok=True)
        os.makedirs(os.path.join(path, 'brutos'), mode=mode, exist_ok=True)
        os.makedirs(os.path.join(path, 'procesado'), mode=mode, exist_ok=True)

        return True
    
    except Exception as e:
        return False



def crear_path_name(email: str, base_dir: str = 'users_files', crear = True):

    
    nombre_usuario = re.sub(r'[^a-zA-Z0-9]', '_', email.replace('@', '_').replace('.', '_'))
    directorio_usuario = os.path.join(base_dir, nombre_usuario)
    
    return directorio_usuario

