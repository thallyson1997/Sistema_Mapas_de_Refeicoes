# Função utilitária para carregar mapas do banco como lista de dicts
def serialize_mapa(m):
	# Serializa um registro Mapa do banco para dict, garantindo todos os campos necessários
	mapa_dict = {c.name: getattr(m, c.name) for c in m.__table__.columns}
	# Lista de todos os campos que podem ser JSON
	json_fields = [
		'cafe_interno_siisp', 'cafe_funcionario_siisp',
		'almoco_interno_siisp', 'almoco_funcionario_siisp',
		'lanche_interno_siisp', 'lanche_funcionario_siisp',
		'jantar_interno_siisp', 'jantar_funcionario_siisp',
		'dados_siisp', 'cafe_interno', 'cafe_funcionario',
		'almoco_interno', 'almoco_funcionario',
		'lanche_interno', 'lanche_funcionario',
		'jantar_interno', 'jantar_funcionario', 'datas'
	]
	for field in json_fields:
		if field in mapa_dict and isinstance(mapa_dict[field], str):
			try:
				mapa_dict[field] = json.loads(mapa_dict[field])
			except Exception:
				mapa_dict[field] = []
		elif field in mapa_dict and mapa_dict[field] is None:
			mapa_dict[field] = []
	# Garante que todos os campos existam
	for field in json_fields:
		if field not in mapa_dict:
			mapa_dict[field] = []
	return mapa_dict

def carregar_mapas_db(filtros=None):
	from .models import Mapa
	query = Mapa.query
	if filtros:
		for k, v in filtros.items():
			query = query.filter(getattr(Mapa, k) == v)
	mapas_db = query.all()
	mapas = [serialize_mapa(m) for m in mapas_db]
	return mapas
import json
import re
import os
import glob
import calendar
from datetime import datetime
from collections import defaultdict



# ----- Data Validation Helpers -----
def _get_lote_data_inicio(lote_id):
	"""
	Obtém a data de início do contrato de um lote.
	
	Args:
		lote_id: ID do lote
	
	Returns:
		datetime ou None se não encontrado ou inválido
	"""
	try:
		from .models import Lote
		lote = Lote.query.get(int(lote_id))
		if lote and lote.data_inicio:
			try:
				return datetime.strptime(lote.data_inicio, '%Y-%m-%d')
			except Exception:
				return None
		return None
	except Exception as e:
		print(f"❌ Erro ao buscar data de início do lote {lote_id}: {e}")
		return None


def _get_lote_data_fim(lote_id):
	"""
	Obtém a data de fim do contrato de um lote.
	
	Args:
		lote_id: ID do lote
	
	Returns:
		datetime ou None se não encontrado ou inválido
	"""
	try:
		from .models import Lote
		lote = Lote.query.get(int(lote_id))
		if lote and lote.data_fim:
			try:
				return datetime.strptime(lote.data_fim, '%Y-%m-%d')
			except Exception:
				return None
		return None
	except Exception as e:
		print(f"❌ Erro ao buscar data de fim do lote {lote_id}: {e}")
		return None


# ----- SIISP Comparison Helpers -----
def _calcular_campos_comparativos_siisp(record):
	if not isinstance(record, dict):
		return
	
	meal_fields = [
		'cafe_interno', 'cafe_funcionario',
		'almoco_interno', 'almoco_funcionario', 
		'lanche_interno', 'lanche_funcionario',
		'jantar_interno', 'jantar_funcionario'
	]
	
	dados_siisp = record.get('dados_siisp', [])
	if not isinstance(dados_siisp, list):
		dados_siisp = []
	
	for field in meal_fields:
		field_data = record.get(field, [])
		if not isinstance(field_data, list):
			field_data = []
		
		siisp_field = f"{field}_siisp"
		
		comparativo = []
		max_len = max(len(field_data), len(dados_siisp))
		
		for i in range(max_len):
			refeicao_val = field_data[i] if i < len(field_data) else 0
			siisp_val = dados_siisp[i] if i < len(dados_siisp) else 0
			
			try:
				refeicao_num = int(refeicao_val) if refeicao_val is not None else 0
			except (ValueError, TypeError):
				refeicao_num = 0
			
			try:
				siisp_num = int(siisp_val) if siisp_val is not None else 0
			except (ValueError, TypeError):
				siisp_num = 0
			
			diferenca = refeicao_num - siisp_num
			comparativo.append(diferenca)
		
		record[siisp_field] = comparativo


