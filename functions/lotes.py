import json
import re
import os
from datetime import datetime


# ----- Data Loading/Saving -----
def _load_lotes_data():
	base_dir = os.path.dirname(os.path.dirname(__file__))
	lotes_path = os.path.join(base_dir, 'dados', 'lotes.json')
	if not os.path.isfile(lotes_path):
		return None
	try:
		with open(lotes_path, 'r', encoding='utf-8') as f:
			return json.load(f)
	except Exception:
		return None


def _save_lotes_data(data):
	base_dir = os.path.dirname(os.path.dirname(__file__))
	lotes_path = os.path.join(base_dir, 'dados', 'lotes.json')
	try:
		os.makedirs(os.path.dirname(lotes_path), exist_ok=True)
		tmp_path = lotes_path + '.tmp'
		with open(tmp_path, 'w', encoding='utf-8') as f:
			json.dump(data, f, ensure_ascii=False, indent=2)
		os.replace(tmp_path, lotes_path)
		return True
	except Exception:
		return False


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


# ----- Price Normalization -----
def normalizar_precos(raw_precos):
	meals = ('cafe', 'almoco', 'lanche', 'jantar')

	def _to_float(v):
		try:
			return float(str(v).replace(',', '.'))
		except Exception:
			return 0.0

	res = {m: {'interno': 0.0, 'funcionario': 0.0} for m in meals}
	if raw_precos is None:
		return res

	if isinstance(raw_precos, str):
		txt = raw_precos.strip()
		try:
			parsed = json.loads(txt)
		except Exception:
			try:
				parsed = json.loads(txt.replace("'", '"'))
			except Exception:
				parsed = {}
				for m in re.finditer(r"([a-zA-Z0-9_]+)\s*[:=]\s*['\"]?([0-9\.,]+)['\"]?", txt):
					k = m.group(1)
					v = m.group(2)
					parsed[k] = v
		raw = parsed
	elif isinstance(raw_precos, dict):
		raw = raw_precos
	else:
		return res

	if isinstance(raw, dict):
		for meal in meals:
			val = raw.get(meal)
			if isinstance(val, dict):
				res[meal]['interno'] = _to_float(val.get('interno') or val.get('interno_val') or 0)
				res[meal]['funcionario'] = _to_float(val.get('funcionario') or val.get('funcionario_val') or 0)
			else:
				int_key = f"{meal}_interno"
				func_key = f"{meal}_funcionario"
				if int_key in raw or func_key in raw:
					res[meal]['interno'] = _to_float(raw.get(int_key) or raw.get(int_key.replace('_', '')))
					res[meal]['funcionario'] = _to_float(raw.get(func_key) or raw.get(func_key.replace('_', '')))
				int_key2 = f"{meal}Interno"
				func_key2 = f"{meal}Funcionario"
				if (res[meal]['interno'] == 0.0) and int_key2 in raw:
					res[meal]['interno'] = _to_float(raw.get(int_key2))
				if (res[meal]['funcionario'] == 0.0) and func_key2 in raw:
					res[meal]['funcionario'] = _to_float(raw.get(func_key2))
		for m in meals:
			res[m]['interno'] = _to_float(res[m]['interno'])
			res[m]['funcionario'] = _to_float(res[m]['funcionario'])
		return res
	return res


