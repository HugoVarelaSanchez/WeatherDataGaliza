from .dbdao import BaseDAO
from werkzeug.security import check_password_hash, generate_password_hash





class usuarioDAO(BaseDAO):


    def __init__(self):
        super().__init__()


    def insert_user(self, user_values:dict):

        query = '''
                INSERT INTO usuario(email, nombre, contrasenha_hash, telefono)
                VALUES
                    (%s, %s, %s, %s)
                '''
        return self.execute_query(query, (user_values['email'], user_values['nombre'], user_values['contrasenha_hash'], user_values['telefono']), fetch=False)









    def get_user(self, email):

        query = '''
                SELECT * 
                FROM usuario
                WHERE email = %s
                '''
        
        aux_result = self.execute_query(query, (email,))
        if len(aux_result) == 0:
                return []
        else:
            result = []
            for i in aux_result:
                result.append({'email':i[0], 'nombre':i[1], 'contrasenha':i[2], 'telefono':i[3]})
            return result
        





    def check_credenciales(self, email, contraseña_texto_plano): 
 
        query = '''
                SELECT contrasenha_hash
                FROM usuario
                WHERE email = %s 
                '''
        
        p_contrasenha_hash_guardada = self.execute_query(query, (email,))

        if p_contrasenha_hash_guardada == []:
            return None
        
        contrasenha_hash_guardada = p_contrasenha_hash_guardada[0][0]
        
        if len(contrasenha_hash_guardada) and len(contraseña_texto_plano) > 0:
            check = check_password_hash(contrasenha_hash_guardada, contraseña_texto_plano)
            return check
        
        return False
    



    def check_user_exist(self, email):
        
        query = '''
                SELECT COUNT(*) 
                FROM usuario
                WHERE email = %s
                '''
        result = self.execute_query(query, (email,))
        return result[0][0] > 0 