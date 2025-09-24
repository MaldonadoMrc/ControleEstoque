
from app.db_file import db

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

class Estado(db.Model):
    __tablename__ = 'estados'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True)
    sigla = db.Column(db.String(2), nullable=False, unique=True)
    def __repr__(self):
        return f'<Estado {self.sigla}>'

class Fornecedor(db.Model):
    __tablename__ = 'fornecedores'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), unique=True, nullable=False)
    contato_nome = db.Column(db.String(100))
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    rua = db.Column(db.String(200))
    numero = db.Column(db.String(20))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    cep = db.Column(db.String(10))
    estado_id = db.Column(db.Integer, db.ForeignKey('estados.id'))
    estado = db.relationship('Estado', backref=db.backref('fornecedores', lazy=True))
    def __repr__(self):
        return f'<Fornecedor {self.nome}>'

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
    funcao_id = db.Column(db.Integer, db.ForeignKey('funcoes.id'), nullable=False)
    funcao = db.relationship('Funcao', backref=db.backref('usuarios', lazy=True))
    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha) 
    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)
    def __repr__(self):
        return f'<Usuario {self.nome}>'
    
class Produto(db.Model):
    __tablename__ = 'produtos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text, nullable=True)
    preco = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'), nullable=False)
    fornecedor = db.relationship('Fornecedor', backref=db.backref('produtos', lazy=True))
    def __repr__(self):
        return f'<Produto {self.nome}>'

class MovimentacaoEstoque(db.Model):
    __tablename__ = 'movimentacoes_estoque'
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=False)
    produto = db.relationship('Produto', backref=db.backref('movimentacoes', lazy='dynamic', cascade="all, delete-orphan"))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    usuario = db.relationship('Usuario', backref=db.backref('movimentacoes', lazy=True))
    tipo = db.Column(db.String(10), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    motivo = db.Column(db.String(255), nullable=True)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    def __repr__(self):
        return f'<Movimentacao {self.id}: {self.tipo} de {self.quantidade} para {self.produto.nome}>'
    
class Cliente(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)

    # Endereço
    rua = db.Column(db.String(200))
    numero = db.Column(db.String(20))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    cep = db.Column(db.String(10))
    # CORREÇÃO: A coluna deve ser minúscula para seguir o padrão (estado_id)
    estado_id = db.Column(db.Integer, db.ForeignKey('estados.id')) 
    estado = db.relationship('Estado', backref=db.backref('clientes', lazy=True))

    # AJUSTE: Usando back_populates para um relacionamento mais claro com OrdemServico
    ordens_servico = db.relationship('OrdemServico', back_populates='cliente', lazy='dynamic')

    def __repr__(self):
        return f'<Cliente {self.nome}>'
    

class OrdemServico(db.Model):
    __tablename__ = 'ordens_servico'
    id = db.Column(db.Integer, primary_key=True)
    
    # CORREÇÃO: Sintaxe correta para definir colunas
    data_abertura = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_conclusao = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), default='Aberta', nullable=False)

    # --- Chaves Estrangeiras ---
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    # ADIÇÃO: Faltava a chave estrangeira para o técnico (usuário)
    tecnico_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    # --- Detalhes do Serviço ---
    equipamento = db.Column(db.String(100), nullable=False)
    descricao_problema = db.Column(db.Text, nullable=False)
    servico_executado = db.Column(db.Text, nullable=True) # Alterado de 'solucao' para combinar com o de baixo

    # --- Valores ---
    valor_servico = db.Column(db.Float, default=0.0)
    valor_pecas = db.Column(db.Float, default=0.0)
    valor_total = db.Column(db.Float, default=0.0)
    
    # --- Relacionamentos Corrigidos ---
    # AJUSTE: Usando back_populates e removendo a duplicata
    cliente = db.relationship('Cliente', back_populates='ordens_servico')
    # AJUSTE: Relacionamento com o técnico (Usuario)
    tecnico = db.relationship('Usuario', backref='ordens_servico_atribuidas')

    def __repr__(self):
        return f'<OrdemServico id={self.id}>'
    
class Venda(db.Model):
    __tablename__ = 'vendas'
    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    valor_total = db.Column(db.Float, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    usuario = db.relationship('Usuario', backref=db.backref('vendas', lazy=True))

class VendaItem(db.Model):
    __tablename__ = 'venda_itens'
    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey('vendas.id'), nullable=False)
    venda = db.relationship('Venda', backref=db.backref('itens', lazy=True))
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=False)
    produto = db.relationship('Produto')
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False) # Preço no momento da venda