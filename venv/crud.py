from sqlalchemy.orm import Session
import models, schemas
from fastapi import HTTPException


# === PRODUTOS ===

def criar_produto(db: Session, produto: schemas.ProdutoCreate):
    # Validação de preço
    if produto.preco <= 0:
        raise HTTPException(status_code=400, detail="Preço deve ser maior que zero")
    
    # Validação de estoque
    if produto.quantidade_estoque < 0:
        raise HTTPException(status_code=400, detail="Quantidade em estoque não pode ser negativa")
    
    # Verificar se produto já existe
    produto_existente = db.query(models.Produto).filter(
        models.Produto.nome == produto.nome
    ).first()
    
    if produto_existente:
        raise HTTPException(status_code=400, detail="Produto com este nome já existe")
    
    db_produto = models.Produto(**produto.dict())
    db.add(db_produto)
    db.commit()
    db.refresh(db_produto)
    return db_produto


def listar_produtos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Produto).offset(skip).limit(limit).all()


def buscar_produto(db: Session, produto_id: int):
    produto = db.query(models.Produto).filter(models.Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto


def atualizar_produto(db: Session, produto_id: int, dados: schemas.ProdutoCreate):
    produto = db.query(models.Produto).filter(models.Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    # Validações
    if dados.preco <= 0:
        raise HTTPException(status_code=400, detail="Preço deve ser maior que zero")
    
    if dados.quantidade_estoque < 0:
        raise HTTPException(status_code=400, detail="Quantidade em estoque não pode ser negativa")
    
    # Verificar se nome já existe (exceto para o próprio produto)
    if dados.nome != produto.nome:
        produto_existente = db.query(models.Produto).filter(
            models.Produto.nome == dados.nome,
            models.Produto.id != produto_id
        ).first()
        
        if produto_existente:
            raise HTTPException(status_code=400, detail="Produto com este nome já existe")
    
    for campo, valor in dados.dict().items():
        setattr(produto, campo, valor)
    
    db.commit()
    db.refresh(produto)
    return produto


def deletar_produto(db: Session, produto_id: int):
    produto = db.query(models.Produto).filter(models.Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    # Verificar se produto está em pedidos
    pedido_com_produto = db.query(models.ItemPedido).filter(
        models.ItemPedido.produto_id == produto_id
    ).first()
    
    if pedido_com_produto:
        raise HTTPException(
            status_code=400, 
            detail="Não é possível excluir produto que está em pedidos"
        )
    
    db.delete(produto)
    db.commit()
    return {"mensagem": "Produto deletado com sucesso"}


# === PEDIDOS ===

def criar_pedido(db: Session, pedido: schemas.PedidoCreate):
    if not pedido.itens:
        raise HTTPException(status_code=400, detail="Pedido deve conter pelo menos um item")
    
    valor_total = 0
    itens_pedido = []

    # Validar todos os itens antes de processar
    for item in pedido.itens:
        if item.quantidade <= 0:
            raise HTTPException(status_code=400, detail="Quantidade deve ser maior que zero")
        
        produto = db.query(models.Produto).filter(
            models.Produto.id == item.produto_id
        ).first()
        
        if not produto:
            raise HTTPException(
                status_code=404, 
                detail=f"Produto {item.produto_id} não encontrado"
            )

        if produto.quantidade_estoque < item.quantidade:
            raise HTTPException(
                status_code=400, 
                detail=f"Estoque insuficiente para o produto {produto.nome}. "
                      f"Disponível: {produto.quantidade_estoque}, Solicitado: {item.quantidade}"
            )

        total_item = item.quantidade * produto.preco
        valor_total += total_item

        itens_pedido.append({
            'produto': produto,
            'item': item,
            'total_item': total_item
        })

    # Criar o pedido
    db_pedido = models.Pedido(
        cliente=pedido.cliente, 
        valor_total=valor_total
    )
    db.add(db_pedido)
    db.flush()

    # Criar os itens e atualizar estoque
    for item_info in itens_pedido:
        produto = item_info['produto']
        item = item_info['item']
        total_item = item_info['total_item']
        
        # Atualizar estoque
        produto.quantidade_estoque -= item.quantidade
        
        # Criar item do pedido
        item_pedido = models.ItemPedido(
            pedido_id=db_pedido.id,
            produto_id=produto.id,
            nome_produto=produto.nome,
            quantidade=item.quantidade,
            preco_unitario=produto.preco,
            valor_total_item=total_item
        )
        db.add(item_pedido)

    db.commit()
    db.refresh(db_pedido)
    return db_pedido


def listar_pedidos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Pedido).offset(skip).limit(limit).all()


def buscar_pedido(db: Session, pedido_id: int):
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return pedido


def atualizar_pedido(db: Session, pedido_id: int, dados: schemas.PedidoUpdate):
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    # Reverter estoque dos itens antigos
    for item in pedido.itens:
        produto = db.query(models.Produto).filter(
            models.Produto.id == item.produto_id
        ).first()
        if produto:
            produto.quantidade_estoque += item.quantidade
    
    # Remover itens antigos
    db.query(models.ItemPedido).filter(
        models.ItemPedido.pedido_id == pedido_id
    ).delete()
    
    # Criar novos itens (reutilizar lógica do criar_pedido)
    if not dados.itens:
        raise HTTPException(status_code=400, detail="Pedido deve conter pelo menos um item")
    
    valor_total = 0
    itens_pedido = []

    for item in dados.itens:
        if item.quantidade <= 0:
            raise HTTPException(status_code=400, detail="Quantidade deve ser maior que zero")
        
        produto = db.query(models.Produto).filter(
            models.Produto.id == item.produto_id
        ).first()
        
        if not produto:
            raise HTTPException(
                status_code=404, 
                detail=f"Produto {item.produto_id} não encontrado"
            )

        if produto.quantidade_estoque < item.quantidade:
            raise HTTPException(
                status_code=400, 
                detail=f"Estoque insuficiente para o produto {produto.nome}"
            )

        total_item = item.quantidade * produto.preco
        valor_total += total_item

        itens_pedido.append({
            'produto': produto,
            'item': item,
            'total_item': total_item
        })

    # Atualizar dados do pedido
    pedido.cliente = dados.cliente
    pedido.valor_total = valor_total

    # Criar novos itens e atualizar estoque
    for item_info in itens_pedido:
        produto = item_info['produto']
        item = item_info['item']
        total_item = item_info['total_item']
        
        produto.quantidade_estoque -= item.quantidade
        
        item_pedido = models.ItemPedido(
            pedido_id=pedido.id,
            produto_id=produto.id,
            nome_produto=produto.nome,
            quantidade=item.quantidade,
            preco_unitario=produto.preco,
            valor_total_item=total_item
        )
        db.add(item_pedido)

    db.commit()
    db.refresh(pedido)
    return pedido


def deletar_pedido(db: Session, pedido_id: int):
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    # Reverter estoque
    for item in pedido.itens:
        produto = db.query(models.Produto).filter(
            models.Produto.id == item.produto_id
        ).first()
        if produto:
            produto.quantidade_estoque += item.quantidade
    
    # Deletar itens do pedido
    db.query(models.ItemPedido).filter(
        models.ItemPedido.pedido_id == pedido_id
    ).delete()
    
    # Deletar pedido
    db.delete(pedido)
    db.commit()
    return {"mensagem": "Pedido deletado com sucesso"}