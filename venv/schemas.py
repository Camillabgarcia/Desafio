from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

# === PRODUTO ===

class ProdutoBase(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100, description="Nome do produto")
    descricao: Optional[str] = Field(None, max_length=500, description="Descrição do produto")
    preco: float = Field(..., gt=0, description="Preço unitário do produto")
    quantidade_estoque: int = Field(..., ge=0, description="Quantidade em estoque")

    @validator('nome')
    def validar_nome(cls, v):
        return v.strip().title()

    @validator('descricao')
    def validar_descricao(cls, v):
        if v:
            return v.strip()
        return v

class ProdutoCreate(ProdutoBase):
    pass

class ProdutoUpdate(ProdutoBase):
    pass

class Produto(ProdutoBase):
    id: int

    class Config:
        orm_mode = True

# === PEDIDO ===

class ItemPedidoCreate(BaseModel):
    produto_id: int = Field(..., gt=0, description="ID do produto")
    quantidade: int = Field(..., gt=0, description="Quantidade do produto")

class ItemPedidoOut(BaseModel):
    id: int
    produto_id: int
    nome_produto: str
    quantidade: int
    preco_unitario: float
    valor_total_item: float

    class Config:
        orm_mode = True

class PedidoBase(BaseModel):
    cliente: str = Field(..., min_length=1, max_length=100, description="Nome do cliente")
    itens: List[ItemPedidoCreate] = Field(..., min_items=1, description="Itens do pedido")

    @validator('cliente')
    def validar_cliente(cls, v):
        return v.strip().title()

    @validator('itens')
    def validar_itens_unicos(cls, v):
        produto_ids = [item.produto_id for item in v]
        if len(produto_ids) != len(set(produto_ids)):
            raise ValueError('Não é possível ter produtos duplicados no mesmo pedido')
        return v

class PedidoCreate(PedidoBase):
    pass

class PedidoUpdate(PedidoBase):
    pass

class Pedido(BaseModel):
    id: int
    cliente: str
    valor_total: float
    data_pedido: datetime
    itens: List[ItemPedidoOut]

    class Config:
        orm_mode = True

# === RESPONSES ===

class MensagemResponse(BaseModel):
    mensagem: str

class ErroResponse(BaseModel):
    detail: str

# === FILTROS ===

class ProdutoFiltro(BaseModel):
    nome: Optional[str] = None
    preco_min: Optional[float] = None
    preco_max: Optional[float] = None
    estoque_min: Optional[int] = None