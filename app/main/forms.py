from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Email, Optional
from app.auth.forms import RegistroForm
from wtforms_sqlalchemy.fields import QuerySelectField
from app.models import Funcao, Fornecedor, Estado, Cliente, Usuario
from sqlalchemy import func
from datetime import datetime
class FornecedorForm(FlaskForm):
    nome = StringField('Nome da Empresa', validators=[DataRequired()])
    contato_nome = StringField('Nome do Contato')
    email = StringField('E-mail', validators=[Optional(), Email()])
    telefone = StringField('Telefone')
    endereco = TextAreaField('Endereço')
    submit = SubmitField('Salvar Fornecedor')
    
def query_estados():
    return Estado.query.order_by(Estado.nome)

def query_fornecedores():
    return Fornecedor.query.order_by(Fornecedor.nome)

def query_funcoes():
    return Funcao.query

class AlterarFuncaoForm(FlaskForm):
    """Formulário para o admin alterar a função de um usuário dentro de um modal."""
    funcao = QuerySelectField('Nova Função',
                              query_factory=query_funcoes,
                              get_label='nome',
                              allow_blank=False,
                              validators=[DataRequired()])
    submit = SubmitField('Salvar Alterações')

class ProdutoForm(FlaskForm):
    nome = StringField('Nome do Produto', validators=[DataRequired(message='O nome do produto é obrigatório.')])
    fornecedor = QuerySelectField(
        'Fornecedor',
        query_factory=query_fornecedores,
        get_label='nome',
        allow_blank=False, # Não permite deixar em branco
        validators=[DataRequired(message="É obrigatório selecionar um fornecedor.")]
    )
    descricao = TextAreaField('Descrição', validators=[Length(max=500, message='A descrição não pode exceder 500 caracteres.')])
    preco = FloatField('Preço', validators=[DataRequired(message='O preço é obrigatório.'), NumberRange(min=0, message='O preço deve ser um valor positivo.')])
    quantidade = IntegerField('Quantidade', validators=[DataRequired(message='A quantidade é obrigatória.'), NumberRange(min=0, message='A quantidade não pode ser negativa.')])
    enviar = SubmitField('Salvar Produto')


class MovimentacaoForm(FlaskForm):
    """Formulário para registrar entrada ou saída de produtos."""
    quantidade = IntegerField(
        'Quantidade', 
        validators=[
            DataRequired(message="A quantidade é obrigatória."),
            NumberRange(min=1, message="A quantidade deve ser de pelo menos 1.")
        ]
    )
    motivo = StringField(
        'Motivo/Descrição',
        validators=[DataRequired(message="O motivo é obrigatório.")]
    )
    submit_entrada = SubmitField('Registrar Entrada')
    submit_saida = SubmitField('Registrar Saída')

class AdminUsuarioForm(RegistroForm):
    """
    Este formulário herda todos os campos (nome, email, senha, etc.)
    do RegistroForm e apenas adiciona o campo para selecionar a função.
    """
    # 5. Adicione o campo extra de Função
    funcao = QuerySelectField(
        'Função do Usuário',
        query_factory=query_funcoes,
        get_label='nome',
        allow_blank=False,
        validators=[DataRequired()]
    )
    # 6. Podemos sobrescrever o botão de submit para ter um texto diferente
    enviar = SubmitField('Cadastrar Novo Usuário')

class FornecedorForm(FlaskForm):
    nome = StringField('Nome da Empresa', validators=[DataRequired()])
    contato_nome = StringField('Nome do Contato')
    email = StringField('E-mail', validators=[Optional(), Email(message="E-mail inválido.")])
    telefone = StringField('Telefone')
    
    # --- NOVOS CAMPOS DE ENDEREÇO ---
    cep = StringField('CEP')
    rua = StringField('Rua / Logradouro')
    numero = StringField('Número')
    bairro = StringField('Bairro')
    cidade = StringField('Cidade')
    estado = QuerySelectField(
        'Estado',
        query_factory=query_estados,
        get_label='nome', # O que o usuário vê
        allow_blank=True, # Permite não selecionar um estado
        blank_text='-- Selecione um Estado --'
    )
    
    submit = SubmitField('Salvar Fornecedor')

def query_cliente():
    return Cliente.query.order_by(Cliente.nome)


def query_tecnicos():
    return Usuario.query.order_by(Usuario.nome)

class ClienteForm(FlaskForm):
    nome = StringField('Nome Completo', validators=[DataRequired()])
    telefone = StringField('Telefone')
    email = StringField('Email', validators=[Optional(), Email(message="E-mail inválido.")])
    cep = StringField('CEP')
    rua = StringField('Rua')
    numero = StringField('Numero')
    bairro = StringField ('Bairro')
    cidade = StringField('Cidade')
    estado = QuerySelectField (
        'Estado',
        query_factory=query_estados,
        get_label='nome',
        allow_blank=True,
        blank_text='-- Selecione um Estado --'

    )
    
    submit = SubmitField('Salvar Cliente')

# Em app/main/forms.py

# ... (outros forms) ...

class OrdemServicoForm(FlaskForm):
    """Formulário para adicionar e editar Ordens de Serviço."""
    cliente = QuerySelectField(
        'Cliente',
        query_factory=query_cliente,
        get_label='nome',
        allow_blank=False,
        validators=[DataRequired(message="É obrigatório selecionar um cliente.")]
    )
    tecnico = QuerySelectField(
        'Técnico Responsável',
        query_factory=query_tecnicos,
        get_label='nome',
        allow_blank=False,
        validators=[DataRequired(message="É obrigatório selecionar um técnico.")]
    )
    equipamento = StringField('Equipamento', validators=[DataRequired(message="O campo equipamento é obrigatório.")])
    
    # GARANTA QUE ESTE CAMPO ESTEJA EXATAMENTE ASSIM
    descricao_problema = TextAreaField('Descrição do Problema', validators=[DataRequired()])
    
    servico_executado = TextAreaField('Serviço Executado')
    
    status = StringField('Status', default='Aberta', validators=[DataRequired()])
    
    valor_servico = FloatField('Valor do Serviço (R$)', default=0.0, validators=[Optional(), NumberRange(min=0)])
    valor_pecas = FloatField('Valor das Peças (R$)', default=0.0, validators=[Optional(), NumberRange(min=0)])
    
    submit = SubmitField('Salvar Ordem de Serviço')