# ----- Main Lote Operations -----
def salvar_novo_lote(payload: dict):
	if not isinstance(payload, dict):
		return {'success': False, 'error': 'Payload inválido'}

	nome = payload.get('nome_lote') or payload.get('nome') or payload.get('nomeLote') or ''
	empresa = payload.get('nome_empresa') or payload.get('empresa') or payload.get('empresa_nome') or ''
	numero_contrato = payload.get('numero_contrato') or payload.get('contrato') or ''
	data_inicio = payload.get('data_inicio') or payload.get('inicio_contrato') or ''
	data_fim = payload.get('data_fim') or payload.get('fim_contrato') or ''
	valor_contratual = payload.get('valor_contratual') or payload.get('valorContratual') or 0
	unidades = payload.get('unidades') or payload.get('unidades[]') or []

	if unidades is None:
		unidades = []
	if isinstance(unidades, str):
		unidades = [u.strip() for u in unidades.split(',') if u.strip()]
	if not isinstance(unidades, list):
		unidades = list(unidades)

	precos = {}
	raw_precos = payload.get('precos') or {}
	if isinstance(raw_precos, dict):
		precos['cafe_interno'] = raw_precos.get('cafe', {}).get('interno') if isinstance(raw_precos.get('cafe'), dict) else raw_precos.get('cafe_interno') or raw_precos.get('cafeInterno')
		precos['cafe_funcionario'] = raw_precos.get('cafe', {}).get('funcionario') if isinstance(raw_precos.get('cafe'), dict) else raw_precos.get('cafe_funcionario') or raw_precos.get('cafeFuncionario')
		precos['almoco_interno'] = raw_precos.get('almoco', {}).get('interno') if isinstance(raw_precos.get('almoco'), dict) else raw_precos.get('almoco_interno') or raw_precos.get('almocoInterno')
		precos['almoco_funcionario'] = raw_precos.get('almoco', {}).get('funcionario') if isinstance(raw_precos.get('almoco'), dict) else raw_precos.get('almoco_funcionario') or raw_precos.get('almocoFuncionario')
		precos['lanche_interno'] = raw_precos.get('lanche', {}).get('interno') if isinstance(raw_precos.get('lanche'), dict) else raw_precos.get('lanche_interno') or raw_precos.get('lancheInterno')
		precos['lanche_funcionario'] = raw_precos.get('lanche', {}).get('funcionario') if isinstance(raw_precos.get('lanche'), dict) else raw_precos.get('lanche_funcionario') or raw_precos.get('lancheFuncionario')
		precos['jantar_interno'] = raw_precos.get('jantar', {}).get('interno') if isinstance(raw_precos.get('jantar'), dict) else raw_precos.get('jantar_interno') or raw_precos.get('jantarInterno')
		precos['jantar_funcionario'] = raw_precos.get('jantar', {}).get('funcionario') if isinstance(raw_precos.get('jantar'), dict) else raw_precos.get('jantar_funcionario') or raw_precos.get('jantarFuncionario')
	else:
		for k in ['cafe_interno','cafe_funcionario','almoco_interno','almoco_funcionario','lanche_interno','lanche_funcionario','jantar_interno','jantar_funcionario']:
			precos[k] = payload.get(k)

	if not nome or not empresa or not numero_contrato or not data_inicio or not data_fim:
		return {'success': False, 'error': 'Campos obrigatórios faltando'}
	if not unidades or not isinstance(unidades, list) or len(unidades) == 0:
		return {'success': False, 'error': 'Adicione pelo menos uma unidade'}

	data = _load_lotes_data()
	lotes = None
	wrapped = None
	if isinstance(data, list):
		lotes = data
	elif isinstance(data, dict) and isinstance(data.get('lotes'), list):
		lotes = data.get('lotes')
		wrapped = data
	else:
		lotes = []

	# Validação 1: Nome do lote não pode ser duplicado
	for lote_existente in lotes:
		if isinstance(lote_existente, dict):
			nome_existente = (lote_existente.get('nome') or '').strip().lower()
			if nome_existente == nome.strip().lower():
				return {'success': False, 'error': f'Já existe um lote com o nome "{nome}". Escolha um nome diferente.'}
	
	# Validação 2: Unidades já vinculadas a outro lote
	units_data = _load_unidades_data()
	units_list = []
	if isinstance(units_data, list):
		units_list = units_data
	elif isinstance(units_data, dict) and isinstance(units_data.get('unidades'), list):
		units_list = units_data.get('unidades')
	
	# Verificar se alguma unidade já está vinculada a outro lote
	unidades_conflitantes = []
	for unidade_nome in unidades:
		for unit in units_list:
			if isinstance(unit, dict):
				unit_nome = (unit.get('nome') or '').strip().lower()
				if unit_nome == str(unidade_nome).strip().lower():
					lote_atual = unit.get('lote_id')
					if lote_atual is not None:
						# Verificar se o lote ainda existe
						lote_existe = False
						for l in lotes:
							if isinstance(l, dict) and l.get('id') == lote_atual:
								lote_existe = True
								lote_nome = l.get('nome', f'Lote ID {lote_atual}')
								unidades_conflitantes.append(f'"{unidade_nome}" (já vinculada ao lote "{lote_nome}")')
								break
						if not lote_existe:
							# Lote não existe mais, liberar a unidade
							unit['lote_id'] = None
	
	if unidades_conflitantes:
		erro_msg = f'As seguintes unidades já estão vinculadas a outros lotes: {", ".join(unidades_conflitantes)}. Remova-as ou desvincule-as primeiro.'
		return {'success': False, 'error': erro_msg}

	existing_ids = [l.get('id') for l in lotes if isinstance(l, dict) and isinstance(l.get('id'), int)]
	new_id = (max(existing_ids) + 1) if existing_ids else 0

	input_unidades = unidades
	unit_ids = []
	created_unit_ids = []

	# Reutilizar units_list já carregado na validação
	units_wrapped = None
	if isinstance(units_data, dict) and isinstance(units_data.get('unidades'), list):
		units_wrapped = units_data

	existing_unit_ids = [u.get('id') for u in units_list if isinstance(u, dict) and isinstance(u.get('id'), int)]
	next_unit_id = (max(existing_unit_ids) + 1) if existing_unit_ids else 0

	def _is_int_like(x):
		try:
			int(x)
			return True
		except Exception:
			return False

	if isinstance(input_unidades, list) and input_unidades and all(_is_int_like(u) for u in input_unidades):
		unit_ids = [int(u) for u in input_unidades]
	else:
		for raw in (input_unidades or []):
			name = str(raw).strip()
			if not name:
				continue
			found = None
			for u in units_list:
				if not isinstance(u, dict):
					continue
				if isinstance(u.get('nome'), str) and u.get('nome').strip().lower() == name.lower():
					found = u
					break
			if found:
				found['lote_id'] = new_id
				unit_ids.append(found.get('id'))
			else:
				uid = next_unit_id
				new_unit = {
					'id': uid,
					'nome': name,
					'lote_id': new_id,
					'criado_em': datetime.now().isoformat()
				}
				units_list.append(new_unit)
				unit_ids.append(uid)
				created_unit_ids.append(uid)
				next_unit_id += 1

	if units_wrapped is not None:
		units_wrapped['unidades'] = units_list
		to_write_units = units_wrapped
	else:
		to_write_units = units_list

	if not _save_unidades_data(to_write_units):
		return {'success': False, 'error': 'Erro ao salvar unidades'}

	lote_record = {
		'id': new_id,
		'nome': str(nome),
		'empresa': str(empresa),
		'numero_contrato': str(numero_contrato),
		'data_inicio': str(data_inicio),
		'data_fim': str(data_fim),
		'valor_contratual': float(valor_contratual) if valor_contratual else 0.0,
		'unidades': unit_ids,
		'precos': precos,
		'ativo': True,
		'criado_em': datetime.now().isoformat()
	}

	lotes.append(lote_record)
	if wrapped is not None:
		wrapped['lotes'] = lotes
		to_write = wrapped
	else:
		to_write = lotes

	ok = _save_lotes_data(to_write)
	if not ok:
		if created_unit_ids:
			try:
				ud = _load_unidades_data() or []
				if isinstance(ud, dict) and isinstance(ud.get('unidades'), list):
					lst = ud.get('unidades')
					lst = [u for u in lst if not (isinstance(u, dict) and u.get('id') in created_unit_ids)]
					ud['unidades'] = lst
				else:
					lst = [u for u in (ud if isinstance(ud, list) else []) if not (isinstance(u, dict) and u.get('id') in created_unit_ids)]
					ud = lst
				_save_unidades_data(ud)
			except Exception:
				pass
		return {'success': False, 'error': 'Erro ao salvar lote'}
	return {'success': True, 'id': new_id}


