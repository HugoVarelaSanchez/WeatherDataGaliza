from flask import Flask, flash, session, redirect, url_for, jsonify, request, render_template, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import json, secrets, os
from dotenv import load_dotenv
from dao import *
from dao.db_mongoDAO import BaseMongoDAO
from utils import *
from services import GeminiFileProcessor

load_dotenv()


def fapp():

    
    app = Flask(__name__, template_folder='web/templates', static_folder='web/static')

    app.config['DEBUG'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_NAME'] = 'hackudc25'
    app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))

    usuario_dao = usuarioDAO()
    token_dao = tokenDAO()
    base_dao = BaseDAO()
    gemini_processor = GeminiFileProcessor()

    base_dao.init_connection_pool()
    BaseMongoDAO.init_connection()
    documentos_dao = DocumentosDAO()

    def login_check():
        def login_check_real(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
 
                try: 
                    # Si no hay un email guardado en la sesion, comprobamos el token
                    if 'user_email' not in session: 
        
                        auth_token = request.cookies.get('login_token')


                        if not auth_token:
                            return redirect(url_for('login'))

                        if auth_token:

                            try:
                                login_data = json.loads(auth_token)
                                n_token = login_data.get('token')
                                n_email = login_data.get('email')

                            except (json.JSONDecodeError, TypeError):
                                return redirect(url_for('login'))
                        
                            
                            check = token_dao.check_token(n_email, n_token)


                            #Compruebas si ese token es valido con ese email
                            if check:                        #Inicias sesion


                                usuario_activo = usuario_dao.get_user(n_email)

                                session_data = {
                                    'user_email': n_email,
                                    'user_name': usuario_activo[0]['nombre'],
                                    'user_phone': usuario_activo[0]['telefono'],
                                }

                                session.update(session_data)

                                token = secrets.token_hex(32)
                                token_dao.update_token(token, n_email)

                                # Ejecutar el endpoint real y añadir la cookie rotada
                                resp = make_response(f(*args, **kwargs))
                                resp.set_cookie(
                                    'login_token',
                                    json.dumps({'token': token, 'email': n_email}),
                                    max_age=2592000,
                                    httponly=True,
                                    secure=True
                                )

                                return resp

                            # Token inválido: redirigir a login
                            return redirect(url_for('login'))
                        



                    #Si hay un email guardado en la sesion
                    #Verificamos que el usuario existe en la BD
                    else:
                        user = usuario_dao.get_user(session['user_email'])

                        #Si no esta guardado ese email, error
                        if not user:
                            flash(f'No existe ningun usuario con el email: {session["user_email"]}', 'error')
                            session.clear()
                            return redirect(url_for('login'))
                    

                except Exception as e:
                        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

                return f(*args, **kwargs)
            decorated_function.__name__ = f.__name__
            return decorated_function
        return login_check_real
            







    @app.route('/')
    @login_check()
    def root():
        return redirect(url_for('index'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():

        if request.method == 'POST': 
            
            email = request.form.get('email')
            
            existencia, checkeo = usuario_dao.check_user_exist(email), False


            if existencia:
                checkeo = usuario_dao.check_credenciales(email, request.form.get('password'))

            else: 
                return render_template('login.html', error='Usuario no registrado')

            if checkeo:
                usuario_activo = usuario_dao.get_user(email)

                session_data = {
                    'user_email': email,
                    'user_name': usuario_activo[0]['nombre'],
                    'user_phone': usuario_activo[0]['telefono'],
                    }
        
                session.update(session_data)

                if request.form.get('remember'):

                    token = secrets.token_hex(32)
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
            if user:
                return render_template('register.html', error='Este usuario ya esta registrado')



            nombre = request.form.get('nombre')
            if not nombre:
                return render_template('register.html', error='Debes anhadir un nombre de usuario')
            
            telefono = request.form.get('phone')
            if not telefono:
                telefono = None

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

    



    @app.route('/index', methods=['GET', 'POST'])
    @login_check()
    def index():
        return render_template('index.html')





    @app.route('/logout')
    def logout():
        session.clear()
        resp = redirect(url_for('login'))
        resp.delete_cookie('login_token')
        return resp


    # ============= File Processing Endpoints =============

    @app.route('/api/upload', methods=['POST'])
    @login_check()
    def upload_file():
        """
        Upload and process a file using Gemini AI
        Requires authentication
        """
        try:
            file = request.files.get('file')

            if not file or file.filename == '':
                return jsonify({'success': False, 'error': 'No file selected'}), 400

            # Determinar tipo para MongoDB
            mime = file.content_type
            if mime.startswith('image/'):
                tipo = 'imagen'
            elif mime.startswith('video/'):
                tipo = 'video'
            elif mime.startswith('audio/'):
                tipo = 'audio'
            else:
                tipo = 'documento'

            # Guardar el archivo en el directorio del usuario
            user_email = session['user_email']
            user_dir = crear_path_name(user_email)
            brutos_dir = os.path.join(user_dir, 'brutos')
            os.makedirs(brutos_dir, exist_ok=True)

            safe_name = secure_filename(file.filename) or 'archivo'
            file_path = os.path.join(brutos_dir, safe_name)
            file.save(file_path)

            # Procesar con Gemini desde la ruta guardada
            result = gemini_processor.process_file_from_path(file_path, mime, file.filename)

            # Persistir en MongoDB
            documentos_dao.insert({
                'email': user_email,
                'tipo': tipo,
                'path': file_path,
                'size': os.path.getsize(file_path),
                'mime_type': mime,
                'titulo': file.filename,
                'descripcion': (result.get('content') or '')[:500],
            })

            return jsonify({'success': True, **result})

        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        except Exception as e:
            return jsonify({'success': False, 'error': f'Processing failed: {str(e)}'}), 500


    @app.route('/api/url', methods=['POST'])
    @login_check()
    def parse_url():
        """
        Validate and save a URL
        Requires authentication
        """
        try:
            data = request.get_json() if request.is_json else request.form
            url = data.get('url')

            if not url:
                return jsonify({'success': False, 'error': 'No URL provided'}), 400

            if gemini_processor.validate_url(url):
                documentos_dao.insert({
                    'email': session['user_email'],
                    'tipo': 'enlace',
                    'url': url,
                    'titulo': url,
                })
                return jsonify({'success': True, 'valid': True, 'url': url})
            else:
                return jsonify({'success': False, 'error': 'Invalid URL format'}), 400

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500


    return app

app = fapp()

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)