# ----- Text Parsing Helpers -----
def parse_texto_tabular(texto):
	if texto is None:
		return {'ok': False, 'error': 'Texto vazio'}
	if not isinstance(texto, str):
		try:
			texto = str(texto)
		except Exception:
			return {'ok': False, 'error': 'Texto não serializável'}

	lines = [ln.strip() for ln in texto.splitlines() if ln.strip()]
	if not lines:
		return {'ok': True, 'colunas': {}, 'linhas': 0, 'colunas_count': 0}

	delimiter = '\t' if any('\t' in ln for ln in lines) else None

	rows = []
	for ln in lines:
		if delimiter:
			parts = [p.strip() for p in ln.split('\t')]
		else:
			parts = [p.strip() for p in re.split(r"\s+", ln) if p.strip()]
		rows.append(parts)

	max_cols = max(len(r) for r in rows)

	cols = {f'coluna_{i}': [] for i in range(max_cols)}

	def _to_number(token):
		if token is None:
			return None
		t = str(token).strip()
		if t == '':
			return None
		t2 = t.replace(',', '.')
		m = re.match(r'^[-+]?\d+(?:\.\d+)?$', t2)
		if m:
			if '.' in t2:
				try:
					return float(t2)
				except Exception:
					return None
			else:
				try:
					return int(t2)
				except Exception:
					try:
						return float(t2)
					except Exception:
						return None
		m2 = re.search(r'[-+]?\d+[\.,]?\d*', t)
		if m2:
			s = m2.group(0).replace(',', '.')
			try:
				if '.' in s:
					return float(s)
				return int(s)
			except Exception:
				try:
					return float(s)
				except Exception:
					return None
		return None

	for r in rows:
		for idx in range(max_cols):
			token = r[idx] if idx < len(r) else ''
			num = _to_number(token)
			cols[f'coluna_{idx}'].append(num)

	return {'ok': True, 'colunas': cols, 'linhas': len(rows), 'colunas_count': max_cols}


def _normalizar_datas_coluna(col0_values, entry):
	if not isinstance(col0_values, list):
		return None

	mes_keys = ('mes', 'month', 'mes_num', 'mesNumero', 'month_num')
	ano_keys = ('ano', 'year')
	mes = None
	ano = None
	for k in mes_keys:
		if k in entry and entry.get(k) is not None:
			try:
				mes = int(entry.get(k))
				break
			except Exception:
				try:
					mes = int(str(entry.get(k)).strip())
					break
				except Exception:
					mes = None
	for k in ano_keys:
		if k in entry and entry.get(k) is not None:
			try:
				ano = int(entry.get(k))
				break
			except Exception:
				try:
					ano = int(str(entry.get(k)).strip())
					break
				except Exception:
					ano = None

	now = datetime.now()
	if mes is None:
		mes = now.month
	if ano is None:
		ano = now.year

	try:
		days_in_month = calendar.monthrange(ano, mes)[1]
	except Exception:
		days_in_month = 31

	out = []
	for v in col0_values:
		if v is None:
			out.append(None)
			continue
		if isinstance(v, (int,)):
			day = int(v)
		else:
			s = str(v).strip()
			if not s:
				out.append(None)
				continue
			if '/' in s or '-' in s:
				parts = re.split(r'[\/\-]', s)
				day = None
				for p in parts:
					m = re.search(r'(\d{1,2})', p)
					if m:
						try:
							day = int(m.group(1))
							break
						except Exception:
							day = None
				if day is None:
					nm = re.search(r'(\d{1,2})', s)
					day = int(nm.group(1)) if nm else None
			else:
				m = re.search(r'(\d{1,2})', s)
				if m:
					try:
						day = int(m.group(1))
					except Exception:
						day = None
				else:
					day = None

		try:
			if day is None or day < 1 or day > days_in_month:
				out.append(None)
			else:
				dt = datetime(year=ano, month=mes, day=day)
				out.append(dt.strftime('%d/%m/%Y'))
		except Exception:
			out.append(None)

	return out


# ----- Validation Helpers -----
def _get_days_in_month_from_entry(entry):
	mes_keys = ('mes', 'month', 'mes_num', 'mesNumero', 'month_num')
	ano_keys = ('ano', 'year')
	mes = None
	ano = None
	for k in mes_keys:
		if k in entry and entry.get(k) is not None:
			try:
				mes = int(entry.get(k))
				break
			except Exception:
				try:
					mes = int(str(entry.get(k)).strip())
					break
				except Exception:
					mes = None
	for k in ano_keys:
		if k in entry and entry.get(k) is not None:
			try:
				ano = int(entry.get(k))
				break
			except Exception:
				try:
					ano = int(str(entry.get(k)).strip())
					break
				except Exception:
					ano = None
	if mes is None or ano is None:
		return None
	try:
		return calendar.monthrange(ano, mes)[1]
	except Exception:
		return None


def _validate_map_day_lengths(entry):
	# Usar campo 'linhas' se existir (dados já filtrados)
	# Senão calcular dias do mês
	if 'linhas' in entry:
		expected = int(entry['linhas'])
	else:
		days = _get_days_in_month_from_entry(entry)
		if days is None:
			return (False, 'Mês ou ano inválido ou ausente no registro')
		expected = int(days)

	daily_fields = [
		'dados_siisp',
		'cafe_interno', 'cafe_funcionario',
		'almoco_interno', 'almoco_funcionario',
		'lanche_interno', 'lanche_funcionario',
		'jantar_interno', 'jantar_funcionario',
		'datas'
	]
	errors = []
	for f in daily_fields:
		if f in entry:
			v = entry.get(f)
			if not isinstance(v, list):
				errors.append(f"{f} não é uma lista")
			else:
				if f == 'dados_siisp':
					if len(v) not in (0, expected):
						errors.append(f"{f} tem {len(v)} elementos; esperado 0 ou {expected}")
				else:
					if len(v) != expected:
						errors.append(f"{f} tem {len(v)} elementos; esperado {expected}")
	if errors:
		return (False, '; '.join(errors))
	return (True, None)