def editar_lote(lote_id, payload: dict):
	if not isinstance(payload, dict):
		return {'success': False, 'error': 'Payload inválido'}
	
	try:
		lote_id = int(lote_id)
	except Exception:
		return {'success': False, 'error': 'ID de lote inválido'}
	
	data = _load_lotes_data()
	lotes = None
	wrapped = None
	if isinstance(data, list):
		lotes = data
	elif isinstance(data, dict) and isinstance(data.get('lotes'), list):
		lotes = data.get('lotes')
		wrapped = data
	else:
		return {'success': False, 'error': 'Nenhum lote encontrado'}
	
	lote_encontrado = None
	lote_index = None
	for i, l in enumerate(lotes):
		if isinstance(l, dict) and l.get('id') == lote_id:
			lote_encontrado = l
			lote_index = i
			break
	
	if lote_encontrado is None:
		return {'success': False, 'error': f'Lote {lote_id} não encontrado'}
	
	# Atualizar campos básicos
	if 'nome_empresa' in payload or 'empresa' in payload:
		lote_encontrado['empresa'] = payload.get('nome_empresa') or payload.get('empresa')
	if 'numero_contrato' in payload or 'contrato' in payload:
		lote_encontrado['numero_contrato'] = payload.get('numero_contrato') or payload.get('contrato')
	if 'data_inicio' in payload:
		lote_encontrado['data_inicio'] = payload.get('data_inicio')
	if 'data_fim' in payload:
		lote_encontrado['data_fim'] = payload.get('data_fim')
	if 'valor_contratual' in payload or 'valorContratual' in payload:
		valor = payload.get('valor_contratual') or payload.get('valorContratual')
		lote_encontrado['valor_contratual'] = float(valor) if valor else 0.0
	if 'ativo' in payload:
		ativo_val = payload.get('ativo')
		if isinstance(ativo_val, str):
			lote_encontrado['ativo'] = ativo_val.lower() in ('true', '1', 'sim', 'yes')
		else:
			lote_encontrado['ativo'] = bool(ativo_val)
	
	# Atualizar preços
	if 'precos' in payload:
		raw_precos = payload.get('precos')
		precos = {}
		if isinstance(raw_precos, dict):
			precos['cafe_interno'] = raw_precos.get('cafe', {}).get('interno') if isinstance(raw_precos.get('cafe'), dict) else raw_precos.get('cafe_interno') or raw_precos.get('cafeInterno')
			precos['cafe_funcionario'] = raw_precos.get('cafe', {}).get('funcionario') if isinstance(raw_precos.get('cafe'), dict) else raw_precos.get('cafe_funcionario') or raw_precos.get('cafeFuncionario')
			precos['almoco_interno'] = raw_precos.get('almoco', {}).get('interno') if isinstance(raw_precos.get('almoco'), dict) else raw_precos.get('almoco_interno') or raw_precos.get('almocoInterno')
			precos['almoco_funcionario'] = raw_precos.get('almoco', {}).get('funcionario') if isinstance(raw_precos.get('almoco'), dict) else raw_precos.get('almoco_funcionario') or raw_precos.get('almocoFuncionario')
			precos['lanche_interno'] = raw_precos.get('lanche', {}).get('interno') if isinstance(raw_precos.get('lanche'), dict) else raw_precos.get('lanche_interno') or raw_precos.get('lancheInterno')
			precos['lanche_funcionario'] = raw_precos.get('lanche', {}).get('funcionario') if isinstance(raw_precos.get('lanche'), dict) else raw_precos.get('lanche_funcionario') or raw_precos.get('lancheFuncionario')
			precos['jantar_interno'] = raw_precos.get('jantar', {}).get('interno') if isinstance(raw_precos.get('jantar'), dict) else raw_precos.get('jantar_interno') or raw_precos.get('jantarInterno')
			precos['jantar_funcionario'] = raw_precos.get('jantar', {}).get('funcionario') if isinstance(raw_precos.get('jantar'), dict) else raw_precos.get('jantar_funcionario') or raw_precos.get('jantarFuncionario')
			lote_encontrado['precos'] = precos
	
	# Processar unidades (adicionar novas, manter existentes)
	if 'unidades' in payload or 'novas_unidades' in payload:
		units_data = _load_unidades_data()
		units_list = []
		units_wrapped = None
		if isinstance(units_data, list):
			units_list = units_data
		elif isinstance(units_data, dict) and isinstance(units_data.get('unidades'), list):
			units_list = units_data.get('unidades')
			units_wrapped = units_data
		
		# Manter IDs de unidades existentes
		unit_ids_existentes = lote_encontrado.get('unidades', [])
		
		# Adicionar novas unidades se fornecidas
		novas_unidades = payload.get('novas_unidades') or []
		if isinstance(novas_unidades, str):
			novas_unidades = [u.strip() for u in novas_unidades.split(',') if u.strip()]
		
		existing_unit_ids = [u.get('id') for u in units_list if isinstance(u, dict) and isinstance(u.get('id'), int)]
		next_unit_id = (max(existing_unit_ids) + 1) if existing_unit_ids else 0
		
		created_unit_ids = []
		for nome_nova in novas_unidades:
			nome = str(nome_nova).strip()
			if not nome:
				continue
			
			# Verificar se já existe
			found = None
			for u in units_list:
				if isinstance(u, dict) and isinstance(u.get('nome'), str):
					if u.get('nome').strip().lower() == nome.lower():
						found = u
						break
			
			if found:
				# Atualizar lote_id
				found['lote_id'] = lote_id
				if found.get('id') not in unit_ids_existentes:
					unit_ids_existentes.append(found.get('id'))
			else:
				# Criar nova unidade
				uid = next_unit_id
				new_unit = {
					'id': uid,
					'nome': nome,
					'lote_id': lote_id,
					'criado_em': datetime.now().isoformat()
				}
				units_list.append(new_unit)
				unit_ids_existentes.append(uid)
				created_unit_ids.append(uid)
				next_unit_id += 1
		
		lote_encontrado['unidades'] = unit_ids_existentes
		
		# Salvar unidades
		if units_wrapped is not None:
			units_wrapped['unidades'] = units_list
			to_write_units = units_wrapped
		else:
			to_write_units = units_list
		
		if not _save_unidades_data(to_write_units):
			return {'success': False, 'error': 'Erro ao salvar unidades'}
	
	lote_encontrado['atualizado_em'] = datetime.now().isoformat()
	
	lotes[lote_index] = lote_encontrado
	
	if wrapped is not None:
		wrapped['lotes'] = lotes
		to_write = wrapped
	else:
		to_write = lotes
	
	if not _save_lotes_data(to_write):
		return {'success': False, 'error': 'Erro ao salvar alterações'}
	
	return {'success': True, 'lote': lote_encontrado}


