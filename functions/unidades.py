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


# ----- API Functions for Flask Routes -----
def api_adicionar_unidade(lote_id, nome, quantitativos_unidade, valor_contratual_unidade, unidade_principal_id=None, sub_empresa=False, delegacia=False):
	"""
	API para adicionar uma nova unidade
	"""
	try:
		from .models import Lote
		
		# DEBUG: Log do valor recebido
		print(f"DEBUG - Valor recebido para sub_empresa: {sub_empresa}, tipo: {type(sub_empresa)}")
		
		# Garantir que sub_empresa é boolean
		if isinstance(sub_empresa, str):
			sub_empresa = sub_empresa.lower() in ['true', '1', 'sim']
		else:
			sub_empresa = bool(sub_empresa)
		
		print(f"DEBUG - Valor após conversão: {sub_empresa}, tipo: {type(sub_empresa)}")
		
		# Garantir que delegacia é boolean
		if isinstance(delegacia, str):
			delegacia = delegacia.lower() in ['true', '1', 'sim']
		else:
			delegacia = bool(delegacia)
		
		# Buscar o lote para validação
		lote = Lote.query.get(lote_id)
		if not lote:
			return {'success': False, 'message': 'Lote não encontrado'}
		
		# Validações para subunidades
		if unidade_principal_id:
			# Verificar se a unidade principal existe e é independente
			unidade_principal = Unidade.query.get(unidade_principal_id)
			if not unidade_principal:
				return {'success': False, 'message': 'Unidade principal não encontrada'}
			
			if unidade_principal.unidade_principal_id:
				return {'success': False, 'message': 'Uma subunidade não pode ser unidade principal de outra'}
			
			# Subunidade não deve ter quantitativos nem valor contratual
			quantitativos_unidade = None
			valor_contratual_unidade = None
		
		# Calcular soma atual dos valores das unidades ativas do lote (apenas independentes)
		unidades_existentes = Unidade.query.filter_by(lote_id=lote_id, ativo=True).all()
		soma_valores_atual = sum(u.valor_contratual_unidade or 0 for u in unidades_existentes if not u.unidade_principal_id)
		
		# Verificar se adicionar esta unidade ultrapassaria o valor contratual do lote (apenas se for independente)
		if not unidade_principal_id:
			nova_soma = soma_valores_atual + (valor_contratual_unidade or 0)
			valor_contratual_lote = lote.valor_contratual or 0
			
			# Arredondar para 2 casas decimais para evitar erros de precisão
			nova_soma = round(nova_soma, 2)
			valor_contratual_lote = round(valor_contratual_lote, 2)
			
			if nova_soma > valor_contratual_lote:
				valor_disponivel = valor_contratual_lote - round(soma_valores_atual, 2)
				return {
					'success': False,
					'message': f'Valor ultrapassa o limite! Valor disponível: R$ {valor_disponivel:.2f}. Total do lote: R$ {valor_contratual_lote:.2f}. Valor já utilizado: R$ {soma_valores_atual:.2f}.'
				}
		
		# Obter o maior ID atual
		max_id_result = db.session.query(db.func.max(Unidade.id)).scalar()
		novo_id = (max_id_result + 1) if max_id_result is not None else 0
		
		# Criar data/hora atual no formato ISO com microsegundos
		criado_em = datetime.now().isoformat()
		
		# DEBUG: Valor final antes de salvar
		print(f"DEBUG - Sobre salvar com sub_empresa: {sub_empresa}, tipo: {type(sub_empresa)}, is bool: {isinstance(sub_empresa, bool)}")
		
		# Criar nova unidade
		nova_unidade = Unidade(
			id=novo_id,
			nome=nome,
			lote_id=lote_id,
			unidade_principal_id=unidade_principal_id,
			quantitativos_unidade=quantitativos_unidade,
			valor_contratual_unidade=valor_contratual_unidade,
			sub_empresa=sub_empresa,
			delegacia=delegacia,
			criado_em=criado_em,
			ativo=True
		)
		
		db.session.add(nova_unidade)
		
		# Atualizar lista de unidades no lote
		if lote:
			# Parse unidades atuais
			unidades_atuais = []
			if lote.unidades:
				try:
					unidades_atuais = json.loads(lote.unidades) if isinstance(lote.unidades, str) else lote.unidades
					if not isinstance(unidades_atuais, list):
						unidades_atuais = []
				except:
					unidades_atuais = []
			
			# Adicionar novo ID se não estiver na lista
			if novo_id not in unidades_atuais:
				unidades_atuais.append(novo_id)
			
			# Atualizar campo unidades do lote
			lote.unidades = json.dumps(unidades_atuais)
		
		db.session.commit()
		
		# DEBUG: Verificar se foi salvo
		unidade_salva = Unidade.query.get(novo_id)
		print(f"DEBUG - Após commit: sub_empresa = {unidade_salva.sub_empresa if unidade_salva else 'NOT FOUND'}, tipo: {type(unidade_salva.sub_empresa) if unidade_salva else 'N/A'}")
		
		return {
			'success': True,
			'message': f'Unidade "{nome}" adicionada com sucesso!',
			'unidade_id': novo_id
		}
		
	except Exception as e:
		db.session.rollback()
		print(f'Erro ao adicionar unidade: {str(e)}')
		return {
			'success': False,
			'message': f'Erro ao adicionar unidade: {str(e)}'
		}


