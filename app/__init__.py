from flask import Flask
from dotenv import load_dotenv
import os
import click
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager


db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # Configurações
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Conecta o 'db' com o 'app'
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import Usuario
        return Usuario.query.get(int(user_id))

    # Importa os blueprints DEPOIS de inicializar o db
    from .auth.routes import auth_bp

    from .main import main_bp
    app.register_blueprint(main_bp)

    # Registra os blueprints
    app.register_blueprint(auth_bp)

    # Cria as tabelas e as funções iniciais
   
    @app.cli.command("init-db")
    def init_db_command():
        """Cria as tabelas do banco e semeia as funções iniciais."""
        # Precisamos importar os modelos aqui
        from app.models import Funcao 
        db.create_all()

        funcoes_iniciais = ['Admin', 'Gerente', 'Visualizador', 'Usuario'] # Nomes com maiúscula por convenção
        for nome_funcao in funcoes_iniciais:
            if not Funcao.query.filter_by(nome=nome_funcao).first():
                nova_funcao = Funcao(nome=nome_funcao)
                db.session.add(nova_funcao)
        
        db.session.commit()
        click.echo("Banco de dados inicializado com sucesso.")
    return app