# ----- File Path Helpers -----

# Funções CRUD usando banco de dados
from .models import db, Mapa


# ----- Data Loading/Saving -----
def _load_mapas_data():
	base_dir = os.path.dirname(os.path.dirname(__file__))
	mapas_path = os.path.join(base_dir, 'dados', 'mapas.json')
	if not os.path.isfile(mapas_path):
		return None
	try:
		with open(mapas_path, 'r', encoding='utf-8') as f:
			data = json.load(f)
			return data
	except Exception as e:
		print(f"❌ Erro ao ler mapas.json: {e}")
		return None


def _save_mapas_data(data):
	base_dir = os.path.dirname(os.path.dirname(__file__))
	mapas_path = os.path.join(base_dir, 'dados', 'mapas.json')
	try:
		os.makedirs(os.path.dirname(mapas_path), exist_ok=True)
		tmp_path = mapas_path + '.tmp'
		with open(tmp_path, 'w', encoding='utf-8') as f:
			json.dump(data, f, ensure_ascii=False, indent=2)
		os.replace(tmp_path, mapas_path)
		return True
	except Exception:
		return False



def _load_mapas_partitioned(mes, ano):
	# Busca mapas por mês/ano
	return Mapa.query.filter_by(mes=mes, ano=ano).all()



# Não é mais necessário salvar em arquivo, mapas são salvos no banco
def _save_mapas_partitioned(mapas_list, mes, ano):
	# Salva lista de mapas no banco
	try:
		for mapa_data in mapas_list:
			mapa = Mapa.query.filter_by(mes=mes, ano=ano, unidade=mapa_data.get('unidade'), lote_id=mapa_data.get('lote_id')).first()
			if mapa:
				# Atualiza sempre com o valor do dicionário, serializando listas
				for k, v in mapa_data.items():
					if hasattr(mapa, k):
						if isinstance(v, list):
							setattr(mapa, k, json.dumps(v))
						else:
							setattr(mapa, k, v)
				mapa.atualizado_em = datetime.now().isoformat()
			else:
				# Cria novo registro, serializando listas
				novo_mapa = Mapa(**{k: json.dumps(v) if isinstance(v, list) else v for k, v in mapa_data.items() if hasattr(Mapa, k)})
				db.session.add(novo_mapa)
		db.session.commit()
		return True
	except Exception as e:
		print(f"❌ Erro ao salvar mapas: {e}")
		db.session.rollback()
		return False


def _load_mapas_by_period(mes_inicio, ano_inicio, mes_fim, ano_fim):
	mapas_agregados = []
	
	ano_atual = ano_inicio
	mes_atual = mes_inicio
	
	while (ano_atual < ano_fim) or (ano_atual == ano_fim and mes_atual <= mes_fim):
		mapas_mes = _load_mapas_partitioned(mes_atual, ano_atual)
		if mapas_mes:
			mapas_agregados.extend(mapas_mes)
			print(f"📂 Carregados {len(mapas_mes)} mapas de {mes_atual:02d}/{ano_atual}")
		
		mes_atual += 1
		if mes_atual > 12:
			mes_atual = 1
			ano_atual += 1
	
	return mapas_agregados


def _load_all_mapas_partitioned():
	# Retorna todos os mapas do banco
	return Mapa.query.all()
def _detect_mes_ano_from_entry(entry):
	if not isinstance(entry, dict):
		return (None, None)
	
	mes_keys = ('mes', 'month', 'mes_num', 'mesNumero', 'month_num')
	ano_keys = ('ano', 'year')
	
	mes = None
	ano = None
	
	for k in mes_keys:
		if k in entry:
			try:
				mes = int(entry[k])
				break
			except (ValueError, TypeError):
				continue
	
	for k in ano_keys:
		if k in entry:
			try:
				ano = int(entry[k])
				break
			except (ValueError, TypeError):
				continue
	
	return (mes, ano)


# ----- Main Map Operations -----