def api_editar_unidade(unidade_id, nome=None, quantitativos_unidade=None, valor_contratual_unidade=None, ativo=None, unidade_principal_id=None, sub_empresa=None, delegacia=None):
	"""
	API para editar uma unidade existente
	"""
	try:
		from .models import Lote
		
		# DEBUG: Log do valor recebido
		print(f"DEBUG EDIT - Valor recebido para sub_empresa: {sub_empresa}, tipo: {type(sub_empresa)}")
		
		# Garantir que sub_empresa é boolean se fornecido
		if sub_empresa is not None:
			if isinstance(sub_empresa, str):
				sub_empresa = sub_empresa.lower() in ['true', '1', 'sim']
			else:
				sub_empresa = bool(sub_empresa)
		
		print(f"DEBUG EDIT - Valor após conversão: {sub_empresa}, tipo: {type(sub_empresa)}")
		
		# Garantir que delegacia é boolean se fornecido
		if delegacia is not None:
			if isinstance(delegacia, str):
				delegacia = delegacia.lower() in ['true', '1', 'sim']
			else:
				delegacia = bool(delegacia)
		
		# Buscar unidade
		unidade = Unidade.query.get(unidade_id)
		if not unidade:
			return {'success': False, 'message': 'Unidade não encontrada'}
		
		# Validar se está tentando definir unidade_principal_id
		if unidade_principal_id is not None:
			# Se for string vazia, converter para None
			if unidade_principal_id == '' or unidade_principal_id == 'None':
				unidade_principal_id = None
			else:
				# Validar se a unidade principal existe e é independente
				unidade_principal = Unidade.query.get(unidade_principal_id)
				if not unidade_principal:
					return {'success': False, 'message': 'Unidade principal não encontrada'}
				
				if unidade_principal.unidade_principal_id:
					return {'success': False, 'message': 'Uma subunidade não pode ser unidade principal de outra'}
				
				if unidade_principal.id == unidade_id:
					return {'success': False, 'message': 'Uma unidade não pode ser subunidade de si mesma'}
				
				# Verificar se alguma unidade já é subunidade desta unidade (evitar ciclo)
				subunidades = Unidade.query.filter_by(unidade_principal_id=unidade_id).all()
				if subunidades:
					return {'success': False, 'message': 'Esta unidade já possui subunidades. Não pode se tornar subunidade de outra.'}
		
		# Se está se tornando subunidade, limpar quantitativos e valor
		if unidade_principal_id:
			quantitativos_unidade = None
			valor_contratual_unidade = None
		
		# Se está alterando o valor contratual, validar (apenas se não for subunidade)
		if valor_contratual_unidade is not None and unidade.lote_id and not unidade_principal_id:
			lote = Lote.query.get(unidade.lote_id)
			if lote:
				# Calcular soma dos valores das outras unidades ativas do lote (exceto esta e excluindo subunidades)
				unidades_existentes = Unidade.query.filter(
					Unidade.lote_id == unidade.lote_id,
					Unidade.ativo == True,
					Unidade.id != unidade_id
				).all()
				soma_valores_outras = sum(u.valor_contratual_unidade or 0 for u in unidades_existentes if not u.unidade_principal_id)
				
				# Verificar se o novo valor ultrapassaria o limite
				nova_soma = soma_valores_outras + valor_contratual_unidade
				valor_contratual_lote = lote.valor_contratual or 0
				
				# Arredondar para 2 casas decimais para evitar erros de precisão
				nova_soma = round(nova_soma, 2)
				valor_contratual_lote = round(valor_contratual_lote, 2)
				
				if nova_soma > valor_contratual_lote:
					valor_disponivel = valor_contratual_lote - round(soma_valores_outras, 2)
					return {
						'success': False,
						'message': f'Valor ultrapassa o limite! Valor disponível: R$ {valor_disponivel:.2f}. Total do lote: R$ {valor_contratual_lote:.2f}. Valor já utilizado por outras unidades: R$ {soma_valores_outras:.2f}.'
					}
		
		# Atualizar campos
		if nome is not None:
			unidade.nome = nome
		
		# Atualizar unidade_principal_id
		if unidade_principal_id != unidade.unidade_principal_id:
			unidade.unidade_principal_id = unidade_principal_id
			
			# Se está virando subunidade, zerar quantitativos e valor
			if unidade_principal_id is not None:
				unidade.quantitativos_unidade = None
				unidade.valor_contratual_unidade = None
		else:
			# Se permanece com o mesmo status, permitir atualizar quantitativos e valor
			if quantitativos_unidade is not None:
				unidade.quantitativos_unidade = quantitativos_unidade
			
			if valor_contratual_unidade is not None:
				unidade.valor_contratual_unidade = valor_contratual_unidade
		
		if ativo is not None:
			unidade.ativo = ativo
		
		# Atualizar sub_empresa se fornecido
		if sub_empresa is not None:
			unidade.sub_empresa = sub_empresa
			print(f"DEBUG EDIT - Atualizando sub_empresa para: {sub_empresa}")
		
		# Atualizar delegacia se fornecido
		if delegacia is not None:
			unidade.delegacia = delegacia
			print(f"DEBUG EDIT - Atualizando delegacia para: {delegacia}")
		
		db.session.commit()
		
		# DEBUG: Verificar se foi salvo
		unidade_atualizada = Unidade.query.get(unidade_id)
		print(f"DEBUG EDIT - Após commit: sub_empresa = {unidade_atualizada.sub_empresa if unidade_atualizada else 'NOT FOUND'}")
		
		return {
			'success': True,
			'message': f'Unidade "{unidade.nome}" atualizada com sucesso!'
		}
		
	except Exception as e:
		db.session.rollback()
		print(f'Erro ao editar unidade: {str(e)}')
		return {
			'success': False,
			'message': f'Erro ao editar unidade: {str(e)}'
		}


