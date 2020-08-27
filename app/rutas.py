from flask import Flask, render_template, Response
from app import app, bdd
from app.formularios import FormInicio, FormRegistro, EditarPerfil, FormActivar, FormDesactivar, FormShutdown, FormSubir
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from app.modelos import Usuario, Domotica
from werkzeug.urls import url_parse # para el next
from datetime import datetime
from app.formularios import RecuperarContraseña
from app.enviar_email import contraseña_olvidada
from app.formularios import ResetearContraseña
from werkzeug.utils import secure_filename
import os
import subprocess

import RPi.GPIO as GPIO
import time

from app.camera_pi import Camera


@app.route('/', methods=['GET','POST'])
@app.route('/index', methods=['GET','POST'])
@login_required # llamar a /login?next=next/index en lugar de a /login 

def index():
    form = FormShutdown()
    if form.validate_on_submit():
        subprocess.run(['sudo shutdown now'],shell=True)
        return 0
    return render_template('index.html', titulo='Página de inicio', form = form, usuario = current_user)


@app.route('/streaming', methods=['GET','POST'])
@login_required
def streaming():
    #GPIO.output(accessPin, True)
    servo1 = Domotica.query.filter_by(nombre="servo1").first() # comprobar cómo quedó

    if servo1.activado:
        form = FormDesactivar()
    else:
        form = FormActivar()

    if form.validate_on_submit():

        if (servo1.activado):
            servo1.activado = 0
        else:
            servo1.activado = 1
        bdd.session.commit()
        return redirect(url_for('streaming'))
        #return render_template('streaming.html',servo1=servo1, form=form, post = 1)


    
    return render_template('streaming.html',servo1=servo1, form=form, post = 0)
    

@app.route('/activar_paneo')
@login_required
def activar_paneo():
    #GPIO.output(accessPin, True)
    servo = Domotica.query.filter_by(id=1).first()
    servo.paneo = 1
    bdd.session.commit()
    return render_template('streaming.html',servo=servo)

@app.route('/desactivar_paneo')
@login_required
def desactivar_paneo():
    #GPIO.output(accessPin, True)
    servo = Domotica.query.filter_by(id=1).first()
    servo.paneo = 0
    bdd.session.commit()
    return render_template('streaming.html',servo=servo)


@app.route('/archivos')
@login_required
def archivos():
    form = FormSubir()
    return render_template('archivos.html',form = form)


@app.route('/camera')
def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/login', methods=['GET', 'POST'])
def login(): # 2. esta definida en init como la funcion login, es lo primero que se ejecuta
  if current_user.is_authenticated: # para que no se identifique dos veces el msimo usuario
      return redirect(url_for('index'))
  form = FormInicio()
  
  if(form.validate_on_submit()): # true cuando el usuario le da al boton (POST), false cuando es el primer GET
      usuario = Usuario.query.filter_by(username=form.nombre.data).first()
      if usuario:
            if usuario.verif_clave(form.contraseña.data):
                login_user(usuario, remember=form.recordar.data) # 3. se registra el usuario como el usuario logeado (guarda el id en login, usuario esta definido como usermixin), y pasamos al cargador en modelos.py
                next_page = request.args.get('next')
                if not next_page or url_parse(next_page).netloc != '': # el segundo argumento evita que next_page tenga direcciones absolutas a otros sitios que puedan ser maliciosos, solo relativas
                    next_page = url_for('index')
                return redirect(next_page)

      flash("Usuario o contraseña no válido.")

      
  return render_template('iniciar_sesion.html', form=form) #GET, por lo que form.validate_on_submit() es False, return de cuando se le da a iniciar sesion

@app.route('/logout')
def logout():
   logout_user()
   return redirect(url_for('index'))


@app.route('/registro', methods=['GET','POST']) # get y post para vistas con formularios
@login_required
def registro():
  #if current_user.is_authenticated:
    #return redirect(url_for('index'))
  form = FormRegistro()
  if form.validate_on_submit(): # boton dentro de registro
    usuario = Usuario(username=form.username.data, email=form.email.data)
    usuario.def_clave(form.contraseña.data)
    bdd.session.add(usuario)
    bdd.session.commit()
    flash('Usuario registrado correctamente, ahora puedes iniciar sesión.')
    return redirect(url_for('login'))
  return render_template('registro.html', titulo='Registro', form=form)


@app.route('/usuario/<username>') # el username de la ruta sera el argumento de la funcion
@login_required
def perfil_usuario(username):
    usuario = Usuario.query.filter_by(username=username).first_or_404()
    return render_template('usuarios.html', usuario=usuario)

@app.route('/editar_perfil', methods=['GET', 'POST'])
@login_required
def editar_perfil():
    form = EditarPerfil(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.sobre_mi = form.sobre_mi.data
        bdd.session.commit() # current_user ya está ligado a la bdd porque ha sido cargado, por lo que no hace flata el add
        flash('Tus cambios han sido guardados correctamente')
        return redirect(url_for('editar_perfil'))
    elif request.method == 'GET': # primera llamada al formulario
        form.username.data = current_user.username
        form.sobre_mi.data = current_user.sobre_mi
    return render_template('editar_perfil.html', titulo='Editar Perfil', form=form) # vuelve a llamar a la misma función



@app.before_request
def ultima_sesion():
    if current_user.is_authenticated:
        current_user.ultima_sesion = datetime.utcnow()
        bdd.session.commit()


@app.route('/recuperar_contraseña', methods=['GET', 'POST'])
def recuperar_contraseña():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RecuperarContraseña()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form.email.data).first()
        if usuario is None:
            flash('No existe ningún usuario con este correo electrónico en nuestros registros') # estos mensajes se muestran en base.html
            form.email.data = "" # limpia el formulario
            redirect(url_for('recuperar_contraseña'))
        if usuario is not None:
            contraseña_olvidada(usuario)
            flash('Chequea tu email para completar la recuperación de contraseña')
            return redirect(url_for('login'))
    return render_template('recuperar_contraseña.html', titulo='Recuperar contraseña', form=form)


@app.route('/resetear_contraseña/<token>', methods= ['GET', 'POST']) # le pasa el token por la 
def resetear_contraseña(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    usuario = Usuario.verificar_token_contraseña(token) # devuelve el usuario al que corresponde el token. Podemos utilizar Usuario en lugar de currenmt_user porque el metodo esta definido como static
    if not usuario:
        return redirect(url_for('index'))
    form = ResetearContraseña()
    if form.validate_on_submit():
        usuario.def_clave(form.contraseña.data)
        bdd.session.commit()
        flash('Tu contraseña ha sido cambiada')
        return redirect(url_for('login'))
    return render_template('resetear_contraseña.html', form=form)