def salvar_mapas_raw(payload):
	try:
		entries = payload if isinstance(payload, list) else [payload or {}]
		saved_ids = []
		saved_records = []
		# Lista de todos os campos do modelo Mapa
		mapa_fields = [
			'lote_id', 'mes', 'ano', 'unidade', 'linhas', 'colunas_count',
			'dados_siisp', 'cafe_interno', 'cafe_funcionario', 'almoco_interno', 'almoco_funcionario',
			'lanche_interno', 'lanche_funcionario', 'jantar_interno', 'jantar_funcionario',
			'datas', 'criado_em', 'atualizado_em',
			'cafe_interno_siisp', 'cafe_funcionario_siisp', 'almoco_interno_siisp', 'almoco_funcionario_siisp',
			'lanche_interno_siisp', 'lanche_funcionario_siisp', 'jantar_interno_siisp', 'jantar_funcionario_siisp'
		]
		for entry in entries:
			mes, ano = _detect_mes_ano_from_entry(entry)
			unidade = entry.get('unidade')
			lote_id = entry.get('lote_id')
			if not (mes and ano and unidade and lote_id):
				continue
			# Se houver campo texto tabular, converter para listas
			possible_text_keys = ('texto', 'conteudo', 'dados', 'texto_raw', 'texto_mapas', 'mapa_texto')
			text_val = None
			used_text_key = None
			for k in possible_text_keys:
				if k in entry and entry.get(k) is not None:
					text_val = entry.get(k)
					used_text_key = k
					break
			if text_val is not None:
				parsed = parse_texto_tabular(text_val)
				if parsed.get('ok'):
					cols = parsed.get('colunas') or {}
					for ck, cv in cols.items():
						entry[ck] = cv
					entry['linhas'] = parsed.get('linhas')
					entry['colunas_count'] = parsed.get('colunas_count')
					col_count = int(parsed.get('colunas_count') or 0)
					if col_count == 1:
						if 'coluna_0' in entry:
							entry['dados_siisp'] = entry.pop('coluna_0')
						else:
							entry['dados_siisp'] = []
					else:
						col_rename_map = {
							'coluna_1': 'cafe_interno',
							'coluna_2': 'cafe_funcionario',
							'coluna_3': 'almoco_interno',
							'coluna_4': 'almoco_funcionario',
							'coluna_5': 'lanche_interno',
							'coluna_6': 'lanche_funcionario',
							'coluna_7': 'jantar_interno',
							'coluna_8': 'jantar_funcionario'
						}
						for oldk, newk in col_rename_map.items():
							if oldk in entry:
								entry[newk] = entry.pop(oldk)
						if 'coluna_0' in entry:
							try:
								datas = _normalizar_datas_coluna(entry.get('coluna_0'), entry)
								entry.pop('coluna_0', None)
								entry['datas'] = datas
							except Exception:
								pass
					# --- Recorte dos arrays após parsing tabular ---
						# Só recorta se houver data_inicio/data_fim, mes, ano
						data_inicio = entry.get('data_inicio')
						data_fim = entry.get('data_fim')
						mes = entry.get('mes')
						ano = entry.get('ano')
						if data_inicio and data_fim and mes and ano:
							try:
								data_inicio_dt = datetime.strptime(str(data_inicio), "%Y-%m-%d")
								data_fim_dt = datetime.strptime(str(data_fim), "%Y-%m-%d")
								dias_do_mes = [datetime(int(ano), int(mes), d+1) for d in range(calendar.monthrange(int(ano), int(mes))[1])]
								indices_validos = [i for i, dia in enumerate(dias_do_mes) if data_inicio_dt <= dia <= data_fim_dt]
								campos_refeicoes = [
									'cafe_interno', 'cafe_funcionario', 'almoco_interno', 'almoco_funcionario',
									'lanche_interno', 'lanche_funcionario', 'jantar_interno', 'jantar_funcionario'
								]
								for campo in campos_refeicoes:
									vals = entry.get(campo)
									if isinstance(vals, list):
										entry[campo] = [vals[i] for i in indices_validos]
								# Recortar dados_siisp usando os mesmos índices válidos, mesmo se já for lista
								if 'dados_siisp' in entry and isinstance(entry['dados_siisp'], list):
									entry['dados_siisp'] = [entry['dados_siisp'][i] for i in indices_validos if i < len(entry['dados_siisp'])]
								if 'datas' in entry and isinstance(entry['datas'], list):
									entry['datas'] = [entry['datas'][i] for i in indices_validos if i < len(entry['datas'])]
							except Exception as e:
								print(f"[DEBUG] Erro ao recortar arrays após parsing tabular: {e}")
				if used_text_key:
					try:
						entry.pop(used_text_key, None)
					except Exception:
						pass
			mapa = Mapa.query.filter_by(mes=mes, ano=ano, unidade=unidade, lote_id=lote_id).first()
			mapa_data = {}

			# Usar o tamanho real dos arrays recortados
			meal_fields = [
				'cafe_interno', 'cafe_funcionario',
				'almoco_interno', 'almoco_funcionario',
				'lanche_interno', 'lanche_funcionario',
				'jantar_interno', 'jantar_funcionario'
			]
			# Descobrir o tamanho real dos dados (prioridade: primeiro campo de refeição válido, depois dados_siisp, depois datas)
			tamanho_real = None
			for field in meal_fields:
				val = entry.get(field)
				if isinstance(val, list) and len(val) > 0:
					tamanho_real = len(val)
					break
			if tamanho_real is None or tamanho_real == 0:
				dados_siisp = entry.get('dados_siisp')
				if isinstance(dados_siisp, list) and len(dados_siisp) > 0:
					tamanho_real = len(dados_siisp)
			if tamanho_real is None or tamanho_real == 0:
				datas = entry.get('datas')
				if isinstance(datas, list) and len(datas) > 0:
					tamanho_real = len(datas)
			# Se ainda for None ou zero, usa o número de dias do mês
			if (tamanho_real is None or tamanho_real == 0) and mes and ano:
				try:
					tamanho_real = calendar.monthrange(int(ano), int(mes))[1]
				except Exception:
					tamanho_real = 0
			if tamanho_real is None:
				tamanho_real = 0

			# Preencher dados_siisp corretamente (parse string if needed)
			dados_siisp = entry.get('dados_siisp')
			if isinstance(dados_siisp, str):
				parsed_siisp = parse_texto_tabular(dados_siisp)
				if parsed_siisp.get('ok') and 'coluna_0' in parsed_siisp.get('colunas', {}):
					dados_siisp = parsed_siisp['colunas']['coluna_0']
				else:
					dados_siisp = None
			# Garante que dados_siisp seja sempre uma lista de zeros se estiver vazio ou não for lista
			if not isinstance(dados_siisp, list) or len(dados_siisp) == 0:
				dados_siisp = [0] * tamanho_real
			# Se por algum motivo ainda estiver vazio, força preenchimento
			if isinstance(dados_siisp, list) and len(dados_siisp) == 0 and tamanho_real > 0:
				dados_siisp = [0] * tamanho_real
			# Se houver indices_validos, recorta usando eles; senão, recorta para o tamanho real
			if 'indices_validos' in locals() and isinstance(indices_validos, list) and len(indices_validos) == tamanho_real:
				dados_siisp = [dados_siisp[i] for i in indices_validos if i < len(dados_siisp)]
			elif len(dados_siisp) != tamanho_real:
				dados_siisp = dados_siisp[:tamanho_real]
			# Força preenchimento com zeros se ainda estiver vazio
			if isinstance(dados_siisp, list) and len(dados_siisp) == 0 and tamanho_real > 0:
				dados_siisp = [0] * tamanho_real
			print(f"[DEBUG] dados_siisp a salvar: {dados_siisp}, tamanho_real: {tamanho_real}")
			mapa_data['dados_siisp'] = json.dumps(dados_siisp)

			# Preencher campos de refeições
			for field in meal_fields:
				val = entry.get(field)
				if isinstance(val, list):
					if len(val) != tamanho_real:
						val = val[:tamanho_real]
					mapa_data[field] = json.dumps(val)
				else:
					mapa_data[field] = json.dumps([0] * tamanho_real)

			# Calcular *_siisp = campo - dados_siisp
			for field in meal_fields:
				campo = json.loads(mapa_data[field])
				siisp = [campo[i] - dados_siisp[i] if i < len(campo) and i < len(dados_siisp) else 0 for i in range(tamanho_real)]
				mapa_data[f'{field}_siisp'] = json.dumps(siisp)

			# Preencher datas
			datas = entry.get('datas')
			if isinstance(datas, list):
				if len(datas) != tamanho_real:
					datas = datas[:tamanho_real]
				mapa_data['datas'] = json.dumps(datas)
			else:
				mapa_data['datas'] = json.dumps([])

			# Preencher outros campos
			for field in mapa_fields:
				if field in mapa_data:
					continue
				val = entry.get(field)
				if isinstance(val, list):
					mapa_data[field] = json.dumps(val)
				elif val is not None:
					mapa_data[field] = val
				elif field in ['linhas', 'colunas_count', 'lote_id', 'mes', 'ano']:
					mapa_data[field] = 0
				elif field in ['criado_em', 'atualizado_em']:
					mapa_data[field] = datetime.now().isoformat()
				else:
					mapa_data[field] = ''
			if mapa:
				for k, v in mapa_data.items():
					setattr(mapa, k, v)
				mapa.atualizado_em = datetime.now().isoformat()
				db.session.commit()
				saved_ids.append(mapa.id)
				saved_records.append(mapa)
			else:
				novo_mapa = Mapa(**mapa_data)
				db.session.add(novo_mapa)
				db.session.commit()
				saved_ids.append(novo_mapa.id)
				saved_records.append(novo_mapa)
		return {'success': True, 'ids': saved_ids, 'registros': [m.id for m in saved_records]}
	except Exception as e:
		db.session.rollback()
		return {'success': False, 'error': f'Erro ao salvar mapas: {e}'}


