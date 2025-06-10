# Em app/main/routes.py

from flask import render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from . import main_bp
from app import db
from app.models import Produto, Usuario
from .forms import ProdutoForm
from app.decorators import permission_required
from sqlalchemy import func
from .forms import ProdutoForm, AdminUsuarioForm
from .forms import AlterarFuncaoForm

def verificar_permissao(produto):
    """Verifica se o usuário atual tem permissão para modificar o produto."""
    if produto.usuario_id != current_user.id and current_user.funcao.nome != 'Admin':
        # Cria a mensagem de erro
        flash('Você não tem permissão para alterar este produto.', 'danger')
        # Retorna False indicando que a permissão foi negada
        return False
    # Se a permissão for concedida, retorna True
    return True

@main_bp.route('/produto/adicionar', methods=['GET', 'POST'])
@login_required # Garante que apenas usuários logados possam adicionar produtos
@permission_required('Admin', 'Gerente')
def adicionar_produto():
    form = ProdutoForm()
    if form.validate_on_submit():
        # Cria uma nova instância do Produto com os dados do formulário
        novo_produto = Produto(
            nome=form.nome.data,
            descricao=form.descricao.data,
            preco=form.preco.data,
            quantidade=form.quantidade.data,
            # Associa o produto ao usuário atualmente logado
            usuario_id=current_user.id 
        )
        db.session.add(novo_produto)
        db.session.commit()
        flash('Produto adicionado com sucesso!', 'success')
        # Redireciona para a página que listará os produtos (nosso próximo passo)
        return redirect(url_for('main.listar_produtos'))
        
    # Se a requisição for GET, apenas exibe o formulário
    return render_template('adicionar_produto.html', 
                           title='Adicionar Novo Produto', 
                           form=form)


@main_bp.route('/produtos')
@login_required # Apenas usuários logados podem ver os produtos
def listar_produtos():
    page = request.args.get('page', 1, type=int)
    # 1. Pega o termo de busca da URL. O padrão é uma string vazia.
    termo_busca = request.args.get('termo_busca', '')

    # 2. Começa com uma consulta base
    query_base = Produto.query

    # 3. Se um termo de busca for fornecido, adiciona um filtro à consulta
    if termo_busca:
        # ilike() faz uma busca case-insensitive (não diferencia maiúsculas de minúsculas)
        # os '%' são wildcards, buscando qualquer produto que contenha o termo
        query_base = query_base.filter(Produto.nome.ilike(f'%{termo_busca}%'))

    # 4. Aplica a ordenação e a paginação na consulta final (seja ela filtrada ou não)
    pagination = query_base.order_by(Produto.nome.asc()).paginate(
        page=page, per_page=5, error_out=False
    )
    produtos = pagination.items
    
    return render_template('listar_produtos.html', 
                           produtos=produtos, 
                           title='Lista de Produtos',
                           pagination=pagination,
                           # 5. Envia o termo de busca de volta para o template
                           termo_busca=termo_busca)

@main_bp.route('/produto/editar/<int:produto_id>', methods=['GET', 'POST'])
@login_required
def editar_produto(produto_id):
    # Busca o produto no banco pelo ID fornecido na URL.
    # get_or_404 é uma função útil que retorna o objeto ou um erro 404 (Not Found) se não existir.
    produto = Produto.query.get_or_404(produto_id)
    if not verificar_permissao(produto):
        return redirect(url_for('main.listar_produtos')) 
    # Passamos o objeto 'produto' para o formulário.
    # O WTForms inteligentemente pré-preenche os campos com os dados do objeto.
    form = ProdutoForm(obj=produto)

    if form.validate_on_submit():
        # Pega os dados do formulário enviado e os usa para atualizar o objeto 'produto'
        form.populate_obj(produto)
        db.session.commit() # Salva as alterações no banco
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('main.listar_produtos'))
    
    # Se for uma requisição GET, renderiza o template com os dados do produto.
    return render_template('editar_produto.html', 
                           title=f'Editar Produto: {produto.nome}', 
                           form=form,
                           produto=produto)



