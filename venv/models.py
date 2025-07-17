from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base

class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False, unique=True, index=True)
    descricao = Column(String, nullable=True)
    preco = Column(Float, nullable=False)
    quantidade_estoque = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relacionamento explícito com back_populates
    itens_pedido = relationship("ItemPedido", back_populates="produto")

    def __repr__(self):
        return f"<Produto(id={self.id}, nome='{self.nome}', preco={self.preco}, estoque={self.quantidade_estoque})>"


class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    cliente = Column(String, nullable=False, index=True)
    valor_total = Column(Float, nullable=False)
    data_pedido = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relacionamento explícito com back_populates e cascade
    itens = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Pedido(id={self.id}, cliente='{self.cliente}', valor_total={self.valor_total})>"


class ItemPedido(Base):
    __tablename__ = "itens_pedido"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    nome_produto = Column(String, nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Float, nullable=False)
    valor_total_item = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relacionamentos explícitos com back_populates
    pedido = relationship("Pedido", back_populates="itens")
    produto = relationship("Produto", back_populates="itens_pedido")

    def __repr__(self):
        return f"<ItemPedido(id={self.id}, pedido_id={self.pedido_id}, produto_id={self.produto_id}, quantidade={self.quantidade})>"


# Índices compostos para otimização
Index('idx_item_pedido_produto', ItemPedido.pedido_id, ItemPedido.produto_id)
Index('idx_pedido_data_cliente', Pedido.data_pedido, Pedido.cliente)