def api_excluir_unidade(unidade_id):
	"""
	API para excluir uma unidade (e suas subunidades, se houver)
	"""
	try:
		from .models import Lote
		
		# Buscar unidade
		unidade = Unidade.query.get(unidade_id)
		if not unidade:
			return {'success': False, 'message': 'Unidade não encontrada'}
		
		nome_unidade = unidade.nome
		lote_id = unidade.lote_id
		
		# Verificar se esta unidade é principal (tem subunidades)
		subunidades = Unidade.query.filter_by(unidade_principal_id=unidade_id, ativo=True).all()
		
		ids_para_remover = [unidade_id]
		nomes_excluidos = [nome_unidade]
		
		if subunidades:
			# Coletar IDs e nomes das subunidades
			for sub in subunidades:
				ids_para_remover.append(sub.id)
				nomes_excluidos.append(sub.nome)
			
			print(f'🗑️ Unidade principal "{nome_unidade}" tem {len(subunidades)} subunidade(s). Excluindo todas...')
		
		# Remover IDs das unidades da lista de unidades do lote
		if lote_id:
			lote = Lote.query.get(lote_id)
			if lote and lote.unidades:
				try:
					# Parse unidades atuais
					unidades_atuais = json.loads(lote.unidades) if isinstance(lote.unidades, str) else lote.unidades
					if isinstance(unidades_atuais, list):
						# Remover todos os IDs (principal + subunidades)
						for uid in ids_para_remover:
							if uid in unidades_atuais:
								unidades_atuais.remove(uid)
						# Atualizar campo unidades do lote
						lote.unidades = json.dumps(unidades_atuais)
				except Exception as e:
					print(f'Aviso: Não foi possível atualizar lista de unidades do lote: {str(e)}')
		
		# Excluir unidade principal e subunidades
		for uid in ids_para_remover:
			unidade_para_excluir = Unidade.query.get(uid)
			if unidade_para_excluir:
				db.session.delete(unidade_para_excluir)
		
		db.session.commit()
		
		# Mensagem de sucesso
		if len(nomes_excluidos) > 1:
			msg = f'Unidade principal "{nome_unidade}" e {len(subunidades)} subunidade(s) excluídas com sucesso!'
		else:
			msg = f'Unidade "{nome_unidade}" excluída com sucesso!'
		
		return {
			'success': True,
			'message': msg
		}
		
	except Exception as e:
		db.session.rollback()
		print(f'Erro ao excluir unidade: {str(e)}')
		return {
			'success': False,
			'message': f'Erro ao excluir unidade: {str(e)}'
		}


def api_listar_unidades(lote_id):
	"""
	API para listar todas as unidades de um lote
	"""
	try:
		unidades = Unidade.query.filter_by(lote_id=lote_id, ativo=True).all()
		
		unidades_list = []
		for u in unidades:
			# Parse quantitativos se for string
			quantitativos = {}
			if u.quantitativos_unidade:
				try:
					quantitativos = json.loads(u.quantitativos_unidade) if isinstance(u.quantitativos_unidade, str) else u.quantitativos_unidade
				except:
					quantitativos = {}
			
			unidades_list.append({
				'id': u.id,
				'nome': u.nome,
				'lote_id': u.lote_id,
				'quantitativos_unidade': quantitativos,
				'valor_contratual_unidade': u.valor_contratual_unidade,
				'criado_em': u.criado_em,
				'ativo': u.ativo,
				'unidade_principal_id': u.unidade_principal_id,
				'sub_empresa': u.sub_empresa,
				'delegacia': u.delegacia
			})
		
		return {
			'success': True,
			'unidades': unidades_list
		}
		
	except Exception as e:
		print(f'Erro ao listar unidades: {str(e)}')
		return {
			'success': False,
			'message': f'Erro ao listar unidades: {str(e)}'
		}
