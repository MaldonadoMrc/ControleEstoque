from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db

class Funcao(db.Model):
    __tablename__ = 'funcoes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(50),  unique=True, nullable=False)




class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)

    funcao_id = db.Column(db.Integer, db.ForeignKey('funcoes.id'), nullable=False) # Chave estrangeira para a tabela de funcoes
    funcao = db.relationship('Funcao', backref=db.backref('usuarios', lazy=True))
    def set_senha(self, senha):
        #Define a senha do usuario, gerandon um HASH seguro
        self.senha_hash = generate_password_hash(senha) 
    
    def verificar_senha(self, senha):
        #Verifica se a senha informada é igual a senha do usuario
        return check_password_hash(self.senha_hash, senha)
    
    def __repr__(self):
        return f'<Usuario {self.nome}'
    
class Produto(db.Model):
    __tablename__ = 'produtos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text, nullable=True)
    preco = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    
    # Criando a relação com a tabela 'usuarios'
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    def __repr__(self):
        return f'<Produto {self.nome}>'