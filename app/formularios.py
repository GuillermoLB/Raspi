from flask_wtf import FlaskForm

from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, FileField

from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length

from app.modelos import Usuario # para buscar si ya existe el usuario

from markupsafe import Markup

class EditarPerfil(FlaskForm): # hereda de FlaskFOrm
    
    username = StringField('Usuario', validators=[DataRequired()])
    
    sobre_mi = TextAreaField('Sobre mi', validators=[Length(min=0, max=140)])
    
    submit = SubmitField('Enviar')

    def __init__(self, usuarioActual, *args, **kwargs):
        super(EditarPerfil, self).__init__(*args, **kwargs) # si esto no está, salta la excepción al intentar editar el perfil
        self.usuarioActual = usuarioActual

    def validate_username(self, username):
        if username.data != self.usuarioActual:
            usuario = Usuario.query.filter_by(username=self.username.data).first()
            if usuario is not None:
                raise ValidationError('El nombre de usuario ya existe, por favor intenta con otro.')

class FormInicio(FlaskForm):

    nombre = StringField('Usuario', validators=[DataRequired(message='Introduce un nombre de usuario.')])

    contraseña = PasswordField('Contraseña', validators=[DataRequired(message='Introduce una contraseña.')])

    recordar = BooleanField('Recordar Usuario')

    enviar = SubmitField('Iniciar Sesión')
    
class FormRegistro(FlaskForm):
    
    username = StringField('Nombre de Usuario', validators=[DataRequired()])
    
    email = StringField('Email', validators=[DataRequired(), Email()])
    
    contraseña = PasswordField('Contraseña', validators=[DataRequired()])
    
    contraseña2 = PasswordField('Repita su Contraseña', validators=[DataRequired(),EqualTo('contraseña', 'Las contraseñas no coinciden')])
    
    submit = SubmitField('Registrar')

    def validate_username(self, username):
        usuario = Usuario.query.filter_by(username=self.username.data).first()
        if usuario is not None:
            raise ValidationError('El nombre de usuario ya existe.') #errores del tipo validationError como los de campo vacio


    def validate_email(self, email):
        usuario = Usuario.query.filter_by(email=self.email.data).first()
        if usuario is not None:
            raise ValidationError('Ya existe un usuario con ese email.') #errores del tipo validationError como los de campo vacio

class RecuperarContraseña(FlaskForm):
    email = StringField('Email', validators=[DataRequired(message='Introduce una dirección de email.'), Email()])
    submit = SubmitField('Recuperar contraseña')

class ResetearContraseña(FlaskForm):
    contraseña = PasswordField('Contraseña', validators=[DataRequired()])
    contraseña2 = PasswordField(
        'Repetir contraseña', validators=[DataRequired(), EqualTo('contraseña')])
    submit = SubmitField('Solicitar cambio de contraseña')


class FormActivar(FlaskForm):
    submit = SubmitField('Activar paneo')

class FormDesactivar(FlaskForm):
    submit = SubmitField('Desactivar paneo')

class FormShutdown(FlaskForm):
    submit = SubmitField('Shutdown')

class FormSubir(FlaskForm):
    archivo = FileField('archivo')
    submit = SubmitField('Postear')