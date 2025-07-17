from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
import logging

import models, schemas, crud
from database import SessionLocal, engine

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar tabelas
models.Base.metadata.create_all(bind=engine)

# Configurar FastAPI
app = FastAPI(
    title="API de Gestão de Estoque e Pedidos",
    description="API para gerenciamento de produtos e pedidos com controle de estoque",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency para obter sessão do banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Exception handler personalizado
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Erro interno: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor"}
    )

# === ENDPOINTS ROOT ===

@app.get("/", tags=["Root"])
def root():
    return {
        "mensagem": "API de Gestão de Estoque e Pedidos",
        "versao": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health", tags=["Health"])
def health_check():
    # Gera o timestamp no momento exato da requisição, no padrão UTC
    timestamp_atual = datetime.now(timezone.utc).isoformat()
    
    return {"status": "OK", "timestamp": timestamp_atual}

# === ENDPOINTS PRODUTOS ===

@app.post("/produtos", response_model=schemas.Produto, tags=["Produtos"])
def criar_produto(produto: schemas.ProdutoCreate, db: Session = Depends(get_db)):
    """
    Criar um novo produto
    
    - **nome**: Nome do produto (obrigatório)
    - **descricao**: Descrição do produto (opcional)
    - **preco**: Preço unitário (deve ser maior que 0)
    - **quantidade_estoque**: Quantidade em estoque (não pode ser negativa)
    """
    return crud.criar_produto(db, produto)

@app.get("/produtos", response_model=List[schemas.Produto], tags=["Produtos"])
def listar_produtos(
    skip: int = Query(0, ge=0, description="Número de registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros"),
    db: Session = Depends(get_db)
):
    """
    Listar todos os produtos com paginação
    """
    return crud.listar_produtos(db, skip=skip, limit=limit)

@app.get("/produtos/{produto_id}", response_model=schemas.Produto, tags=["Produtos"])
def obter_produto(produto_id: int, db: Session = Depends(get_db)):
    """
    Obter produto específico por ID
    """
    return crud.buscar_produto(db, produto_id)

@app.put("/produtos/{produto_id}", response_model=schemas.Produto, tags=["Produtos"])
def atualizar_produto(
    produto_id: int, 
    dados: schemas.ProdutoUpdate, 
    db: Session = Depends(get_db)
):
    """
    Atualizar produto existente
    """
    return crud.atualizar_produto(db, produto_id, dados)

@app.delete("/produtos/{produto_id}", response_model=schemas.MensagemResponse, tags=["Produtos"])
def deletar_produto(produto_id: int, db: Session = Depends(get_db)):
    """
    Deletar produto (apenas se não estiver em nenhum pedido)
    """
    return crud.deletar_produto(db, produto_id)

# === ENDPOINTS PEDIDOS ===

@app.post("/pedidos", response_model=schemas.Pedido, tags=["Pedidos"])
def criar_pedido(pedido: schemas.PedidoCreate, db: Session = Depends(get_db)):
    """
    Criar um novo pedido
    
    - **cliente**: Nome do cliente (obrigatório)
    - **itens**: Lista de itens do pedido (obrigatório, mínimo 1 item)
    
    O sistema automaticamente:
    - Calcula o valor total do pedido
    - Atualiza o estoque dos produtos
    - Valida se há estoque suficiente
    """
    return crud.criar_pedido(db, pedido)

@app.get("/pedidos", response_model=List[schemas.Pedido], tags=["Pedidos"])
def listar_pedidos(
    skip: int = Query(0, ge=0, description="Número de registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de registros"),
    db: Session = Depends(get_db)
):
    """
    Listar todos os pedidos com paginação
    """
    return crud.listar_pedidos(db, skip=skip, limit=limit)

@app.get("/pedidos/{pedido_id}", response_model=schemas.Pedido, tags=["Pedidos"])
def obter_pedido(pedido_id: int, db: Session = Depends(get_db)):
    """
    Obter pedido específico por ID
    """
    return crud.buscar_pedido(db, pedido_id)

@app.put("/pedidos/{pedido_id}", response_model=schemas.Pedido, tags=["Pedidos"])
def atualizar_pedido(
    pedido_id: int, 
    dados: schemas.PedidoUpdate, 
    db: Session = Depends(get_db)
):
    """
    Atualizar pedido existente
    
    Atenção: Esta operação irá:
    - Reverter o estoque dos itens antigos
    - Aplicar os novos itens ao estoque
    - Recalcular o valor total
    """
    return crud.atualizar_pedido(db, pedido_id, dados)

@app.delete("/pedidos/{pedido_id}", response_model=schemas.MensagemResponse, tags=["Pedidos"])
def deletar_pedido(pedido_id: int, db: Session = Depends(get_db)):
    """
    Deletar pedido e reverter estoque
    """
    return crud.deletar_pedido(db, pedido_id)

# === ENDPOINTS EXTRAS ===

@app.get("/produtos/baixo-estoque/{limite}", response_model=List[schemas.Produto], tags=["Relatórios"])
def produtos_baixo_estoque(limite: int = 10, db: Session = Depends(get_db)):
    """
    Listar produtos com estoque abaixo do limite especificado
    """
    produtos = db.query(models.Produto).filter(
        models.Produto.quantidade_estoque <= limite
    ).all()
    return produtos

@app.get("/estatisticas", tags=["Relatórios"])
def estatisticas(db: Session = Depends(get_db)):
    """
    Estatísticas gerais do sistema
    """
    total_produtos = db.query(models.Produto).count()
    total_pedidos = db.query(models.Pedido).count()
    valor_total_pedidos = db.query(models.Pedido).all()
    
    valor_total = sum(pedido.valor_total for pedido in valor_total_pedidos)
    
    return {
        "total_produtos": total_produtos,
        "total_pedidos": total_pedidos,
        "valor_total_pedidos": valor_total,
        "ticket_medio": valor_total / total_pedidos if total_pedidos > 0 else 0
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)