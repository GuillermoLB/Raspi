from app import app, bdd
from app.modelos import Usuario, Domotica

@app.shell_context_processor
def make_shell_context():
  return {'bdd':bdd,'Usuario':Usuario, 'Domotica':Domotica}
