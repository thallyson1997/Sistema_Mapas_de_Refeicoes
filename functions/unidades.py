import json
import os
from datetime import datetime
from .models import Unidade, db


# ----- Data Loading/Saving -----
def _load_unidades_data():
	base_dir = os.path.dirname(os.path.dirname(__file__))
	unidades_path = os.path.join(base_dir, 'dados', 'unidades.json')
	if not os.path.isfile(unidades_path):
		return None
	try:
		with open(unidades_path, 'r', encoding='utf-8') as f:
			return json.load(f)
	except Exception:
		return None


def _save_unidades_data(data):
	base_dir = os.path.dirname(os.path.dirname(__file__))
	unidades_path = os.path.join(base_dir, 'dados', 'unidades.json')
	try:
		os.makedirs(os.path.dirname(unidades_path), exist_ok=True)
		tmp_path = unidades_path + '.tmp'
		with open(tmp_path, 'w', encoding='utf-8') as f:
			json.dump(data, f, ensure_ascii=False, indent=2)
		os.replace(tmp_path, unidades_path)
		return True
	except Exception:
		return False


# ----- Main Unidade Operations -----
def criar_unidade(nome, lote_id=None):
	"""
	Cria uma nova unidade no banco de dados
	"""
	if not nome or not isinstance(nome, str):
		return {'success': False, 'error': 'Nome da unidade é obrigatório'}
	nome = nome.strip()
	if not nome:
		return {'success': False, 'error': 'Nome da unidade não pode ser vazio'}
	# Verificar se já existe unidade com o mesmo nome
	if Unidade.query.filter(Unidade.nome.ilike(nome)).first():
		return {'success': False, 'error': f'Unidade "{nome}" já existe'}
	# Gerar novo ID
	last_unidade = Unidade.query.order_by(Unidade.id.desc()).first()
	new_id = (last_unidade.id + 1) if last_unidade else 0
	nova_unidade = Unidade(
		id=new_id,
		nome=nome,
		lote_id=int(lote_id) if lote_id is not None else None,
		criado_em=datetime.now().isoformat()
	)
	db.session.add(nova_unidade)
	db.session.commit()
	return {'success': True, 'id': new_id, 'unidade': {
		'id': nova_unidade.id,
		'nome': nova_unidade.nome,
		'lote_id': nova_unidade.lote_id,
		'criado_em': nova_unidade.criado_em
	}}


def editar_unidade(unidade_id, novo_nome=None, novo_lote_id=None):
	"""
	Edita uma unidade existente no banco de dados
	"""
	try:
		unidade_id = int(unidade_id)
	except Exception:
		return {'success': False, 'error': 'ID de unidade inválido'}
	unidade = Unidade.query.get(unidade_id)
	if not unidade:
		return {'success': False, 'error': f'Unidade {unidade_id} não encontrada'}
	if novo_nome is not None:
		novo_nome = str(novo_nome).strip()
		if not novo_nome:
			return {'success': False, 'error': 'Nome da unidade não pode ser vazio'}
		if Unidade.query.filter(Unidade.nome.ilike(novo_nome), Unidade.id != unidade_id).first():
			return {'success': False, 'error': f'Já existe uma unidade com o nome "{novo_nome}"'}
		unidade.nome = novo_nome
	if novo_lote_id is not None:
		try:
			unidade.lote_id = int(novo_lote_id)
		except Exception:
			unidade.lote_id = None
	unidade.atualizado_em = datetime.now().isoformat()
	db.session.commit()
	return {'success': True, 'unidade': {
		'id': unidade.id,
		'nome': unidade.nome,
		'lote_id': unidade.lote_id,
		'criado_em': unidade.criado_em,
		'atualizado_em': unidade.atualizado_em
	}}


def deletar_unidade(unidade_id):
	"""
	Deleta uma unidade do banco de dados
	"""
	try:
		unidade_id = int(unidade_id)
	except Exception:
		return {'success': False, 'error': 'ID de unidade inválido'}
	unidade = Unidade.query.get(unidade_id)
	if not unidade:
		return {'success': False, 'error': f'Unidade {unidade_id} não encontrada'}
	db.session.delete(unidade)
	db.session.commit()
	return {'success': True, 'mensagem': f'Unidade {unidade_id} deletada com sucesso'}


def obter_unidade_por_id(unidade_id):
	"""
	Obtém uma unidade específica por ID
	"""
	try:
		unidade_id = int(unidade_id)
	except Exception:
		return None
	
	data = _load_unidades_data()
	unidades_list = []
	
	if isinstance(data, list):
		unidades_list = data
	elif isinstance(data, dict) and isinstance(data.get('unidades'), list):
		unidades_list = data.get('unidades')
	else:
		return None
	
	for u in unidades_list:
		if isinstance(u, dict) and u.get('id') == unidade_id:
			return u
	
	return None


def obter_unidade_por_nome(nome):
	"""
	Obtém uma unidade específica por nome
	"""
	if not nome or not isinstance(nome, str):
		return None
	
	nome = nome.strip().lower()
	
	data = _load_unidades_data()
	unidades_list = []
	
	if isinstance(data, list):
		unidades_list = data
	elif isinstance(data, dict) and isinstance(data.get('unidades'), list):
		unidades_list = data.get('unidades')
	else:
		return None
	
	for u in unidades_list:
		if isinstance(u, dict) and isinstance(u.get('nome'), str):
			if u.get('nome').strip().lower() == nome:
				return u
	
	return None


def listar_unidades(lote_id=None):
	"""
	Lista todas as unidades, opcionalmente filtradas por lote_id
	"""
	data = _load_unidades_data()
	unidades_list = []
	
	if isinstance(data, list):
		unidades_list = data
	elif isinstance(data, dict) and isinstance(data.get('unidades'), list):
		unidades_list = data.get('unidades')
	else:
		return []
	
	if lote_id is not None:
		try:
			lote_id = int(lote_id)
			return [u for u in unidades_list if isinstance(u, dict) and u.get('lote_id') == lote_id]
		except Exception:
			return []
	
	return unidades_list


def obter_mapa_unidades():
	"""
	Retorna um dicionário mapeando ID -> Nome de unidade
	"""
	data = _load_unidades_data()
	unidades_list = []
	
	if isinstance(data, list):
		unidades_list = data
	elif isinstance(data, dict) and isinstance(data.get('unidades'), list):
		unidades_list = data.get('unidades')
	else:
		return {}
	
	mapa = {}
	for u in unidades_list:
		if isinstance(u, dict) and isinstance(u.get('id'), int):
			mapa[int(u.get('id'))] = u.get('nome', '')
	
	return mapa


def associar_unidade_ao_lote(unidade_id, lote_id):
	"""
	Associa uma unidade a um lote
	"""
	try:
		unidade_id = int(unidade_id)
		lote_id = int(lote_id)
	except Exception:
		return {'success': False, 'error': 'IDs inválidos'}
	
	return editar_unidade(unidade_id, novo_lote_id=lote_id)


def desassociar_unidade_do_lote(unidade_id):
	"""
	Remove a associação de uma unidade com um lote
	"""
	try:
		unidade_id = int(unidade_id)
	except Exception:
		return {'success': False, 'error': 'ID de unidade inválido'}
	
	return editar_unidade(unidade_id, novo_lote_id=None)