def preparar_dados_entrada_manual(data):
	try:
		if not isinstance(data, dict):
			return {'success': False, 'error': 'Dados inválidos'}
		
		import copy
		processed = copy.deepcopy(data)
		
		meal_fields = [
			'cafe_interno', 'cafe_funcionario',
			'almoco_interno', 'almoco_funcionario', 
			'lanche_interno', 'lanche_funcionario',
			'jantar_interno', 'jantar_funcionario'
		]
		
		if 'dados_tabela' in processed and isinstance(processed['dados_tabela'], list):
			tabela = processed['dados_tabela']
			
			for field in meal_fields:
				processed[field] = []
			
			for dia_data in tabela:
				for field in meal_fields:
					valor = dia_data.get(field, 0)
					try:
						valor_int = int(valor) if valor is not None and valor != '' else 0
					except (ValueError, TypeError):
						valor_int = 0
					processed[field].append(valor_int)
			
			del processed['dados_tabela']
		
		else:
			def normalizar_array(arr):
				if not isinstance(arr, list):
					return []
				normalized = []
				for item in arr:
					if item is None or item == '' or item == 'null':
						normalized.append(0)
					else:
						try:
							normalized.append(int(item))
						except (ValueError, TypeError):
							normalized.append(0)
				return normalized
			
			for field in meal_fields:
				if field in processed:
					processed[field] = normalizar_array(processed.get(field))
		
		max_days = 0
		for field in meal_fields:
			if field in processed and isinstance(processed[field], list):
				max_days = max(max_days, len(processed[field]))
		
		mes = processed.get('mes')
		ano = processed.get('ano')
		
		# Verificar data de início e fim do contrato
		lote_id = processed.get('lote_id')
		data_inicio = None
		data_fim = None
		if lote_id:
			try:
				data_inicio = _get_lote_data_inicio(int(lote_id))
				data_fim = _get_lote_data_fim(int(lote_id))
			except:
				pass
		
		datas = []
		
		if mes and ano:
			try:
				mes = int(mes)
				ano = int(ano)
				days_in_month = calendar.monthrange(ano, mes)[1]
				num_days = min(max_days, days_in_month) if max_days > 0 else days_in_month
				
				# Filtrar por data de início e fim
				indices_validos = []
				for dia in range(1, num_days + 1):
					data_dia = datetime(ano, mes, dia)
					valido = True
					if data_inicio and data_dia < data_inicio:
						valido = False
					if data_fim and data_dia > data_fim:
						valido = False
					if valido:
						indices_validos.append(dia - 1)
						datas.append(f"{dia:02d}/{mes:02d}/{ano}")
				
				# Filtrar arrays
				if (data_inicio or data_fim) and len(indices_validos) < num_days:
					for field in meal_fields:
						if field in processed and isinstance(processed[field], list):
							arr = processed[field]
							processed[field] = [arr[i] if i < len(arr) else 0 for i in indices_validos]
					max_days = len(indices_validos)
			except:
				for dia in range(1, max_days + 1):
					data_str = f"{dia:02d}/01/2025"
					datas.append(data_str)
		
		if len(datas) == 0 and (data_inicio or data_fim):
			return {'success': False, 'error': f'Todos os dias estão fora do período do contrato.'}
		
		processed['datas'] = datas
		processed['linhas'] = len(datas)
		processed['colunas_count'] = 9
		
		processed['criado_em'] = datetime.now().isoformat()
		
		if 'dados_siisp' not in processed:
			processed['dados_siisp'] = []
		
		if not processed.get('dados_siisp') or len(processed.get('dados_siisp', [])) == 0:
			# Usar tamanho filtrado
			processed['dados_siisp'] = [0] * len(datas) if len(datas) > 0 else []
		
		_calcular_campos_comparativos_siisp(processed)
		
		return {'success': True, 'data': processed}
	except Exception as e:
		return {'success': False, 'error': f'Erro ao preparar dados: {str(e)}'}


