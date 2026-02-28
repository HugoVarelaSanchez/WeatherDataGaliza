from .dbdao import BaseDAO
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta




class tokenDAO(BaseDAO):


    def __init__(self):
        super().__init__()


    def insert_token(self, token_values:dict):

        query = '''
                INSERT INTO token_login(token, email, f_creacion, f_expiracion)
                VALUES 
                    (?, ?, ?, ?)
                '''
        return self.execute_query(query, (token_values['token'], token_values['email'], datetime.now(), datetime.now()+timedelta(weeks=2)), fetch=False)
 


    def update_token(self, token, email):
        
        query = '''
                DELETE FROM token_login
                WHERE email = ?
                '''
        self.execute_query(query, (email,), fetch=False)

        h_token = generate_password_hash(token)

        self.insert_token({'email':email, 'token':h_token})




    def delete_token(self, email):
        

        query = '''
                DELETE FROM token_login
                WHERE email = ?
                '''
        return self.execute_query(query, (email,), fetch=False)
        




    def check_token(self, email, n_token):
         
        query = '''
                SELECT *
                FROM token_login
                WHERE email = ?
                '''
        
        p_token_h = self.execute_query(query, (email,))

        if p_token_h == []:
            return False
        
        
        token_h = p_token_h[0][0]

        if token_h != None:
            if len(n_token) and len(token_h) > 0:
                check = check_password_hash(token_h, n_token)
                return check
            
        return False
    




    def check_user(self, email):   # Comprueba si un usuario tiene token 
        

        query = '''
                SELECT COUNT(*) 
                FROM token_login
                WHERE email = ?
                '''
        result = self.execute_query(query, (email,))
        return result[0][0] > 0
