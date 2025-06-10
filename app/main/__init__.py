# Em app/main/__init__.py
from flask import Blueprint

# Define o blueprint 'main'
main_bp = Blueprint('main', __name__, template_folder='templates')

# Importa as rotas no final para evitar importações circulares
from . import routes

