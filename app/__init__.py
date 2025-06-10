from flask import Flask
from dotenv import load_dotenv
import os
import click
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
# Importamos o 'db' do nosso arquivo neutro para evitar importações circulares.
from .db_file import db
# Novas importações para o nosso filtro de hora local.
from datetime import datetime
import pytz

def create_app():
    """
    Cria e configura uma instância da aplicação Flask.
    Este é o padrão Application Factory.
    """
    app = Flask(__name__)

    # Configurações da aplicação, buscando do .env ou usando um valor padrão.
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'uma-chave-secreta-forte-para-desenvolvimento')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///meu_banco.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializa o banco de dados com a nossa aplicação.
    db.init_app(app)

    # Configura o gerenciador de login.
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Por favor, faça o login para acessar esta página."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        # A importação do modelo é feita aqui dentro para garantir
        # que a aplicação já esteja totalmente configurada.
        from app.models import Usuario
        return Usuario.query.get(int(user_id))

    # --- Filtro de Template Customizado para Hora Local ---
    @app.template_filter('hora_local')
    def format_datetime_local(utc_datetime):
        """Converte uma data/hora UTC para o fuso horário de Campo Grande."""
        if utc_datetime is None:
            return ""
        # Define o fuso horário de destino
        fuso_horario_local = pytz.timezone('America/Campo_Grande')
        # Garante que a data de entrada seja tratada como UTC e a converte
        horario_local = utc_datetime.replace(tzinfo=pytz.utc).astimezone(fuso_horario_local)
        return horario_local.strftime('%d/%m/%Y %H:%M:%S')

    # Importa e registra os Blueprints (conjuntos de rotas)
    # A importação é feita aqui para evitar dependências circulares.
    from .auth.routes import auth_bp
    from .main import main_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    # --- Comando de Linha de Comando para Inicializar o Banco de Dados ---
    @app.cli.command("init-db")
    def init_db_command():
        """Cria as tabelas do banco e semeia os dados iniciais (Funções e Estados)."""
        from app.models import Funcao, Estado
        
        db.create_all()

        # Seed de Funções
        funcoes_iniciais = ['Admin', 'Gerente', 'Visualizador', 'Usuario']
        for nome_funcao in funcoes_iniciais:
            if not Funcao.query.filter_by(nome=nome_funcao).first():
                nova_funcao = Funcao(nome=nome_funcao)
                db.session.add(nova_funcao)
        
        # Seed de Estados
        estados_iniciais = [
            {'nome': 'Acre', 'sigla': 'AC'}, {'nome': 'Alagoas', 'sigla': 'AL'},
            {'nome': 'Amapá', 'sigla': 'AP'}, {'nome': 'Amazonas', 'sigla': 'AM'},
            {'nome': 'Bahia', 'sigla': 'BA'}, {'nome': 'Ceará', 'sigla': 'CE'},
            {'nome': 'Distrito Federal', 'sigla': 'DF'}, {'nome': 'Espírito Santo', 'sigla': 'ES'},
            {'nome': 'Goiás', 'sigla': 'GO'}, {'nome': 'Maranhão', 'sigla': 'MA'},
            {'nome': 'Mato Grosso', 'sigla': 'MT'}, {'nome': 'Mato Grosso do Sul', 'sigla': 'MS'},
            {'nome': 'Minas Gerais', 'sigla': 'MG'}, {'nome': 'Pará', 'sigla': 'PA'},
            {'nome': 'Paraíba', 'sigla': 'PB'}, {'nome': 'Paraná', 'sigla': 'PR'},
            {'nome': 'Pernambuco', 'sigla': 'PE'}, {'nome': 'Piauí', 'sigla': 'PI'},
            {'nome': 'Rio de Janeiro', 'sigla': 'RJ'}, {'nome': 'Rio Grande do Norte', 'sigla': 'RN'},
            {'nome': 'Rio Grande do Sul', 'sigla': 'RS'}, {'nome': 'Rondônia', 'sigla': 'RO'},
            {'nome': 'Roraima', 'sigla': 'RR'}, {'nome': 'Santa Catarina', 'sigla': 'SC'},
            {'nome': 'São Paulo', 'sigla': 'SP'}, {'nome': 'Sergipe', 'sigla': 'SE'},
            {'nome': 'Tocantins', 'sigla': 'TO'}
        ]
        
        for est_data in estados_iniciais:
            if not Estado.query.filter_by(sigla=est_data['sigla']).first():
                novo_estado = Estado(nome=est_data['nome'], sigla=est_data['sigla'])
                db.session.add(novo_estado)

        db.session.commit()
        click.echo("Banco de dados inicializado com sucesso (Funções e Estados criados).")

    return app