@main_bp.route('/produto/deletar/<int:produto_id>', methods=['POST'])
@login_required
def deletar_produto(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    if not verificar_permissao(produto):
        return redirect(url_for('main.listar_produtos'))
    # Verificação de Permissão: O usuário só pode deletar seus próprios produtos
    # A menos que ele seja um 'Admin'.

    db.session.delete(produto)
    db.session.commit()
    flash('Produto deletado com sucesso.', 'success')
    return redirect(url_for('main.listar_produtos'))


@main_bp.route('/home')
@main_bp.route('/')
@login_required
def home():
    # --- LÓGICA DO NOVO DASHBOARD ---

    # 1. Contar o número total de produtos distintos
    total_produtos_distintos = db.session.query(func.count(Produto.id)).scalar()

    # 2. Somar a quantidade total de itens no estoque
    total_itens_estoque = db.session.query(func.sum(Produto.quantidade)).scalar() or 0

    # 3. Calcular o valor total do estoque (soma de preço * quantidade)
    valor_total_estoque = db.session.query(func.sum(Produto.preco * Produto.quantidade)).scalar() or 0
    
    # 4. Contar o número total de usuários cadastrados
    total_usuarios = db.session.query(func.count(Usuario.id)).scalar()

    # 5. Encontrar os 5 produtos com menor quantidade em estoque
    produtos_baixo_estoque = Produto.query.order_by(Produto.quantidade.asc()).limit(5).all()

    # 6. Enviar todas as estatísticas para o template
    return render_template('home.html', 
                           title='Dashboard',
                           total_produtos_distintos=total_produtos_distintos,
                           total_itens_estoque=total_itens_estoque,
                           valor_total_estoque=valor_total_estoque,
                           total_usuarios=total_usuarios,
                           produtos_baixo_estoque=produtos_baixo_estoque)

@main_bp.route('/admin/usuarios')
@login_required
@permission_required('Admin') # Apenas Admins podem acessar
def listar_usuarios():
    # Busca todos os usuários, ordenados por nome
    # O .options(db.joinedload(Usuario.funcao)) é uma otimização para carregar
    # a função de cada usuário de forma mais eficiente, evitando múltiplas queries.
    usuarios = Usuario.query.order_by(Usuario.nome).options(db.joinedload(Usuario.funcao)).all()
    form_alterar_funcao = AlterarFuncaoForm()
    return render_template('admin/listar_usuarios.html', 
                           usuarios=usuarios, 
                           title="Gerenciamento de Usuários",form_alterar_funcao=form_alterar_funcao)

@main_bp.route('/admin/usuarios/adicionar', methods=['GET', 'POST'])
@login_required
@permission_required('Admin')
def adicionar_usuario_admin():
    form = AdminUsuarioForm()
    if form.validate_on_submit():
        novo_usuario = Usuario(
            nome=form.nome.data,
            email=form.email.data,
            # O 'form.funcao.data' já nos dá o objeto Funcao completo
            funcao=form.funcao.data
        )
        novo_usuario.set_senha(form.senha.data)
        db.session.add(novo_usuario)
        db.session.commit()
        flash('Novo usuário cadastrado com sucesso!', 'success')
        return redirect(url_for('main.listar_usuarios'))
        
    return render_template('admin/adicionar_usuario.html',
                           title='Adicionar Novo Usuário',
                           form=form)
@main_bp.route('/admin/usuarios/alterar_funcao/<int:usuario_id>', methods=['GET', 'POST'])
@login_required
@permission_required('Admin')
def alterar_funcao_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    form = AlterarFuncaoForm()
    
    # A linha foi removida. O resto da lógica continua igual.
    if form.validate_on_submit():
        usuario.funcao = form.funcao.data
        db.session.commit()
        flash(f'A função de {usuario.nome} foi atualizada com sucesso!', 'success')
        return redirect(url_for('main.listar_usuarios'))

    # Pré-selecionamos a função atual do usuário no carregamento da página
    form.funcao.data = usuario.funcao
    
    return render_template('admin/alterar_funcao.html',
                           title='Alterar Função',
                           form=form,
                           usuario=usuario)