def reordenar_registro_mapas(registro_id):
	try:
		base_dir = os.path.dirname(os.path.dirname(__file__))
		mapas_file = os.path.join(base_dir, 'dados', 'mapas.json')
		
		if not os.path.exists(mapas_file):
			return False
		
		with open(mapas_file, 'r', encoding='utf-8') as f:
			mapas_data = json.load(f)
		
		if not isinstance(mapas_data, list):
			return False
		
		for i, mapa in enumerate(mapas_data):
			if isinstance(mapa, dict) and mapa.get('id') == registro_id:
				field_order = [
					'lote_id', 'mes', 'ano', 'unidade', 'dados_siisp', 'linhas', 'colunas_count',
					'cafe_interno', 'cafe_funcionario', 'almoco_interno', 'almoco_funcionario',
					'lanche_interno', 'lanche_funcionario', 'jantar_interno', 'jantar_funcionario',
					'datas', 'id', 'criado_em', 'atualizado_em'
				]
				
				ordered_data = {}
				for field in field_order:
					if field in mapa:
						ordered_data[field] = mapa[field]
				
				for field, value in mapa.items():
					if field not in ordered_data:
						ordered_data[field] = value
				
				mapas_data[i] = ordered_data
				break
		
		with open(mapas_file, 'w', encoding='utf-8') as f:
			json.dump(mapas_data, f, indent=2, ensure_ascii=False)
		
		return True
		
	except Exception:
		return False



