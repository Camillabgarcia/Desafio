# API de Gestão de Estoque e Pedidos

Uma API RESTful desenvolvida em Python com FastAPI para gerenciamento de produtos e pedidos com controle automático de estoque.

## 🚀 Funcionalidades

### Produtos
- ✅ Criar produto com validações
- ✅ Listar produtos com paginação
- ✅ Buscar produto por ID
- ✅ Atualizar produto
- ✅ Deletar produto (com proteção)
- ✅ Relatório de produtos com baixo estoque

### Pedidos
- ✅ Criar pedido com cálculo automático do valor total
- ✅ Listar pedidos com paginação
- ✅ Buscar pedido por ID
- ✅ Atualizar pedido (com reversão de estoque)
- ✅ Deletar pedido (com reversão de estoque)
- ✅ Controle automático de estoque

### Extras
- ✅ Documentação automática (Swagger)
- ✅ Validações robustas
- ✅ Tratamento de erros
- ✅ Estatísticas do sistema
- ✅ CORS configurado

## 🛠️ Tecnologias Utilizadas

- **Python 3.13**
- **FastAPI** - Framework web moderno e rápido
- **SQLAlchemy** - ORM para Python
- **Pydantic** - Validação de dados
- **SQLite** - Banco de dados (pode ser facilmente alterado)
- **Uvicorn** - Servidor ASGI

## 📋 Pré-requisitos

- Python 3.8+
- pip (gerenciador de pacotes Python)

## 🔧 Instalação

1. Clone o repositório:
```bash
git clone <seu-repositorio>
cd api-estoque-pedidos
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
```

3. Ative o ambiente virtual:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. Instale as dependências:
```bash
pip install -r requirements.txt
```

5. Execute a aplicação:
```bash
uvicorn main:app --reload
```

## 📖 Documentação da API

Após iniciar a aplicação, acesse:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🎯 Endpoints Principais

### Produtos

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/produtos` | Criar produto |
| GET | `/produtos` | Listar produtos |
| GET | `/produtos/{id}` | Buscar produto |
| PUT | `/produtos/{id}` | Atualizar produto |
| DELETE | `/produtos/{id}` | Deletar produto |

### Pedidos

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/pedidos` | Criar pedido |
| GET | `/pedidos` | Listar pedidos |
| GET | `/pedidos/{id}` | Buscar pedido |
| PUT | `/pedidos/{id}` | Atualizar pedido |
| DELETE | `/pedidos/{id}` | Deletar pedido |

## 📝 Exemplos de Uso

### Criar Produto
```bash
curl -X POST "http://localhost:8000/produtos" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Caneta Azul",
    "descricao": "Caneta esferográfica azul",
    "preco": 2.50,
    "quantidade_estoque": 150
  }'
```

### Criar Pedido
```bash
curl -X POST "http://localhost:8000/pedidos" \
  -H "Content-Type: application/json" \
  -d '{
    "cliente": "João da Silva",
    "itens": [
      {
        "produto_id": 1,
        "quantidade": 10
      }
    ]
  }'
```

## 🔒 Validações Implementadas

### Produtos
- Nome obrigatório (1-100 caracteres)
- Preço deve ser maior que zero
- Estoque não pode ser negativo
- Nome deve ser único
- Não permite deletar produto que está em pedidos

### Pedidos
- Cliente obrigatório
- Deve conter pelo menos um item
- Quantidade deve ser maior que zero
- Verifica se produto existe
- Verifica se há estoque suficiente
- Não permite produtos duplicados no mesmo pedido

## 🗃️ Estrutura do Banco de Dados

### Tabela: produtos
- id (PK)
- nome
- descricao
- preco
- quantidade_estoque

### Tabela: pedidos
- id (PK)
- cliente
- valor_total
- data_pedido

### Tabela: itens_pedido
- id (PK)
- pedido_id (FK)
- produto_id (FK)
- nome_produto
- quantidade
- preco_unitario
- valor_total_item

## 🚨 Tratamento de Erros

A API retorna códigos de status HTTP apropriados:

- **200**: Sucesso
- **201**: Criado
- **400**: Erro de validação
- **404**: Recurso não encontrado
- **500**: Erro interno do servidor

## 📊 Relatórios Disponíveis

- **Produtos com baixo estoque**: `GET /produtos/baixo-estoque/{limite}`
- **Estatísticas gerais**: `GET /estatisticas`

## 🔄 Controle de Estoque

O sistema implementa controle automático de estoque:

1. **Ao criar pedido**: Reduz estoque dos produtos