def deletar_lote(lote_id):
	try:
		lote_id = int(lote_id)
	except Exception:
		return {'success': False, 'error': 'ID de lote inválido'}
	
	data = _load_lotes_data()
	lotes = None
	wrapped = None
	if isinstance(data, list):
		lotes = data
	elif isinstance(data, dict) and isinstance(data.get('lotes'), list):
		lotes = data.get('lotes')
		wrapped = data
	else:
		return {'success': False, 'error': 'Nenhum lote encontrado'}
	
	lote_index = None
	for i, l in enumerate(lotes):
		if isinstance(l, dict) and l.get('id') == lote_id:
			lote_index = i
			break
	
	if lote_index is None:
		return {'success': False, 'error': f'Lote {lote_id} não encontrado'}
	
	lotes.pop(lote_index)
	
	if wrapped is not None:
		wrapped['lotes'] = lotes
		to_write = wrapped
	else:
		to_write = lotes
	
	if not _save_lotes_data(to_write):
		return {'success': False, 'error': 'Erro ao salvar alterações'}
	
	return {'success': True, 'mensagem': f'Lote {lote_id} deletado com sucesso'}


def obter_lote_por_id(lote_id):
	try:
		lote_id = int(lote_id)
	except Exception:
		return None
	
	data = _load_lotes_data()
	lotes = None
	if isinstance(data, list):
		lotes = data
	elif isinstance(data, dict) and isinstance(data.get('lotes'), list):
		lotes = data.get('lotes')
	else:
		return None
	
	for l in lotes:
		if isinstance(l, dict) and l.get('id') == lote_id:
			return l
	
	return None