def excluir_mapa(payload):
	if not isinstance(payload, dict):
		return {'success': False, 'error': 'Payload inválido'}
	unidade = payload.get('unidade', '').strip()
	mes = payload.get('mes')
	ano = payload.get('ano')
	lote_id = payload.get('lote_id')
	if not unidade or not mes or not ano:
		return {'success': False, 'error': 'Campos obrigatórios ausentes: unidade, mes, ano'}
	try:
		mes = int(mes)
		ano = int(ano)
		if lote_id is not None:
			lote_id = int(lote_id)
	except Exception:
		return {'success': False, 'error': 'Valores inválidos para mes, ano ou lote_id'}
	mapa = Mapa.query.filter_by(mes=mes, ano=ano, unidade=unidade, lote_id=lote_id).first()
	if not mapa:
		return {'success': False, 'error': f'Mapa não encontrado para Unidade "{unidade}", período {mes:02d}/{ano}.'}
	mapa_id = mapa.id
	try:
		db.session.delete(mapa)
		db.session.commit()
		return {'success': True, 'mensagem': f'Mapa {mapa_id} da unidade "{unidade}" ({mes:02d}/{ano}) excluído com sucesso.', 'id': mapa_id}
	except Exception as e:
		db.session.rollback()
		return {'success': False, 'error': f'Erro ao excluir mapa: {e}'}


