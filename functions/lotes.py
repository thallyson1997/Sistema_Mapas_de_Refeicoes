def to_int_list(unidades):
	result = []
	for u in unidades:
		try:
			result.append(int(u))
		except Exception:
			continue
	return result
# Função para carregar lotes do banco de dados (substitui o antigo carregamento do JSON)
def _load_lotes_data():
	"""Retorna todos os lotes cadastrados no banco de dados."""
	lotes = Lote.query.all()
	return [lote_to_dict(l) for l in lotes]
# Função para calcular a última atividade dos lotes
def calcular_ultima_atividade_lotes(lotes, mapas=None):
	"""Retorna a data da última atividade dos lotes ou mapas."""
	datas = []
	if lotes:
		datas += [lote.get('data_criacao') for lote in lotes if 'data_criacao' in lote and lote.get('data_criacao')]
	if mapas:
		datas += [mapa.get('atualizado_em') for mapa in mapas if 'atualizado_em' in mapa and mapa.get('atualizado_em')]
	datas = [d for d in datas if d]
	return max(datas) if datas else None

from .models import Lote, db
from datetime import datetime
from .unidades import criar_unidade

import json

def lote_to_dict(lote):
	return {
		'id': lote.id,
		'nome': lote.nome,
		'empresa': lote.empresa,
		'numero_contrato': lote.numero_contrato,
		'numero': lote.numero,
		'data_inicio': lote.data_inicio,
		'data_fim': lote.data_fim,
		'valor_contratual': lote.valor_contratual,
		'unidades': json.loads(lote.unidades) if lote.unidades else [],
		'precos': json.loads(lote.precos) if lote.precos else {},
		'ativo': lote.ativo,
		'criado_em': lote.criado_em,
		'data_criacao': lote.data_criacao,
		'data_contrato': lote.data_contrato,
		'status': lote.status,
		'descricao': lote.descricao,
	}

def listar_lotes():
	lotes = Lote.query.all()
	return [lote_to_dict(l) for l in lotes]

def deletar_lote(lote_id, db):
	"""
	Deleta um lote pelo ID e todos os dados associados (mapas e unidades).
	Isso evita dados órfãos e conflitos de integridade referencial.
	"""
	from .models import Mapa, Unidade
	
	lote = db.session.query(Lote).filter_by(id=lote_id).first()
	if not lote:
		return False
	
	try:
		# 1. Excluir todos os mapas associados ao lote
		mapas_deletados = db.session.query(Mapa).filter_by(lote_id=lote_id).delete()
		print(f"🗑️ Excluídos {mapas_deletados} mapas do lote {lote_id}")
		
		# 2. Excluir todas as unidades associadas ao lote
		unidades_deletadas = db.session.query(Unidade).filter_by(lote_id=lote_id).delete()
		print(f"🗑️ Excluídas {unidades_deletadas} unidades do lote {lote_id}")
		
		# 3. Excluir o lote
		db.session.delete(lote)
		
		# 4. Commit de todas as alterações
		db.session.commit()
		
		print(f"✅ Lote {lote_id} e todos os dados associados foram excluídos com sucesso")
		return True
		
	except Exception as e:
		db.session.rollback()
		print(f"❌ Erro ao excluir lote {lote_id}: {e}")
		return False

def obter_lote_por_id(lote_id):
	try:
		lote_id = int(lote_id)
	except Exception:
		return None
	lote = Lote.query.get(lote_id)
	if lote:
		return lote_to_dict(lote)
	return None


