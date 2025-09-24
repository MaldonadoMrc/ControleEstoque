from flask import render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from . import main_bp
from app import db
from app.models import Produto, Usuario, MovimentacaoEstoque, Fornecedor, Cliente, OrdemServico
from .forms import ProdutoForm
from app.decorators import permission_required
from sqlalchemy import func
from .forms import ProdutoForm, AdminUsuarioForm, AlterarFuncaoForm, MovimentacaoForm, FornecedorForm, ClienteForm, OrdemServicoForm
from flask import jsonify # Adicione jsonify
from .forms import VendaForm # Adicione VendaForm
from app.models import Venda, VendaItem # Adicione os novos models
import json # Adicione a biblioteca json




def verificar_permissao(produto):
    """Verifica se o usuário atual tem permissão para modificar o produto."""
    if produto.usuario_id != current_user.id and current_user.funcao.nome != 'Admin':
        flash('Você não tem permissão para alterar este produto.', 'danger')
        return False
    return True

@main_bp.route('/produto/adicionar', methods=['GET', 'POST'])
@login_required 
@permission_required('Admin', 'Gerente')
def adicionar_produto():
    form = ProdutoForm()
    if form.validate_on_submit():
        novo_produto = Produto(
            nome=form.nome.data,
            descricao=form.descricao.data,
            preco=form.preco.data,
            quantidade=form.quantidade.data,
            usuario_id=current_user.id,
            # Salvar o fornecedor selecionado no formulário
            fornecedor=form.fornecedor.data 
        )
        db.session.add(novo_produto)
        db.session.commit()
        flash('Produto adicionado com sucesso!', 'success')
        return redirect(url_for('main.listar_produtos'))
        
    return render_template('adicionar_produto.html', 
                           title='Adicionar Novo Produto', 
                           form=form)


@main_bp.route('/produtos')
@login_required
def listar_produtos():
    page = request.args.get('page', 1, type=int)
    termo_busca = request.args.get('termo_busca', '')
    query_base = Produto.query.options(db.joinedload(Produto.fornecedor))
    if termo_busca:
        query_base = query_base.filter(Produto.nome.ilike(f'%{termo_busca}%'))

    pagination = query_base.order_by(Produto.nome.asc()).paginate(
        page=page, per_page=5, error_out=False
    )
    produtos = pagination.items
    form_movimentacao = MovimentacaoForm()
    
    return render_template('listar_produtos.html', 
                           produtos=produtos, 
                           title='Lista de Produtos',
                           pagination=pagination,
                           termo_busca=termo_busca,
                           form_movimentacao=form_movimentacao)

@main_bp.route('/produto/editar/<int:produto_id>', methods=['GET', 'POST'])
@login_required
def editar_produto(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    if not verificar_permissao(produto):
        return redirect(url_for('main.listar_produtos')) 
    form = ProdutoForm(obj=produto)
    if form.validate_on_submit():
        form.populate_obj(produto)
        db.session.commit()
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('main.listar_produtos'))
    
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
    db.session.delete(produto)
    db.session.commit()
    flash('Produto deletado com sucesso.', 'success')
    return redirect(url_for('main.listar_produtos'))


@main_bp.route('/home')
@main_bp.route('/')
@login_required
def home():
    total_produtos_distintos = db.session.query(func.count(Produto.id)).scalar()
    total_itens_estoque = db.session.query(func.sum(Produto.quantidade)).scalar() or 0
    valor_total_estoque = db.session.query(func.sum(Produto.preco * Produto.quantidade)).scalar() or 0
    total_usuarios = db.session.query(func.count(Usuario.id)).scalar()
    produtos_baixo_estoque = Produto.query.order_by(Produto.quantidade.asc()).limit(5).all()

    return render_template('home.html', 
                           title='Dashboard',
                           total_produtos_distintos=total_produtos_distintos,
                           total_itens_estoque=total_itens_estoque,
                           valor_total_estoque=valor_total_estoque,
                           total_usuarios=total_usuarios,
                           produtos_baixo_estoque=produtos_baixo_estoque)

@main_bp.route('/admin/usuarios')
@login_required
@permission_required('Admin')
def listar_usuarios():
    usuarios = Usuario.query.order_by(Usuario.nome).options(db.joinedload(Usuario.funcao)).all()
    form_alterar_funcao = AlterarFuncaoForm()
    return render_template('admin/listar_usuarios.html', 
                           usuarios=usuarios, 
                           title="Gerenciamento de Usuários",
                           form_alterar_funcao=form_alterar_funcao)