def listar_lotes():
	data = _load_lotes_data()
	if isinstance(data, list):
		return data
	elif isinstance(data, dict) and isinstance(data.get('lotes'), list):
		return data.get('lotes')
	return []


def calcular_ultima_atividade_lotes(lotes, mapas):
	"""
	Calcula a última atividade relevante para cada lote.
	
	Args:
		lotes: Lista de lotes
		mapas: Lista de mapas
	
	Returns:
		None (modifica os lotes in-place)
	"""
	for lote in lotes:
		lote_id = lote.get('id')
		mapas_do_lote = [m for m in mapas if m.get('lote_id') == lote_id]
		
		ultima_data = None
		ultima_atividade = "Sem registros"
		
		# Verificar mapas criados/atualizados
		for mapa in mapas_do_lote:
			data_atualizado = mapa.get('atualizado_em')
			data_criado = mapa.get('criado_em')
			
			data_relevante = data_atualizado or data_criado
			if data_relevante:
				try:
					if isinstance(data_relevante, str):
						data_obj = datetime.fromisoformat(data_relevante.replace('Z', '+00:00'))
					else:
						data_obj = data_relevante
					
					if ultima_data is None or data_obj > ultima_data:
						ultima_data = data_obj
						if data_atualizado:
							ultima_atividade = "Mapa atualizado"
						else:
							ultima_atividade = "Mapa cadastrado"
				except:
					pass
		
		# Verificar data de criação do próprio lote
		data_criacao_lote = lote.get('criado_em')
		if data_criacao_lote:
			try:
				if isinstance(data_criacao_lote, str):
					data_obj = datetime.fromisoformat(data_criacao_lote.replace('Z', '+00:00'))
				else:
					data_obj = data_criacao_lote
				
				if ultima_data is None or data_obj > ultima_data:
					ultima_data = data_obj
					ultima_atividade = "Lote criado"
			except:
				pass
		
		# Formatar a data
		if ultima_data:
			lote['ultima_atualizacao'] = ultima_data.strftime('%d/%m/%Y às %H:%M')
			lote['ultima_atividade'] = ultima_atividade
		else:
			lote['ultima_atualizacao'] = "Sem registros"
			lote['ultima_atividade'] = ""
