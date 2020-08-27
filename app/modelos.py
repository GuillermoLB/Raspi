from app import bdd, login
from datetime import datetime
from werkzeug.security import generate_password_hash as genph
from werkzeug.security import check_password_hash as checkph
from flask_login import UserMixin
from hashlib import md5 # para imagen de avatar

import jwt
from app import app
from time import time




class Usuario(UserMixin, bdd.Model): #UserMixin lo define como el usuario para autentificacion, añade los requerimientos para que sea la clase current_user de flask_login

  id = bdd.Column(bdd.Integer, primary_key=True) # este id se registra como el id de la sesion del usuario
  username = bdd.Column(bdd.String(64), index=True, unique=True)
  email = bdd.Column(bdd.String(120), index=True, unique=True)
  hash_clave = bdd.Column(bdd.String(128))
  sobre_mi = bdd.Column(bdd.String(140))
  ultima_sesion = bdd.Column(bdd.DateTime, default=datetime.utcnow)

  
  def obtener_token_contraseña(self, expiracion=600):
      return jwt.encode(
      {'recuperar_contraseña': self.id, 'expide': time() + expiracion},
      app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')


  @staticmethod
  def verificar_token_contraseña(token):
      try:
          id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['recuperar_contraseña']
      except:
          return
      return Usuario.query.get(id) # devuelve el usuario con la id del token


  def __repr__(self): #se ejecuta automáticamente cuando se llama a print

    return '<Usuario {}>'.format(self.username)

  def def_clave(self, clave): #generar la clave hash a partir del argumento clave
    self.hash_clave = genph(clave)
    
  def verif_clave(self, clave): #comparar la clave pasada como argumento con el hash del usuario
    return checkph(self.hash_clave, clave)

  def imagen_perfil(self, tamaño):
    codigo_hash = md5(self.email.lower().encode('utf-8')).hexdigest()
    return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(codigo_hash, tamaño)


class Domotica(bdd.Model):

  id = bdd.Column(bdd.Integer, primary_key=True)
  nombre = bdd.Column(bdd.String(64), index=True, unique=True)
  activado = bdd.Column(bdd.Integer)



@login.user_loader # 4. cuando un usuario se logea. login es la variable y dado que el user mixin es Uusario, la funcion carga el usuario entero a current_user y define las funciones requeridas sobre el
def cargar_usuario(id): # callback para hacer una consulta para devolver el usuaio completo a partir del id de la sesion
    return Usuario.query.get(int(id)) # lo usará la función del decorador, que cargará la base de datos de usuario a la sesion (current_user)
