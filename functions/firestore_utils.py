import firebase_admin
from firebase_admin import credentials, firestore
import os

# Inicialização do Firebase (garante que só inicializa uma vez)
if not firebase_admin._apps:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DADOS_DIR = os.path.join(BASE_DIR, 'dados')
    cred_path = os.path.join(DADOS_DIR, "serviceAccountKey.json")
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

db = firestore.client()

def criar_documento(nome_colecao, dados):
    """
    Adiciona um documento à coleção especificada. Se a coleção não existir, ela será criada.
    Retorna o ID do documento criado.
    """
    colecao_ref = db.collection(nome_colecao)
    doc_ref = colecao_ref.document()
    doc_ref.set(dados)
    return doc_ref.id

def ler_documento(nome_colecao, doc_id):
    """
    Lê um documento pelo ID na coleção especificada.
    Retorna o documento como dict ou None se não existir.
    """
    doc_ref = db.collection(nome_colecao).document(doc_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict() | {'id': doc.id}
    return None

def atualizar_documento(nome_colecao, doc_id, campo, novo_valor):
    """
    Atualiza um campo específico de um documento pelo ID.
    Retorna True se atualizado, False se não existir.
    """
    doc_ref = db.collection(nome_colecao).document(doc_id)
    if doc_ref.get().exists:
        doc_ref.update({campo: novo_valor})
        return True
    return False

def deletar_documento(nome_colecao, doc_id):
    """
    Deleta um documento pelo ID na coleção especificada.
    Retorna True se deletado, False se não existir.
    """
    doc_ref = db.collection(nome_colecao).document(doc_id)
    if doc_ref.get().exists:
        doc_ref.delete()
        return True
    return False

def ler_colecao(nome_colecao):
    """
    Lê todos os documentos de uma coleção do Firestore e retorna como lista de dicts (JSON).
    """
    colecao_ref = db.collection(nome_colecao)
    return [doc.to_dict() | {'id': doc.id} for doc in colecao_ref.stream()]

def filtrar_documentos(nome_colecao, campo, valor):
    """
    Retorna documentos da coleção onde o campo é igual ao valor informado.
    """
    colecao_ref = db.collection(nome_colecao)
    query = colecao_ref.where(campo, '==', valor).stream()
    return [doc.to_dict() | {'id': doc.id} for doc in query]