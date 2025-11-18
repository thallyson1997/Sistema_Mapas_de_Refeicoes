import json
import os
from datetime import datetime


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
	Cria uma nova unidade
	"""
	if not nome or not isinstance(nome, str):
		return {'success': False, 'error': 'Nome da unidade é obrigatório'}
	
	nome = nome.strip()
	if not nome:
		return {'success': False, 'error': 'Nome da unidade não pode ser vazio'}
	
	data = _load_unidades_data()
	unidades_list = []
	wrapped = None
	
	if isinstance(data, list):
		unidades_list = data
	elif isinstance(data, dict) and isinstance(data.get('unidades'), list):
		unidades_list = data.get('unidades')
		wrapped = data
	else:
		unidades_list = []
	
	# Verificar se já existe unidade com o mesmo nome
	for u in unidades_list:
		if isinstance(u, dict) and isinstance(u.get('nome'), str):
			if u.get('nome').strip().lower() == nome.lower():
				return {'success': False, 'error': f'Unidade "{nome}" já existe'}
	
	# Gerar novo ID
	existing_ids = [u.get('id') for u in unidades_list if isinstance(u, dict) and isinstance(u.get('id'), int)]
	new_id = (max(existing_ids) + 1) if existing_ids else 0
	
	# Criar nova unidade
	nova_unidade = {
		'id': new_id,
		'nome': nome,
		'criado_em': datetime.now().isoformat()
	}
	
	if lote_id is not None:
		try:
			nova_unidade['lote_id'] = int(lote_id)
		except Exception:
			pass
	
	unidades_list.append(nova_unidade)
	
	# Salvar
	if wrapped is not None:
		wrapped['unidades'] = unidades_list
		to_write = wrapped
	else:
		to_write = unidades_list
	
	if not _save_unidades_data(to_write):
		return {'success': False, 'error': 'Erro ao salvar unidade'}
	
	return {'success': True, 'id': new_id, 'unidade': nova_unidade}


def editar_unidade(unidade_id, novo_nome=None, novo_lote_id=None):
	"""
	Edita uma unidade existente
	"""
	try:
		unidade_id = int(unidade_id)
	except Exception:
		return {'success': False, 'error': 'ID de unidade inválido'}
	
	data = _load_unidades_data()
	unidades_list = []
	wrapped = None
	
	if isinstance(data, list):
		unidades_list = data
	elif isinstance(data, dict) and isinstance(data.get('unidades'), list):
		unidades_list = data.get('unidades')
		wrapped = data
	else:
		return {'success': False, 'error': 'Nenhuma unidade encontrada'}
	
	# Encontrar unidade
	unidade_encontrada = None
	unidade_index = None
	for i, u in enumerate(unidades_list):
		if isinstance(u, dict) and u.get('id') == unidade_id:
			unidade_encontrada = u
			unidade_index = i
			break
	
	if unidade_encontrada is None:
		return {'success': False, 'error': f'Unidade {unidade_id} não encontrada'}
	
	# Atualizar campos
	if novo_nome is not None:
		novo_nome = str(novo_nome).strip()
		if not novo_nome:
			return {'success': False, 'error': 'Nome da unidade não pode ser vazio'}
		
		# Verificar duplicata
		for u in unidades_list:
			if isinstance(u, dict) and u.get('id') != unidade_id:
				if isinstance(u.get('nome'), str) and u.get('nome').strip().lower() == novo_nome.lower():
					return {'success': False, 'error': f'Já existe uma unidade com o nome "{novo_nome}"'}
		
		unidade_encontrada['nome'] = novo_nome
	
	if novo_lote_id is not None:
		try:
			unidade_encontrada['lote_id'] = int(novo_lote_id)
		except Exception:
			unidade_encontrada['lote_id'] = None
	
	unidade_encontrada['atualizado_em'] = datetime.now().isoformat()
	
	unidades_list[unidade_index] = unidade_encontrada
	
	# Salvar
	if wrapped is not None:
		wrapped['unidades'] = unidades_list
		to_write = wrapped
	else:
		to_write = unidades_list
	
	if not _save_unidades_data(to_write):
		return {'success': False, 'error': 'Erro ao salvar alterações'}
	
	return {'success': True, 'unidade': unidade_encontrada}


def deletar_unidade(unidade_id):
	"""
	Deleta uma unidade
	"""
	try:
		unidade_id = int(unidade_id)
	except Exception:
		return {'success': False, 'error': 'ID de unidade inválido'}
	
	data = _load_unidades_data()
	unidades_list = []
	wrapped = None
	
	if isinstance(data, list):
		unidades_list = data
	elif isinstance(data, dict) and isinstance(data.get('unidades'), list):
		unidades_list = data.get('unidades')
		wrapped = data
	else:
		return {'success': False, 'error': 'Nenhuma unidade encontrada'}
	
	# Encontrar unidade
	unidade_index = None
	for i, u in enumerate(unidades_list):
		if isinstance(u, dict) and u.get('id') == unidade_id:
			unidade_index = i
			break
	
	if unidade_index is None:
		return {'success': False, 'error': f'Unidade {unidade_id} não encontrada'}
	
	# Remover unidade
	unidades_list.pop(unidade_index)
	
	# Salvar
	if wrapped is not None:
		wrapped['unidades'] = unidades_list
		to_write = wrapped
	else:
		to_write = unidades_list
	
	if not _save_unidades_data(to_write):
		return {'success': False, 'error': 'Erro ao salvar alterações'}
	
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