@main_bp.route('/admin/usuarios/adicionar', methods=['GET', 'POST'])
@login_required
@permission_required('Admin')
def adicionar_usuario_admin():
    form = AdminUsuarioForm()
    if form.validate_on_submit():
        novo_usuario = Usuario(
            nome=form.nome.data,
            email=form.email.data,
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



@main_bp.route('/admin/usuarios/alterar_funcao/<int:usuario_id>', methods=['POST'])
@login_required
@permission_required('Admin')
def alterar_funcao_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    form = AlterarFuncaoForm()
    
    if form.validate_on_submit():
        usuario.funcao = form.funcao.data
        db.session.commit()
        flash(f'A função de {usuario.nome} foi atualizada com sucesso!', 'success')
        return redirect(url_for('main.listar_usuarios'))

    
    form.funcao.data = usuario.funcao
    return render_template('admin/listar_usuarios.html',
                           form_alterar_funcao=form)


@main_bp.route('/produto/<int:produto_id>/movimentar', methods=['POST'])
@login_required
@permission_required('Admin', 'Gerente')
def movimentar_estoque(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    form = MovimentacaoForm()

    tipo_movimentacao = 'Entrada' if form.submit_entrada.data else 'Saída'

    if form.validate_on_submit():
        quantidade_mov = form.quantidade.data
        
        if tipo_movimentacao == 'Saída' and produto.quantidade < quantidade_mov:
            flash(f'Não há estoque suficiente para a saída. Estoque atual: {produto.quantidade}.', 'danger')
            return redirect(url_for('main.listar_produtos'))

        nova_movimentacao = MovimentacaoEstoque(
            produto_id=produto.id,
            usuario_id=current_user.id,
            tipo=tipo_movimentacao,
            quantidade=quantidade_mov,
            motivo=form.motivo.data
        )
        
        if tipo_movimentacao == 'Entrada':
            produto.quantidade += quantidade_mov
        else:
            produto.quantidade -= quantidade_mov
            
        try:
            db.session.add(nova_movimentacao)
            db.session.add(produto)
            db.session.commit()
            flash(f'{tipo_movimentacao} de {quantidade_mov} unidade(s) do produto "{produto.nome}" registrada com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar movimentação: {e}', 'danger')

    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Erro no campo '{getattr(form, field).label.text}': {error}", 'warning')

    return redirect(url_for('main.listar_produtos'))

@main_bp.route('/produto/<int:produto_id>/historico')
@login_required
def historico_produto(produto_id):
    #busca o produto pelo ID fornecido na URL. Se não encontrar, retorna erro 404.
    produto = Produto.query.get_or_404(produto_id)
    
    # Usa o "backref" para acessar a query de movimentações do produto
    #e ordena pela data_hora, com as mais recentes primeiro.
    movimentacoes = produto.movimentacoes.order_by(MovimentacaoEstoque.data_hora.desc()).all()
    
    # 3. Renderiza o novo template, passando o produto e a lista de movimentações.
    return render_template('historico_produto.html', 
                           produto=produto, 
                           movimentacoes=movimentacoes,
                           title=f'Histórico de {produto.nome}')

@main_bp.route('/fornecedores')
@login_required
def listar_fornecedores():
    fornecedores = Fornecedor.query.order_by(Fornecedor.nome).all()
    return render_template('listar_fornecedores.html', 
                           fornecedores=fornecedores, 
                           title="Fornecedores")

@main_bp.route('/fornecedor/adicionar', methods=['GET', 'POST'])
@login_required
@permission_required('Admin', 'Gerente')
def adicionar_fornecedor():
    form = FornecedorForm()
    if form.validate_on_submit():
        novo_fornecedor = Fornecedor(
            nome=form.nome.data,
            contato_nome=form.contato_nome.data,
            email=form.email.data,
            telefone=form.telefone.data,
            cep=form.cep.data,
            rua=form.rua.data,
            numero=form.numero.data,
            bairro=form.bairro.data,
            cidade=form.cidade.data,
            estado=form.estado.data
        )
        db.session.add(novo_fornecedor)
        db.session.commit()
        flash(f'Fornecedor "{novo_fornecedor.nome}" cadastrado com sucesso!', 'success')
        return redirect(url_for('main.listar_fornecedores'))
    return render_template('gerenciar_fornecedor.html', 
                           title='Adicionar Novo Fornecedor', 
                           form=form)
@main_bp.route('/fornecedor/editar/<int:fornecedor_id>', methods=['GET', 'POST'])
@login_required
@permission_required('Admin', 'Gerente')
def editar_fornecedor(fornecedor_id):
    fornecedor = Fornecedor.query.get_or_404(fornecedor_id)
    form = FornecedorForm(obj=fornecedor)
    if form.validate_on_submit():
        form.populate_obj(fornecedor)
        db.session.commit()
        flash(f'Dados do fornecedor "{fornecedor.nome}" atualizados com sucesso!', 'success')
        return redirect(url_for('main.listar_fornecedores'))
    return render_template('gerenciar_fornecedor.html', 
                           title='Editar Fornecedor', 
                           form=form)

@main_bp.route('/fornecedor/deletar/<int:fornecedor_id>', methods=['POST'])
@login_required
@permission_required('Admin')
def deletar_fornecedor(fornecedor_id):
    fornecedor = Fornecedor.query.get_or_404(fornecedor_id)
    
    #Verificação de segurança não permite deletar se houver produtos associados
    if fornecedor.produtos:
        flash(f'Não é possível excluir o fornecedor "{fornecedor.nome}", pois ele tem produtos cadastrados.', 'danger')
        return redirect(url_for('main.listar_fornecedores'))

    db.session.delete(fornecedor)
    db.session.commit()
    flash(f'Fornecedor "{fornecedor.nome}" excluído com sucesso.', 'success')
    return redirect(url_for('main.listar_fornecedores'))

@main_bp.route('/clientes')
@login_required
def listar_clientes():
    clientes = Cliente.query.order_by(Cliente.nome).all()
    return render_template('listar_clientes.html', 
                           clientes=clientes, 
                           title="Clientes")

@main_bp.route('/cliente/adicionar', methods=['GET', 'POST'])
@login_required
@permission_required('Admin, Gerente')
def adicionar_cliente():
    form = ClienteForm()
    if form.validate_on_submit():
        novo_cliente = Cliente()
        form.populate_obj(novo_cliente) # metodo populate preenche os dados do form
        db.session.add(novo_cliente)
        db.session.commit()
        flash(f'Cliente "{novo_cliente.nome}" cadastrado com sucesso!', 'success}')
        return redirect(url_for('main.listar_clientes'))
    return render_template('gerenciar_cliente.html', 
                           title='Adicionar Novo Cliente', 
                           form=form)

@main_bp.route('/cliente/editar/<int:cliente_id>', methods=['GET', 'POST'])
@login_required
@permission_required('Admin', 'Gerente')
def editar_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    form = ClienteForm(obj=cliente)
    if form.validate_on_submit():
        form.populate_obj(cliente)
        db.session.commit()
        flash(f'Dados do cliente "{cliente.nome}" atualizados com sucesso!', 'success')
        return redirect(url_for('main.listar_clientes'))
    return render_template('gerenciar_cliente.html', 
                           title='Editar Cliente', 
                           form=form)


@main_bp.route('/cliente/deletar/<int:cliente_id>', methods=['POST'])
@login_required
@permission_required('Admin')
def deletar_cliente(cliente_id):
    """Processa a exclusão de um cliente."""
    cliente = Cliente.query.get_or_404(cliente_id)
    
    # Regra de negócio: não permitir excluir cliente com OS associada
    if cliente.ordens_servico.count() > 0:
        flash(f'Não é possível excluir o cliente "{cliente.nome}", pois ele possui Ordens de Serviço vinculadas.', 'danger')
        return redirect(url_for('main.listar_clientes'))
    
    db.session.delete(cliente)
    db.session.commit()
    flash(f'Cliente "{cliente.nome}" excluído com sucesso.', 'success')
    return redirect(url_for('main.listar_clientes'))


# --- ROTAS PARA GERENCIAMENTO DE ORDENS DE SERVIÇO ---

@main_bp.route('/os')
@login_required
def listar_os():
    """Exibe a lista de todas as Ordens de Serviço."""
    # .options(db.joinedload(...)) é uma otimização para carregar os dados relacionados
    # de uma vez só, evitando múltiplas queries ao banco.
    ordens = OrdemServico.query.options(
        db.joinedload(OrdemServico.cliente), 
        db.joinedload(OrdemServico.tecnico)
    ).order_by(OrdemServico.data_abertura.desc()).all()
    
    return render_template('listar_os.html', 
                           ordens=ordens, 
                           title="Ordens de Serviço")

@main_bp.route('/os/adicionar', methods=['GET', 'POST'])
@login_required
@permission_required('Admin', 'Gerente')
def adicionar_os():
    """Exibe o formulário e processa o cadastro de uma nova OS."""
    form = OrdemServicoForm()
    if form.validate_on_submit():
        nova_os = OrdemServico()
        form.populate_obj(nova_os)
        
        # Calcula o valor total antes de salvar
        valor_servico = form.valor_servico.data or 0.0
        valor_pecas = form.valor_pecas.data or 0.0
        nova_os.valor_total = valor_servico + valor_pecas
        
        db.session.add(nova_os)
        db.session.commit()
        flash(f'Ordem de Serviço #{nova_os.id} para o cliente "{nova_os.cliente.nome}" foi aberta com sucesso!', 'success')
        return redirect(url_for('main.listar_os'))
        
    return render_template('gerenciar_os.html', 
                           form=form, 
                           title='Abrir Nova Ordem de Serviço')


@main_bp.route('/os/editar/<int:os_id>', methods=['GET', 'POST'])
@login_required
@permission_required('Admin', 'Gerente')
def editar_os(os_id):
    """Exibe o formulário e processa a edição de uma OS existente."""
    os_obj = OrdemServico.query.get_or_404(os_id)
    form = OrdemServicoForm(obj=os_obj)
    
    if form.validate_on_submit():
        form.populate_obj(os_obj)

        valor_servico = form.valor_servico.data or 0.0
        valor_pecas = form.valor_pecas.data or 0.0
        os_obj.valor_total = valor_servico + valor_pecas
        
        db.session.commit()
        flash(f'Ordem de Serviço #{os_obj.id} atualizada com sucesso!', 'success')
        return redirect(url_for('main.listar_os'))

    return render_template('gerenciar_os.html', 
                           form=form, 
                           title=f'Editar Ordem de Serviço #{os_obj.id}')

# API para a busca de produtos em tempo real (usada pelo JavaScript)
@main_bp.route('/api/produtos')
@login_required
def api_produtos():
    termo_busca = request.args.get('termo', '')
    if not termo_busca:
        return jsonify([])

    produtos = Produto.query.filter(
        Produto.nome.ilike(f'%{termo_busca}%'),
        Produto.quantidade > 0 # Apenas produtos com estoque
    ).limit(10).all()

    # Converte os objetos produto em um formato que o JavaScript entende (JSON)
    lista_produtos = [
        {'id': p.id, 'nome': p.nome, 'preco': p.preco, 'quantidade': p.quantidade}
        for p in produtos
    ]
    return jsonify(lista_produtos)

# Rota para a página de vendas
@main_bp.route('/venda/registrar', methods=['GET', 'POST'])
@login_required
@permission_required('Admin', 'Gerente') # Defina quem pode vender
def registrar_venda():
    form = VendaForm()
    if form.validate_on_submit():
        try:
            # Pega a string JSON do formulário e converte de volta para uma lista Python
            itens_do_carrinho = json.loads(form.itens_venda.data)

            if not itens_do_carrinho:
                flash('O carrinho não pode estar vazio para finalizar a venda.', 'warning')
                return redirect(url_for('main.registrar_venda'))

            valor_total_venda = 0
            nova_venda = Venda(usuario_id=current_user.id, valor_total=0) # Cria a venda
            db.session.add(nova_venda)

            for item_carrinho in itens_do_carrinho:
                produto = Produto.query.get(item_carrinho['id'])
                quantidade_vendida = int(item_carrinho['quantidade'])

                if not produto or produto.quantidade < quantidade_vendida:
                    raise Exception(f"Estoque insuficiente para o produto {item_carrinho['nome']}.")

                # Abate do estoque
                produto.quantidade -= quantidade_vendida

                # Cria o item da venda
                novo_item_venda = VendaItem(
                    venda=nova_venda,
                    produto_id=produto.id,
                    quantidade=quantidade_vendida,
                    preco_unitario=produto.preco
                )
                valor_total_venda += quantidade_vendida * produto.preco
                db.session.add(novo_item_venda)

            # Atualiza o valor total na venda
            nova_venda.valor_total = valor_total_venda
            db.session.commit()
            flash('Venda registrada com sucesso!', 'success')
            return redirect(url_for('main.home'))

        except Exception as e:
            db.session.rollback() # Desfaz tudo se der algum erro
            flash(f'Erro ao processar a venda: {e}', 'danger')

    return render_template('registrar_venda.html', title='Registrar Venda', form=form)