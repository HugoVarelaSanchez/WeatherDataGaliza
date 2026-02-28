from flask import Flask, flash, session,  redirect, url_for, jsonify, request, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import json, secrets
from dao import *
from utils import *

def app():


    app = Flask(__name__)

    app.config['DEBUG'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_NAME'] = 'hackudc25'         

    usuario_dao = usuarioDAO()
    token_dao = tokenDAO()


    def login_check():
        def login_check_real(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
 
                try: 
                    # Si no hay un email guardado en la sesion, comprobamos el token
                    if 'user_email' not in session: 
        
                        auth_token = request.cookies.get('login_token')


                        if auth_token:
                            
                            try: 
                                login_data = json.loads(auth_token)
                                n_token = login_data.get('token')
                                n_email = login_data.get('email')

                            except (json.JSONDecodeError, TypeError):
                                return redirect(url_for('login'))
                        
                            
                            check = tokenDAO.check_token(n_email, n_token)
                            

                            #Compruebas si ese token es valido con ese email
                            if check:                        #Inicias sesion


                                usuario_activo = usuario_dao.get_user(n_email)

                                session_data = {
                                    'user_email': n_email,
                                    'user_name': usuario_activo['nombre'],
                                    'user_phone': usuario_activo['telefono'],
                                }
                            
                                session.update(session_data) 

                                

                                token = secrets.token_hex(32)
                                token_dao.update_token(token, n_email)
                                
                                resp = redirect(url_for('index'))
                                resp.set_cookie(
                                    'login_token', 
                                    json.dumps({'token': token, 'email': n_email}),  
                                    max_age=2592000, 
                                    httponly=True, 
                                    secure=True
                                )

                                return resp
                        



                    #Si hay un email guardado en la sesion
                    #Verificamos que todo esta bien
                    else:
                        user = usuario_dao.get_user(session['user_email'])
                        
                        #Si no esta guardado ese email, error
                        if not user:
                            flash(f'No existe ningun usuario con el email: {session["user_email"]}', 'error')
                            session.clear()
                            return redirect(url_for('login'))
                        
                        token_almacenado = session.get('auth_token')
                        if not token_dao.check_token(session['user_email'], token_almacenado):
                            session.clear()
                            return redirect(url_for('login'))
                    

                except Exception as e:
                        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

                return f(*args, **kwargs)
            decorated_function.__name__ = f.__name__
            return decorated_function
        return login_check_real
            







    @app.route('/login', methods=['GET', 'POST'])
    def login():

        if request.method == 'POST': 
            
            email = request.form.get('email')
            passwor = request.form.get('password')

            existencia, checkeo = usuario_dao.check_user_exist(email), False


            if existencia:
                checkeo = usuario_dao.check_credenciales(email, request.form.get('password'))

            else: 
                return render_template('login.html', error='Usuario no registrado')

            if checkeo:
                usuario_activo = usuario_dao.get_user_cod(email)
                
                session_data = {
                    'user_email': email,
                    'user_name': usuario_activo['nombre'],
                    'user_phone': usuario_activo['telefono'],
                    }
        
                session.update(session_data)

                if request.form.get('remember'):

                    token = secrets.token_hex(32)
                    token_autenticacion = token_dao.check_user(email)

                    if token_autenticacion:
                        token_dao.update_token(token, email)
                
                    resp = redirect(url_for('index'))
                    resp.set_cookie(
                        'login_token', 
                        json.dumps({'token': token, 'email': email}),  
                        max_age=2592000, 
                        httponly=True, 
                        secure=True
                    )

                    return resp

                return redirect(url_for('index'))

            return render_template('login.html', error='Credenciales invalidas')

        return render_template('login.html')




    @app.route('/register', methods=['GET', 'POST'])
    def register():  
        
        if request.method == 'POST':

            
            
            email = request.form.get('email') 

            user = usuario_dao.get_user(email)
            if user is not None:
                return render_template('register.html', error='Este usuario ya esta registrado')



            nombre = request.form.get('nombre')
            if not nombre:
                return render_template('register.html', error='Debes anhadir un nombre de usuario')
            
            telefono = request.form.get('phone')

            contrasenha = request.form.get('contrasenha')
            check_contra = request.form.get('contrasenha_confirm')
            if not contrasenha or not check_contra:
                return render_template('register.html', error='Las contraseñas son obligatorias')
            if contrasenha != check_contra:
                return render_template('register.html', error='Las contraseñas no coinciden')
            


            try:
                status = crear_directorio(crear_path_name(email))
                if not status:
                    return render_template('register.html', error='Internal Server Error')
                
            except Exception as e:
                return render_template('register.html', error='Internal Server Error')


    
            contrasenha_hash = generate_password_hash(contrasenha)
           
            try:
                usuario_dao.insert_user({'email':email, 'nombre':nombre, 'contrasenha_hash':contrasenha_hash, 'telefono':telefono})
                return redirect(url_for('login'))
            
            except Exception as e:
                return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
            

        return render_template('register.html')

    



    @login_check
    @app.route('/index', methods=['GET', 'POST'])
    def index():
        pass