def salvar_novo_lote(payload: dict):
    if not isinstance(payload, dict):
        return {'success': False, 'error': 'Payload inválido'}

    nome = payload.get('nome_lote') or payload.get('nome') or payload.get('nomeLote') or ''
    empresa = payload.get('empresa') or payload.get('nome_empresa', '')
    numero_contrato = payload.get('numero_contrato') or payload.get('contrato') or ''
    numero = payload.get('numero') or numero_contrato or ''
    data_inicio = payload.get('data_inicio', '')
    data_fim = payload.get('data_fim', '')
    # Normalizar data_fim para YYYY-MM-DD
    if data_fim:
        import re
        match = re.match(r'(\d{2})/(\d{2})/(\d{4})', data_fim)
        if match:
            data_fim = f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
        else:
            match_iso = re.match(r'(\d{4})[-/](\d{2})[-/](\d{2})', data_fim)
            if match_iso:
                data_fim = f"{match_iso.group(1)}-{match_iso.group(2)}-{match_iso.group(3)}"
    valor_contratual = payload.get('valor_contratual', 0.0)
    unidades_nomes = payload.get('unidades', [])
    precos = payload.get('precos', {})
    ativo = payload.get('ativo', True)
    if isinstance(ativo, str):
        ativo = ativo.lower() in ['true', '1', 'sim', 'ativo']
    criado_em = payload.get('criado_em') or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data_criacao = payload.get('data_criacao') or criado_em
    data_contrato = payload.get('data_contrato', '')
    status = payload.get('status', 'ativo')
    descricao = payload.get('descricao', '')

    if not nome or not numero:
        return {'success': False, 'error': 'Campos obrigatórios faltando'}

    if Lote.query.filter_by(nome=nome).first():
        return {'success': False, 'error': f'Já existe um lote com o nome "{nome}". Escolha um nome diferente.'}

    novo_lote = Lote(
        nome=nome,
        empresa=empresa,
        numero_contrato=numero_contrato,
        numero=numero,
        data_inicio=data_inicio,
        data_fim=data_fim,
        valor_contratual=valor_contratual,
        unidades="[]",  # será atualizado após criar as unidades
        precos=json.dumps(precos),
        ativo=ativo,
        criado_em=criado_em,
        data_criacao=data_criacao,
        data_contrato=data_contrato,
        status=status,
        descricao=descricao
    )
    db.session.add(novo_lote)
    db.session.commit()

    # Criar unidades e associar ao lote
    unidade_ids = []
    for nome_unidade in unidades_nomes:
        res = criar_unidade(nome_unidade, lote_id=novo_lote.id)
        if res.get('success'):
            unidade_ids.append(res['id'])
    # Atualizar campo unidades do lote
    novo_lote.unidades = json.dumps(unidade_ids)
    db.session.commit()
    return {'success': True, 'id': novo_lote.id}



def editar_lote(lote_id, payload: dict):
	if not isinstance(payload, dict):
		return {'success': False, 'error': 'Payload inválido'}
	try:
		lote_id = int(lote_id)
	except Exception as e:
		print(f'[ERRO editar_lote] ID inválido: {e}')
		return {'success': False, 'error': 'ID de lote inválido'}
	lote = Lote.query.get(lote_id)
	if not lote:
		return {'success': False, 'error': f'Lote {lote_id} não encontrado'}

	# Verificar se o nome está sendo alterado e se já existe outro lote com esse nome
	novo_nome = payload.get('nome')
	if novo_nome and novo_nome != lote.nome:
		lote_existente = Lote.query.filter_by(nome=novo_nome).first()
		if lote_existente:
			return {'success': False, 'error': f'Já existe um lote com o nome "{novo_nome}". Escolha um nome diferente.'}

	try:
		for campo in [
			'nome', 'empresa', 'numero_contrato', 'numero', 'data_inicio', 'data_fim',
			'valor_contratual', 'unidades', 'precos', 'ativo', 'criado_em',
			'data_criacao', 'data_contrato', 'status', 'descricao'
		]:
			if campo in payload:
				valor = payload[campo]
				if campo == 'data_fim' and valor:
					import re
					match = re.match(r'(\d{2})/(\d{2})/(\d{4})', valor)
					if match:
						valor = f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
					else:
						match_iso = re.match(r'(\d{4})[-/](\d{2})[-/](\d{2})', valor)
						if match_iso:
							valor = f"{match_iso.group(1)}-{match_iso.group(2)}-{match_iso.group(3)}"
				if campo == 'ativo':
					if isinstance(valor, str):
						valor = valor.lower() in ['true', '1', 'sim', 'ativo']
				if campo == 'unidades':
					# Se vier nomes, gera novos IDs únicos (não repete)
					if valor and isinstance(valor[0], str):
						max_id = 0
						try:
							todos_lotes = Lote.query.all()
							for l in todos_lotes:
								ids = json.loads(l.unidades) if l.unidades else []
								if ids:
									max_id = max(max_id, max(ids))
						except Exception:
							pass
						valor = list(range(max_id + 1, max_id + 1 + len(valor)))
					else:
						valor = to_int_list(valor)
					valor = json.dumps(valor)
				elif campo == 'precos':
					valor = json.dumps(valor)
				setattr(lote, campo, valor)
		db.session.commit()
		return {'success': True, 'lote': lote_to_dict(lote)}
	except Exception as e:
		print(f'[ERRO editar_lote] {e}')
		return {'success': False, 'error': f'Erro interno: {e}'}


# Função placeholder para normalizar preços dos lotes
def normalizar_precos(dados):
	"""Normaliza os preços dos lotes. Implemente a lógica conforme necessário."""
	return dados


