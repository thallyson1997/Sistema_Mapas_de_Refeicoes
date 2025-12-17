import sqlite3
import json

# Conectar ao banco de dados
conn = sqlite3.connect('dados/dados.db')
cursor = conn.cursor()

print("Iniciando migração da tabela 'unidades'...")

# Verificar se as colunas já existem
cursor.execute("PRAGMA table_info(unidades)")
columns = [row[1] for row in cursor.fetchall()]
print(f"Colunas atuais: {columns}")

# Adicionar coluna quantitativos_unidade se não existir
if 'quantitativos_unidade' not in columns:
    print("Adicionando coluna 'quantitativos_unidade'...")
    cursor.execute("ALTER TABLE unidades ADD COLUMN quantitativos_unidade TEXT")
    print("✅ Coluna 'quantitativos_unidade' adicionada com sucesso!")
    
    # Inicializar com JSON vazio para unidades existentes
    cursor.execute("UPDATE unidades SET quantitativos_unidade = '{}' WHERE quantitativos_unidade IS NULL")
    print("✅ Valores inicializados para unidades existentes")
else:
    print("⚠️ Coluna 'quantitativos_unidade' já existe")

# Adicionar coluna valor_contratual_unidade se não existir
if 'valor_contratual_unidade' not in columns:
    print("Adicionando coluna 'valor_contratual_unidade'...")
    cursor.execute("ALTER TABLE unidades ADD COLUMN valor_contratual_unidade REAL")
    print("✅ Coluna 'valor_contratual_unidade' adicionada com sucesso!")
    
    # Inicializar com 0.0 para unidades existentes
    cursor.execute("UPDATE unidades SET valor_contratual_unidade = 0.0 WHERE valor_contratual_unidade IS NULL")
    print("✅ Valores inicializados para unidades existentes")
else:
    print("⚠️ Coluna 'valor_contratual_unidade' já existe")

# Commit das alterações
conn.commit()

# Verificar estrutura final
print("\nVerificando estrutura final da tabela 'unidades':")
cursor.execute("PRAGMA table_info(unidades)")
for row in cursor.fetchall():
    print(f"  - {row[1]} ({row[2]})")

# Verificar dados das unidades
print("\nUnidades cadastradas:")
cursor.execute("SELECT id, nome, lote_id, quantitativos_unidade, valor_contratual_unidade FROM unidades")
unidades = cursor.fetchall()
for unidade in unidades:
    print(f"  ID: {unidade[0]} | Nome: {unidade[1]} | Lote: {unidade[2]} | Qtd: {unidade[3]} | Valor: R$ {unidade[4]}")

conn.close()
print("\n✅ Migração concluída com sucesso!")
