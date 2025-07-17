import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# Pega o caminho absoluto do diretório onde este arquivo (database.py) está
diretorio_atual = os.path.dirname(os.path.abspath(__file__))

# Define o nome do arquivo do banco de dados
NOME_BANCO = "estoque.db"

# Junta o caminho do diretório com o nome do arquivo para criar um caminho completo
caminho_banco = os.path.join(diretorio_atual, NOME_BANCO)

# URL do banco de dados SQLite usando o caminho absoluto
SQLALCHEMY_DATABASE_URL = f"sqlite:///{caminho_banco}"

# Conexão com o SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Criando uma sessão para conectar com o banco
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para criação dos modelos
Base = declarative_base()