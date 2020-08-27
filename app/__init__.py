from flask import Flask
from app.settings.config import Ajustes, ConexionMail
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import logging
from logging.handlers import SMTPHandler
from flask_moment import Moment

app = Flask(__name__)
app.config.from_object(Ajustes)

bdd = SQLAlchemy(app)
migrar = Migrate(app,bdd)

moment = Moment(app)

login = LoginManager(app)
login.login_view = 'login' # 1.la funcion login es la que maneja los inicios de sesion
login.login_message = 'Por favor inicia sesión para acceder a esta página.'

from app import rutas, modelos, errores



if app.debug == False:
    if ConexionMail.MAIL_SERVER: # existe configuracion para MAIL-SERVER
        autenticacion = None
        if ConexionMail.MAIL_USERNAME or ConexionMail.MAIL_PASSWORD:
            autenticacion = (ConexionMail.MAIL_USERNAME, ConexionMail.MAIL_PASSWORD)
        seguridad = None
        if ConexionMail.MAIL_USE_TLS: # no hace falta pasarle el parámetro de seguridad
            seguridad = ()
        enviar_email = SMTPHandler(
            mailhost = (ConexionMail.MAIL_SERVER, ConexionMail.MAIL_PORT),
            fromaddr = 'no-reply@' + ConexionMail.MAIL_SERVER,
            toaddrs = ConexionMail.ADMINS, subject='Fallo encontrado en nuestro Blog',
            credentials= autenticacion, secure=seguridad
        )
        enviar_email.setLevel(logging.ERROR) # solo los errores en los formularios
        app.logger.addHandler(enviar_email)


if __name__ == "__main__":
    
    app.run(host='0.0.0.0', port=80)
