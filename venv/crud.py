from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import models, schemas
from fastapi import HTTPException
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


# === PRODUTOS ===

def criar_produto(db: Session, produto: schemas.ProdutoCreate):
    """
    Cria um novo produto no banco de dados com validações e tratamento de erros.
    """
    try:
        # Validação de preço
        if produto.preco <= 0:
            raise HTTPException(status_code=400, detail="Preço deve ser maior que zero")
        
        # Validação de estoque
        if produto.quantidade_estoque < 0:
            raise HTTPException(status_code=400, detail="Quantidade em estoque não pode ser negativa")
        
        # Verificar se produto já existe (o unique constraint também fará isso)
        produto_existente = db.query(models.Produto).filter(
            models.Produto.nome == produto.nome.strip().title()
        ).first()
        
        if produto_existente:
            raise HTTPException(status_code=400, detail="Produto com este nome já existe")
        
        # Criar produto
        produto_data = produto.dict()
        produto_data['nome'] = produto_data['nome'].strip().title()
        if produto_data.get('descricao'):
            produto_data['descricao'] = produto_data['descricao'].strip()
        
        db_produto = models.Produto(**produto_data)
        db.add(db_produto)
        db.commit()
        db.refresh(db_produto)
        
        logger.info(f"Produto criado com sucesso: {db_produto.id} - {db_produto.nome}")
        return db_produto
        
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Erro de integridade ao criar produto: {str(e)}")
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(status_code=400, detail="Produto com este nome já existe")
        raise HTTPException(status_code=400, detail="Erro de validação dos dados")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erro de banco ao criar produto: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")
    except Exception as e:
        db.rollback()
        logger.error(f"Erro inesperado ao criar produto: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


def listar_produtos(db: Session, skip: int = 0, limit: int = 100):
    """
    Lista produtos com paginação.
    """
    try:
        return db.query(models.Produto).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Erro ao listar produtos: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


def buscar_produto(db: Session, produto_id: int):
    """
    Busca um produto específico por ID.
    """
    try:
        produto = db.query(models.Produto).filter(models.Produto.id == produto_id).first()
        if not produto:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        return produto
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Erro ao buscar produto {produto_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


def atualizar_produto(db: Session, produto_id: int, dados: schemas.ProdutoUpdate):
    """
    Atualiza um produto existente com validações e tratamento de erros.
    """
    try:
        produto = db.query(models.Produto).filter(models.Produto.id == produto_id).first()
        if not produto:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        
        # Validações
        if dados.preco <= 0:
            raise HTTPException(status_code=400, detail="Preço deve ser maior que zero")
        
        if dados.quantidade_estoque < 0:
            raise HTTPException(status_code=400, detail="Quantidade em estoque não pode ser negativa")
        
        # Verificar se nome já existe (exceto para o próprio produto)
        nome_normalizado = dados.nome.strip().title()
        if nome_normalizado != produto.nome:
            produto_existente = db.query(models.Produto).filter(
                models.Produto.nome == nome_normalizado,
                models.Produto.id != produto_id
            ).first()
            
            if produto_existente:
                raise HTTPException(status_code=400, detail="Produto com este nome já existe")
        
        # Atualizar campos
        produto.nome = nome_normalizado
        produto.descricao = dados.descricao.strip() if dados.descricao else None
        produto.preco = dados.preco
        produto.quantidade_estoque = dados.quantidade_estoque
        
        db.commit()
        db.refresh(produto)
        
        logger.info(f"Produto atualizado com sucesso: {produto.id} - {produto.nome}")
        return produto
        
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Erro de integridade ao atualizar produto {produto_id}: {str(e)}")
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(status_code=400, detail="Produto com este nome já existe")
        raise HTTPException(status_code=400, detail="Erro de validação dos dados")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erro de banco ao atualizar produto {produto_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")
    except Exception as e:
        db.rollback()
        logger.error(f"Erro inesperado ao atualizar produto {produto_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


def deletar_produto(db: Session, produto_id: int):
    """
    Deleta um produto se não estiver em nenhum pedido.
    """
    try:
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
        
        nome_produto = produto.nome
        db.delete(produto)
        db.commit()
        
        logger.info(f"Produto deletado com sucesso: {produto_id} - {nome_produto}")
        return {"mensagem": "Produto deletado com sucesso"}
        
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erro de banco ao deletar produto {produto_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")
    except Exception as e:
        db.rollback()
        logger.error(f"Erro inesperado ao deletar produto {produto_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


# === PEDIDOS ===

def criar_pedido(db: Session, pedido: schemas.PedidoCreate):
    """
    Cria um novo pedido com validações completas e controle de estoque.
    """
    try:
        if not pedido.itens:
            raise HTTPException(status_code=400, detail="Pedido deve conter pelo menos um item")
        
        # Validar produtos duplicados
        produto_ids = [item.produto_id for item in pedido.itens]
        if len(produto_ids) != len(set(produto_ids)):
            raise HTTPException(status_code=400, detail="Não é possível ter produtos duplicados no mesmo pedido")
        
        valor_total = 0
        itens_pedido = []
        produtos_para_atualizar = []

        # Validar todos os itens antes de processar qualquer coisa
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
        cliente_normalizado = pedido.cliente.strip().title()
        db_pedido = models.Pedido(
            cliente=cliente_normalizado, 
            valor_total=valor_total
        )
        db.add(db_pedido)
        db.flush()  # Para obter o ID do pedido sem fazer commit

        # Criar os itens e atualizar estoque
        for item_info in itens_pedido:
            produto = item_info['produto']
            item = item_info['item']
            total_item = item_info['total_item']
            
            # Atualizar estoque
            produto.quantidade_estoque -= item.quantidade
            produtos_para_atualizar.append((produto.id, item.quantidade))
            
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
        
        logger.info(f"Pedido criado com sucesso: {db_pedido.id} - Cliente: {db_pedido.cliente}")
        return db_pedido
        
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erro de banco ao criar pedido: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")
    except Exception as e:
        db.rollback()
        logger.error(f"Erro inesperado ao criar pedido: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


def listar_pedidos(db: Session, skip: int = 0, limit: int = 100):
    """
    Lista pedidos com paginação.
    """
    try:
        return db.query(models.Pedido).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Erro ao listar pedidos: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


def buscar_pedido(db: Session, pedido_id: int):
    """
    Busca um pedido específico por ID.
    """
    try:
        pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
        if not pedido:
            raise HTTPException(status_code=404, detail="Pedido não encontrado")
        return pedido
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Erro ao buscar pedido {pedido_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


def atualizar_pedido(db: Session, pedido_id: int, dados: schemas.PedidoUpdate):
    """
    Atualiza um pedido existente com controle completo de estoque.
    """
    try:
        pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
        if not pedido:
            raise HTTPException(status_code=404, detail="Pedido não encontrado")
        
        # Validações iniciais
        if not dados.itens:
            raise HTTPException(status_code=400, detail="Pedido deve conter pelo menos um item")
        
        # Validar produtos duplicados
        produto_ids = [item.produto_id for item in dados.itens]
        if len(produto_ids) != len(set(produto_ids)):
            raise HTTPException(status_code=400, detail="Não é possível ter produtos duplicados no mesmo pedido")
        
        # Armazenar estado anterior para possível rollback
        itens_antigos = []
        for item in pedido.itens:
            produto = db.query(models.Produto).filter(
                models.Produto.id == item.produto_id
            ).first()
            if produto:
                itens_antigos.append((produto, item.quantidade))
        
        # Reverter estoque dos itens antigos
        for produto, quantidade in itens_antigos:
            produto.quantidade_estoque += quantidade
        
        # Remover itens antigos
        db.query(models.ItemPedido).filter(
            models.ItemPedido.pedido_id == pedido_id
        ).delete()
        
        # Validar e processar novos itens
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

        # Atualizar dados do pedido
        pedido.cliente = dados.cliente.strip().title()
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
        
        logger.info(f"Pedido atualizado com sucesso: {pedido.id} - Cliente: {pedido.cliente}")
        return pedido
        
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erro de banco ao atualizar pedido {pedido_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")
    except Exception as e:
        db.rollback()
        logger.error(f"Erro inesperado ao atualizar pedido {pedido_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


def deletar_pedido(db: Session, pedido_id: int):
    """
    Deleta um pedido e reverte o estoque.
    """
    try:
        pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
        if not pedido:
            raise HTTPException(status_code=404, detail="Pedido não encontrado")
        
        cliente_pedido = pedido.cliente
        
        # Reverter estoque
        for item in pedido.itens:
            produto = db.query(models.Produto).filter(
                models.Produto.id == item.produto_id
            ).first()
            if produto:
                produto.quantidade_estoque += item.quantidade
        
        # Deletar itens do pedido (cascade deve fazer isso automaticamente)
        db.query(models.ItemPedido).filter(
            models.ItemPedido.pedido_id == pedido_id
        ).delete()
        
        # Deletar pedido
        db.delete(pedido)
        db.commit()
        
        logger.info(f"Pedido deletado com sucesso: {pedido_id} - Cliente: {cliente_pedido}")
        return {"mensagem": "Pedido deletado com sucesso"}
        
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erro de banco ao deletar pedido {pedido_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")
    except Exception as e:
        db.rollback()
        logger.error(f"Erro inesperado ao deletar pedido {pedido_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


# === FUNÇÕES AUXILIARES ===

def verificar_estoque_produto(db: Session, produto_id: int, quantidade: int) -> bool:
    """
    Verifica se há estoque suficiente para um produto.
    """
    produto = db.query(models.Produto).filter(models.Produto.id == produto_id).first()
    if not produto:
        return False
    return produto.quantidade_estoque >= quantidade


def obter_produtos_baixo_estoque(db: Session, limite: int = 10) -> List[models.Produto]:
    """
    Retorna produtos com estoque abaixo do limite.
    """
    try:
        return db.query(models.Produto).filter(
            models.Produto.quantidade_estoque <= limite
        ).all()
    except SQLAlchemyError as e:
        logger.error(f"Erro ao buscar produtos com baixo estoque: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


def calcular_estatisticas(db: Session) -> dict:
    """
    Calcula estatísticas gerais do sistema.
    """
    try:
        total_produtos = db.query(models.Produto).count()
        total_pedidos = db.query(models.Pedido).count()
        
        # Valor total dos pedidos
        pedidos = db.query(models.Pedido).all()
        valor_total = sum(pedido.valor_total for pedido in pedidos)
        
        # Produto mais vendido
        produto_mais_vendido = db.query(
            models.ItemPedido.produto_id,
            models.ItemPedido.nome_produto,
            db.func.sum(models.ItemPedido.quantidade).label('total_vendido')
        ).group_by(
            models.ItemPedido.produto_id,
            models.ItemPedido.nome_produto
        ).order_by(
            db.func.sum(models.ItemPedido.quantidade).desc()
        ).first()
        
        return {
            "total_produtos": total_produtos,
            "total_pedidos": total_pedidos,
            "valor_total_pedidos": valor_total,
            "ticket_medio": valor_total / total_pedidos if total_pedidos > 0 else 0,
            "produto_mais_vendido": {
                "id": produto_mais_vendido.produto_id if produto_mais_vendido else None,
                "nome": produto_mais_vendido.nome_produto if produto_mais_vendido else None,
                "quantidade_vendida": produto_mais_vendido.total_vendido if produto_mais_vendido else 0
            } if produto_mais_vendido else None
        }
    except SQLAlchemyError as e:
        logger.error(f"Erro ao calcular estatísticas: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")