from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange
from app.auth.forms import RegistroForm
from wtforms_sqlalchemy.fields import QuerySelectField
from app.models import Funcao

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
    descricao = TextAreaField('Descrição', validators=[Length(max=500, message='A descrição não pode exceder 500 caracteres.')])
    preco = FloatField('Preço', validators=[DataRequired(message='O preço é obrigatório.'), NumberRange(min=0, message='O preço deve ser um valor positivo.')])
    quantidade = IntegerField('Quantidade', validators=[DataRequired(message='A quantidade é obrigatória.'), NumberRange(min=0, message='A quantidade não pode ser negativa.')])
    enviar = SubmitField('Salvar Produto')

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
