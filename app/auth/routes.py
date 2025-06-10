from flask import Blueprint, render_template, redirect, url_for, flash
from app import db
from .forms import LoginForm, RegistroForm
from flask_login import login_user
from flask_login import login_user, logout_user, login_required, current_user
auth_bp = Blueprint('auth', __name__, template_folder='templates/auth', static_folder='static')
from app.models import Usuario, Funcao
main_bp = Blueprint('main', __name__, template_folder='templates/main', static_folder='static')
@auth_bp.route('/logout')
@login_required # Só permite acesso a usuários que estão logados
def logout():
    logout_user() # Invalida a sessão do usuário
    flash('Você foi desconectado com sucesso.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    form = RegistroForm()
    if form.validate_on_submit():
        # Cria um novo usuário com os dados do formulário
        funcao_padrao = Funcao.query.filter_by(nome='Admin').first()
        if not funcao_padrao:
            flash('Função padrão "Usuario" não encontrada. Por favor, crie uma função antes de registrar um usuário.', 'danger')
            return redirect(url_for('auth.registro'))
        
        novo_usuario = Usuario(nome=form.nome.data, email=form.email.data, funcao=funcao_padrao)
        novo_usuario.set_senha(form.senha.data)
        db.session.add(novo_usuario)
        db.session.commit()
        flash('Conta criada com sucesso!', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/registro.html', form=form, titulo='Registro de Usuário')

@auth_bp.route('/', methods=['GET', 'POST'])
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form.email.data).first()
        if usuario and usuario.verificar_senha(form.senha.data):
            login_user(usuario, remember=form.lembrar_me.data)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('main.home'))
        else:
            flash('Email ou senha inválidos. Tente novamente.', 'danger')
    return render_template('auth/login.html', form=form, titulo='Bem vindo ao Ypê Auto Peças')
            