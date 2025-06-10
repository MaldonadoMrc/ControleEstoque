from functools import wraps
from flask import flash, redirect, url_for # 1. Adicione flash, redirect, url_for
from flask_login import current_user

def permission_required(*permissions):
    """
    Verifica se o usuário logado tem pelo menos uma das permissões exigidas.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(current_user, 'funcao') or not hasattr(current_user.funcao, 'nome'):
                flash('Você não tem permissão para acessar esta página.', 'danger')
                return redirect(url_for('main.listar_produtos'))

            if current_user.funcao.nome not in permissions:
                flash(f"Acesso Restrito!\nÉ necessário ter uma das seguintes funções: {', '.join(permissions)}.", 'warning')
                return redirect(url_for('main.listar_produtos')) # Redireciona para uma página segura
            return f(*args, **kwargs)
        return decorated_function
    return decorator