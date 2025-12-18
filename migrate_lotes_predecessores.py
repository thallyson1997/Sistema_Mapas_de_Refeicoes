"""
Script de migração para adicionar campo lote_predecessor_id à tabela lotes
Permite criar cadeia de lotes históricos para lidar com reajustes de preços
"""

import sqlite3
import os

# Caminho do banco de dados
DB_PATH = os.path.join('dados', 'dados.db')

def migrar_lotes_predecessores():
    """Adiciona campo lote_predecessor_id à tabela lotes"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Banco de dados não encontrado: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Verificar se a coluna já existe
        cursor.execute("PRAGMA table_info(lotes)")
        colunas = [info[1] for info in cursor.fetchall()]
        
        print(f"📋 Colunas atuais da tabela lotes: {colunas}")
        
        if 'lote_predecessor_id' in colunas:
            print("✅ Campo 'lote_predecessor_id' já existe na tabela lotes!")
            return
        
        # Adicionar nova coluna
        print("\n🔧 Adicionando campo 'lote_predecessor_id' à tabela lotes...")
        cursor.execute("""
            ALTER TABLE lotes 
            ADD COLUMN lote_predecessor_id INTEGER NULL
        """)
        
        conn.commit()
        print("✅ Campo 'lote_predecessor_id' adicionado com sucesso!")
        
        # Verificar estrutura atualizada
        cursor.execute("PRAGMA table_info(lotes)")
        colunas_atualizadas = cursor.fetchall()
        
        print("\n📊 Estrutura da tabela lotes após migração:")
        for col in colunas_atualizadas:
            print(f"  - {col[1]} ({col[2]}){' NOT NULL' if col[3] else ' NULL'}")
        
        # Mostrar alguns lotes como exemplo
        cursor.execute("SELECT id, nome, ativo, lote_predecessor_id FROM lotes LIMIT 5")
        lotes = cursor.fetchall()
        
        print(f"\n📦 Primeiros {len(lotes)} lotes (exemplo):")
        for lote in lotes:
            print(f"  ID: {lote[0]}, Nome: {lote[1]}, Ativo: {lote[2]}, Predecessor: {lote[3]}")
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao migrar tabela: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("🔄 MIGRAÇÃO: Adicionar campo lote_predecessor_id")
    print("=" * 60)
    migrar_lotes_predecessores()
    print("\n" + "=" * 60)
    print("✅ Migração concluída!")
    print("=" * 60)
