from database import Base, engine
import models

print("Criando o banco de dados...")
Base.metadata.create_all(bind=engine)