def calcular_metricas_lotes(lotes, mapas):
	"""
	Calcula métricas de refeições, custos e desvios para cada lote.
	Modifica os lotes in-place adicionando as métricas calculadas.
	
	Args:
		lotes: Lista de lotes
		mapas: Lista de mapas
	
	Returns:
		None (modifica os lotes in-place)
	"""
	# print removido: [DEBUG] Iniciando calcular_metricas_lotes
	meses_por_lote = defaultdict(set)
	totais_refeicoes_por_lote = {}
	totais_custos_por_lote = {}
	totais_desvios_por_lote = {}

	for m in (mapas or []):
		# Se for objeto, converte para dict
		if not isinstance(m, dict):
			try:
				m = serialize_mapa(m)
			except Exception:
				pass
				pass
				continue
		try:
			lote_id = int(m.get('lote_id'))
		except Exception:
			# print removido: [DEBUG] lote_id inválido em mapa
			continue

		mes = m.get('mes') or m.get('month') or m.get('mes_num') or m.get('month_num')
		ano = m.get('ano') or m.get('year')

		if (mes is None or ano is None) and isinstance(m.get('datas'), list) and len(m.get('datas')) > 0:
				parts = str(m.get('datas')[0]).split('/')
				if len(parts) >= 3:
					mes = int(parts[1])
					ano = int(parts[2])
				# print removido: [DEBUG] Erro ao extrair mes/ano de datas
				pass

		try:
			mes_i = int(mes)
			ano_i = int(ano)
		except Exception:
			# print removido: [DEBUG] mes/ano inválido
			continue

		meses_por_lote[lote_id].add((mes_i, ano_i))

		if 'refeicoes_mes' in m and m.get('refeicoes_mes') not in [None, '', 0, '0', 0.0]:
			try:
				total = int(m.get('refeicoes_mes') or 0)
			except Exception:
				try:
					total = int(float(m.get('refeicoes_mes') or 0))
				except Exception:
					total = 0
		else:
			# Calcular somando todos os campos de refeições
			total = 0
			for campo in ['cafe_interno', 'cafe_funcionario', 'almoco_interno', 'almoco_funcionario', 'lanche_interno', 'lanche_funcionario', 'jantar_interno', 'jantar_funcionario']:
				vals = m.get(campo, [])
				if isinstance(vals, list):
					soma = sum(int(x) if x is not None else 0 for x in vals)
					total += soma

		# print removido: [DEBUG] Mapa lote_id=..., total_refeicoes=...
		def soma_positivos(lista):
			total = 0
			for x in lista:
				try:
					val = float(x)
					if val > 0:
						total += val
				except (ValueError, TypeError):
					continue
			return total

		for l_temp in lotes:
			try:
				if int(l_temp.get('id')) == lote_id:
					precos = l_temp.get('precos', {})
					break
			except Exception:
				continue

		def get_preco(refeicao, tipo):
			if isinstance(precos.get(refeicao), dict):
				valor = precos[refeicao].get(tipo, 0)
			else:
				chave = f"{refeicao}_{tipo}"
				valor = precos.get(chave, 0)
			try:
				return float(valor)
			except (ValueError, TypeError):
				return 0.0

		# print removido: [DEBUG] cafe_interno_siisp soma_positivos
		# print removido: [DEBUG] dados_siisp
		# print removido: [DEBUG] cafe_funcionario_siisp soma_positivos
		# print removido: [DEBUG] almoco_interno_siisp soma_positivos
		# print removido: [DEBUG] almoco_funcionario_siisp soma_positivos
		# print removido: [DEBUG] lanche_interno_siisp soma_positivos
		# print removido: [DEBUG] lanche_funcionario_siisp soma_positivos
		# print removido: [DEBUG] jantar_interno_siisp soma_positivos
		# print removido: [DEBUG] jantar_funcionario_siisp soma_positivos
		desvio_total_produtos = (
			soma_positivos(m.get('cafe_interno_siisp', [])) * get_preco('cafe', 'interno') +
			soma_positivos(m.get('cafe_funcionario_siisp', [])) * get_preco('cafe', 'funcionario') +
			soma_positivos(m.get('almoco_interno_siisp', [])) * get_preco('almoco', 'interno') +
			soma_positivos(m.get('almoco_funcionario_siisp', [])) * get_preco('almoco', 'funcionario') +
			soma_positivos(m.get('lanche_interno_siisp', [])) * get_preco('lanche', 'interno') +
			soma_positivos(m.get('lanche_funcionario_siisp', [])) * get_preco('lanche', 'funcionario') +
			soma_positivos(m.get('jantar_interno_siisp', [])) * get_preco('jantar', 'interno') +
			soma_positivos(m.get('jantar_funcionario_siisp', [])) * get_preco('jantar', 'funcionario')
		)

		custo_mapa = 0.0
		desvio_mapa = 0.0
		lote_do_mapa = None
		for l_temp in lotes:
			try:
				if int(l_temp.get('id')) == lote_id:
					lote_do_mapa = l_temp
					break
			except Exception:
				pass

		# Fim do bloco for/try/except
		if lote_do_mapa and isinstance(lote_do_mapa.get('precos'), dict):
			precos = lote_do_mapa.get('precos', {})

			def get_preco(refeicao, tipo):
				if isinstance(precos.get(refeicao), dict):
					valor = precos[refeicao].get(tipo, 0)
				else:
					chave = f"{refeicao}_{tipo}"
					valor = precos.get(chave, 0)
				try:
					return float(valor)
				except (ValueError, TypeError):
					return 0.0

			meal_fields = [
				('cafe_interno', get_preco('cafe', 'interno')),
				('cafe_funcionario', get_preco('cafe', 'funcionario')),
				('almoco_interno', get_preco('almoco', 'interno')),
				('almoco_funcionario', get_preco('almoco', 'funcionario')),
				('lanche_interno', get_preco('lanche', 'interno')),
				('lanche_funcionario', get_preco('lanche', 'funcionario')),
				('jantar_interno', get_preco('jantar', 'interno')),
				('jantar_funcionario', get_preco('jantar', 'funcionario'))
			]

			for field_name, preco_unitario in meal_fields:
				if field_name in m and isinstance(m[field_name], list):
					try:
						quantidade = sum(int(x) if x is not None else 0 for x in m[field_name])
						custo_mapa += quantidade * preco_unitario
					except Exception:
						# print removido: [DEBUG] Erro ao somar ...
						pass

			# Calcular desvios baseado em discrepâncias SIISP
			for i in range(len(m.get('data', []))):
				siisp = m.get('dados_siisp', [])[i] if m.get('dados_siisp') and i < len(m.get('dados_siisp', [])) else 0
				if siisp > 0:
					if m.get('cafe_interno_siisp') and i < len(m.get('cafe_interno_siisp', [])):
						excedente_cafe = max(0, m['cafe_interno_siisp'][i])
						desvio_mapa += excedente_cafe * get_preco('cafe', 'interno')
					if m.get('almoco_interno_siisp') and i < len(m.get('almoco_interno_siisp', [])):
						excedente_almoco = max(0, m['almoco_interno_siisp'][i])
					if m.get('lanche_interno_siisp') and i < len(m.get('lanche_interno_siisp', [])):
						excedente_lanche = max(0, m['lanche_interno_siisp'][i])
						desvio_mapa += excedente_lanche * get_preco('lanche', 'interno')
					if m.get('jantar_interno_siisp') and i < len(m.get('jantar_interno_siisp', [])):
						excedente_jantar = max(0, m['jantar_interno_siisp'][i])
						desvio_mapa += excedente_jantar * get_preco('jantar', 'interno')
			print(f"[DEBUG] lote_id={lote_id}, custo_mapa={custo_mapa}, desvio_mapa={desvio_mapa}")

		totais_custos_por_lote[lote_id] = totais_custos_por_lote.get(lote_id, 0.0) + custo_mapa
		totais_desvios_por_lote[lote_id] = totais_desvios_por_lote.get(lote_id, 0.0) + desvio_total_produtos

	# Atualizar os lotes com as métricas calculadas
	for lote in lotes:
		lote_id = lote.get('id')
		meses_count = len(meses_por_lote.get(lote_id, []))
		lote['meses_cadastrados'] = meses_count

		custo_total = totais_custos_por_lote.get(lote_id, 0.0)
		desvio_total = totais_desvios_por_lote.get(lote_id, 0.0)

		if meses_count > 0:
			lote['refeicoes_mes'] = totais_refeicoes_por_lote.get(lote_id, 0) / meses_count
			lote['custo_mes'] = custo_total / meses_count
			lote['desvio_mes'] = desvio_total / meses_count
		else:
			lote['refeicoes_mes'] = 0
			lote['custo_mes'] = 0.0
			lote['desvio_mes'] = 0.0

		valor_contratual = lote.get('valor_contratual', 0)
		try:
			valor_contratual = float(valor_contratual)
		except (ValueError, TypeError):
			valor_contratual = 0.0

		if valor_contratual > 0:
			lote['percentual_executado'] = round((custo_total / valor_contratual) * 100, 1)
		else:
			lote['percentual_executado'] = 0.0

		if lote['custo_mes'] > 0:
			lote['conformidade'] = round(max(0, ((lote['custo_mes'] - lote['desvio_mes']) / lote['custo_mes']) * 100), 1)
		else:
			lote['conformidade'] = 0.0
