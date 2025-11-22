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
		base_dir = os.path.dirname(os.path.dirname(__file__))
		lotes_path = os.path.join(base_dir, 'dados', 'lotes.json')
		
		if not os.path.isfile(lotes_path):
			return None
		
		with open(lotes_path, 'r', encoding='utf-8') as f:
			lotes = json.load(f)
		
		if not isinstance(lotes, list):
			return None
		
		for lote in lotes:
			if not isinstance(lote, dict):
				continue
			
			try:
				if int(lote.get('id')) == int(lote_id):
					data_inicio_str = lote.get('data_inicio')
					if data_inicio_str:
						return datetime.strptime(data_inicio_str, '%Y-%m-%d')
			except Exception:
				continue
		
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
		base_dir = os.path.dirname(os.path.dirname(__file__))
		lotes_path = os.path.join(base_dir, 'dados', 'lotes.json')
		
		if not os.path.isfile(lotes_path):
			return None
		
		with open(lotes_path, 'r', encoding='utf-8') as f:
			lotes = json.load(f)
		
		if not isinstance(lotes, list):
			return None
		
		for lote in lotes:
			if not isinstance(lote, dict):
				continue
			
			try:
				if int(lote.get('id')) == int(lote_id):
					data_fim_str = lote.get('data_fim')
					if data_fim_str:
						return datetime.strptime(data_fim_str, '%Y-%m-%d')
			except Exception:
				continue
		
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
def _get_mapas_filepath(mes, ano):
	base_dir = os.path.dirname(os.path.dirname(__file__))
	filename = f'mapas_{ano}_{mes:02d}.json'
	return os.path.join(base_dir, 'dados', filename)


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
	filepath = _get_mapas_filepath(mes, ano)
	if not os.path.isfile(filepath):
		return None
	try:
		with open(filepath, 'r', encoding='utf-8') as f:
			data = json.load(f)
			if isinstance(data, dict) and 'mapas' in data:
				return data['mapas']
			elif isinstance(data, list):
				return data
			return None
	except Exception as e:
		print(f"❌ Erro ao ler {filepath}: {e}")
		return None


def _save_mapas_partitioned(mapas_list, mes, ano):
	filepath = _get_mapas_filepath(mes, ano)
	try:
		os.makedirs(os.path.dirname(filepath), exist_ok=True)
		tmp_path = filepath + '.tmp'
		with open(tmp_path, 'w', encoding='utf-8') as f:
			json.dump(mapas_list, f, ensure_ascii=False, indent=2)
		os.replace(tmp_path, filepath)
		print(f"✅ Mapas salvos em: {filepath} ({len(mapas_list)} registros)")
		return True
	except Exception as e:
		print(f"❌ Erro ao salvar {filepath}: {e}")
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
	base_dir = os.path.dirname(os.path.dirname(__file__))
	dados_dir = os.path.join(base_dir, 'dados')
	
	pattern = os.path.join(dados_dir, 'mapas_????_??.json')
	
	arquivos = glob.glob(pattern)
	mapas_agregados = []
	
	for filepath in sorted(arquivos):
		try:
			with open(filepath, 'r', encoding='utf-8') as f:
				data = json.load(f)
				if isinstance(data, dict) and 'mapas' in data:
					mapas_agregados.extend(data['mapas'])
				elif isinstance(data, list):
					mapas_agregados.extend(data)
		except Exception as e:
			print(f"❌ Erro ao carregar {filepath}: {e}")
			continue
	
	return mapas_agregados
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
		entries = []
		if isinstance(payload, list):
			entries = payload
		else:
			entries = [payload or {}]
		
		periodos_afetados = set()
		for entry in entries:
			mes, ano = _detect_mes_ano_from_entry(entry)
			if mes and ano:
				periodos_afetados.add((mes, ano))
		
		if not periodos_afetados:
			return {'success': False, 'error': 'Não foi possível detectar mês/ano dos dados'}
		
		mapas_list = []
		for (mes, ano) in periodos_afetados:
			mapas_periodo = _load_mapas_partitioned(mes, ano)
			if mapas_periodo:
				mapas_list.extend(mapas_periodo)
		
		legacy_data = _load_mapas_data()
		if legacy_data:
			if isinstance(legacy_data, dict) and isinstance(legacy_data.get('mapas'), list):
				mapas_list.extend(legacy_data.get('mapas'))
			elif isinstance(legacy_data, list):
				mapas_list.extend(legacy_data)

		existing_ids = {int(m.get('id')) for m in mapas_list if isinstance(m, dict) and isinstance(m.get('id'), int)}
		next_id = (max(existing_ids) + 1) if existing_ids else 0

		saved_ids = []
		saved_records = []
		for entry in entries:
			if not isinstance(entry, dict):
				entry = {'data': entry}
			provided = entry.get('id')

			def _extract_key(obj):
				lote_keys = ('lote_id', 'loteId', 'lote', 'loteId')
				unidade_keys = ('unidade', 'unidade_id', 'unidadeId', 'unidade_nome', 'unidadeNome')
				mes_keys = ('mes', 'month', 'mes_num', 'mesNumero', 'month_num')
				ano_keys = ('ano', 'year')
				try:
					lote_val = None
					for k in lote_keys:
						if k in obj:
							lote_val = obj.get(k)
							break
					if lote_val is None:
						return None
					unidade_val = None
					for k in unidade_keys:
						if k in obj:
							unidade_val = obj.get(k)
							break
					if unidade_val is None:
						return None
					mes_val = None
					for k in mes_keys:
						if k in obj:
							mes_val = obj.get(k)
							break
					if mes_val is None:
						return None
					ano_val = None
					for k in ano_keys:
						if k in obj:
							ano_val = obj.get(k)
							break
					if ano_val is None:
						return None
					try:
						lote_n = int(lote_val)
					except Exception:
						try:
							lote_n = int(str(lote_val).strip())
						except Exception:
							return None
					try:
						mes_n = int(mes_val)
					except Exception:
						try:
							mes_n = int(str(mes_val).strip())
						except Exception:
							return None
					try:
						ano_n = int(ano_val)
					except Exception:
						try:
							ano_n = int(str(ano_val).strip())
						except Exception:
							return None
					unidade_s = str(unidade_val).strip().lower()
					return (lote_n, unidade_s, mes_n, ano_n)
				except Exception:
					return None

			entry_key = _extract_key(entry)
			matched_index = None
			matched_record = None
			if entry_key is not None:
				for idx, existing_map in enumerate(mapas_list):
					try:
						existing_key = _extract_key(existing_map) if isinstance(existing_map, dict) else None
						if existing_key is not None and existing_key == entry_key:
							matched_index = idx
							matched_record = existing_map
							break
					except Exception:
						continue

			if matched_index is not None:
				assigned = int(matched_record.get('id')) if isinstance(matched_record.get('id'), int) else matched_record.get('id')
				rec = dict(entry)
				possible_text_keys = ('texto', 'conteudo', 'dados', 'texto_raw', 'texto_mapas', 'mapa_texto')
				text_val = None
				used_text_key = None
				for k in possible_text_keys:
					if k in rec and rec.get(k) is not None:
						text_val = rec.get(k)
						used_text_key = k
						break
				if text_val is not None:
					parsed = parse_texto_tabular(text_val)
					if parsed.get('ok'):
						cols = parsed.get('colunas') or {}
						col_count = int(parsed.get('colunas_count') or 0)
						if col_count < 9:
							return {'success': False, 'error': f'Texto tabular contém colunas insuficientes: {col_count} (<9)'}
						for ck, cv in cols.items():
							rec[ck] = cv
						rec['linhas'] = parsed.get('linhas')
						rec['colunas_count'] = parsed.get('colunas_count')
						col_count = int(parsed.get('colunas_count') or 0)
						if col_count == 1:
							if 'coluna_0' in rec:
								rec['dados_siisp'] = rec.pop('coluna_0')
							else:
								rec['dados_siisp'] = []
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
								if oldk in rec:
									rec[newk] = rec.pop(oldk)
							if 'coluna_0' in rec:
								try:
									datas = _normalizar_datas_coluna(rec.get('coluna_0'), rec)
									rec.pop('coluna_0', None)
									rec['datas'] = datas
								except Exception:
									pass
					else:
						rec['colunas_parse_error'] = parsed.get('error')
					if used_text_key:
						try:
							rec.pop(used_text_key, None)
						except Exception:
							pass
				rec['id'] = assigned
				if 'dados_siisp' in rec:
					val = rec.get('dados_siisp')
					if isinstance(val, str):
						parsed_ds = parse_texto_tabular(val)
						if parsed_ds.get('ok') and int(parsed_ds.get('colunas_count') or 0) == 1:
							rec['dados_siisp'] = parsed_ds.get('colunas', {}).get('coluna_0', [])
						else:
							rec['dados_siisp'] = []
					elif not isinstance(val, list):
						rec['dados_siisp'] = []
				if 'dados_siisp' not in rec or rec.get('dados_siisp') is None:
					rec['dados_siisp'] = []
				
				if not rec.get('dados_siisp') or len(rec.get('dados_siisp', [])) == 0:
					try:
						mes_num = int(rec.get('mes') or datetime.now().month)
						ano_num = int(rec.get('ano') or datetime.now().year)
						dias_no_mes = calendar.monthrange(ano_num, mes_num)[1]
						rec['dados_siisp'] = [0] * dias_no_mes
					except Exception:
						rec['dados_siisp'] = [0] * 31
				
				# Filtrar por data de início do contrato (se ainda não foi filtrado)
				if 'linhas' not in rec or rec.get('linhas') >= len(rec.get('datas', [])):
					lote_id_rec = rec.get('lote_id')
					if lote_id_rec:
						try:
							data_inicio = _get_lote_data_inicio(int(lote_id_rec))
							data_fim = _get_lote_data_fim(int(lote_id_rec))
							if data_inicio or data_fim:
								mes_rec = int(rec.get('mes'))
								ano_rec = int(rec.get('ano'))
								meal_fields = [
									'cafe_interno', 'cafe_funcionario',
									'almoco_interno', 'almoco_funcionario',
									'lanche_interno', 'lanche_funcionario',
									'jantar_interno', 'jantar_funcionario'
								]
								indices_validos = []
								datas = rec.get('datas', [])
								for idx, data_str in enumerate(datas):
									try:
										dia = int(data_str.split('/')[0])
										data_dia = datetime(ano_rec, mes_rec, dia)
										valido = True
										if data_inicio and data_dia < data_inicio:
											valido = False
										if data_fim and data_dia > data_fim:
											valido = False
										if valido:
											indices_validos.append(idx)
									except:
										indices_validos.append(idx)
								
								if len(indices_validos) < len(datas):
									# Filtrar arrays
									for field in meal_fields:
										if field in rec and isinstance(rec[field], list):
											arr = rec[field]
											rec[field] = [arr[i] for i in indices_validos if i < len(arr)]
									if 'dados_siisp' in rec and isinstance(rec['dados_siisp'], list):
										arr_siisp = rec['dados_siisp']
										rec['dados_siisp'] = [arr_siisp[i] for i in indices_validos if i < len(arr_siisp)]
									rec['datas'] = [datas[i] for i in indices_validos]
									rec['linhas'] = len(indices_validos)
						except:
							pass
				if 'criado_em' not in rec and matched_record.get('criado_em'):
					rec['criado_em'] = matched_record.get('criado_em')
				rec['atualizado_em'] = datetime.now().isoformat()
				
				_calcular_campos_comparativos_siisp(rec)
				
				valid_ok, valid_msg = _validate_map_day_lengths(rec)
				if not valid_ok:
					return {'success': False, 'error': f'Validação de tamanho falhou: {valid_msg}'}
				mapas_list[matched_index] = rec
				saved_ids.append(assigned)
				saved_records.append(rec)
				if 'operacoes' not in locals():
					operacoes = []
				operacoes.append('overwritten')
				existing_ids.add(int(assigned))
				continue

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
					if col_count < 9:
						return {'success': False, 'error': f'Texto tabular contém colunas insuficientes: {col_count} (<9)'}
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
				else:
					entry['colunas_parse_error'] = parsed.get('error')
				if used_text_key:
					try:
						entry.pop(used_text_key, None)
					except Exception:
						pass
			if provided is None:
				assigned = next_id
				next_id += 1
			else:
				try:
					pid = int(provided)
				except Exception:
					return {'success': False, 'error': 'ID inválido fornecido'}
				if pid in existing_ids or pid in saved_ids:
					return {'success': False, 'error': f'ID já existe: {pid}'}
				assigned = pid
				if pid >= next_id:
					next_id = pid + 1

			rec = dict(entry)
			rec['id'] = assigned
			if 'criado_em' not in rec:
				rec['criado_em'] = datetime.now().isoformat()
			if 'dados_siisp' in rec:
				val = rec.get('dados_siisp')
				if isinstance(val, str):
					parsed_ds = parse_texto_tabular(val)
					if parsed_ds.get('ok') and int(parsed_ds.get('colunas_count') or 0) == 1:
						rec['dados_siisp'] = parsed_ds.get('colunas', {}).get('coluna_0', [])
					else:
						rec['dados_siisp'] = []
				elif not isinstance(val, list):
					rec['dados_siisp'] = []
			if 'dados_siisp' not in rec or rec.get('dados_siisp') is None:
				rec['dados_siisp'] = []
			
			if not rec.get('dados_siisp') or len(rec.get('dados_siisp', [])) == 0:
				try:
					mes_num = int(rec.get('mes') or datetime.now().month)
					ano_num = int(rec.get('ano') or datetime.now().year)
					dias_no_mes = calendar.monthrange(ano_num, mes_num)[1]
					rec['dados_siisp'] = [0] * dias_no_mes
				except Exception:
					rec['dados_siisp'] = [0] * 31
			
			
			# Filtrar por data de início do contrato (se ainda não foi filtrado)
			if 'linhas' not in rec or rec.get('linhas') >= len(rec.get('datas', [])):
				lote_id_rec = rec.get('lote_id')
				if lote_id_rec:
					try:
						data_inicio = _get_lote_data_inicio(int(lote_id_rec))
						data_fim = _get_lote_data_fim(int(lote_id_rec))
						if data_inicio or data_fim:
							mes_rec = int(rec.get('mes'))
							ano_rec = int(rec.get('ano'))
							meal_fields = [
								'cafe_interno', 'cafe_funcionario',
								'almoco_interno', 'almoco_funcionario',
								'lanche_interno', 'lanche_funcionario',
								'jantar_interno', 'jantar_funcionario'
							]
							indices_validos = []
							datas = rec.get('datas', [])
							for idx, data_str in enumerate(datas):
								try:
									dia = int(data_str.split('/')[0])
									data_dia = datetime(ano_rec, mes_rec, dia)
									valido = True
									if data_inicio and data_dia < data_inicio:
										valido = False
									if data_fim and data_dia > data_fim:
										valido = False
									if valido:
										indices_validos.append(idx)
								except:
									indices_validos.append(idx)
							
							if len(indices_validos) < len(datas):
								# Filtrar arrays
								for field in meal_fields:
									if field in rec and isinstance(rec[field], list):
										arr = rec[field]
										rec[field] = [arr[i] for i in indices_validos if i < len(arr)]
								if 'dados_siisp' in rec and isinstance(rec['dados_siisp'], list):
									arr_siisp = rec['dados_siisp']
									rec['dados_siisp'] = [arr_siisp[i] for i in indices_validos if i < len(arr_siisp)]
								rec['datas'] = [datas[i] for i in indices_validos]
								rec['linhas'] = len(indices_validos)
					except:
						pass
			
			_calcular_campos_comparativos_siisp(rec)
			
			valid_ok, valid_msg = _validate_map_day_lengths(rec)
			if not valid_ok:
				return {'success': False, 'error': f'Validação de tamanho falhou: {valid_msg}'}
			mapas_list.append(rec)
			saved_ids.append(assigned)
			saved_records.append(rec)
			if 'operacoes' not in locals():
				operacoes = []
			operacoes.append('created')

		mapas_por_periodo = {}
		
		for mapa in mapas_list:
			mes, ano = _detect_mes_ano_from_entry(mapa)
			if mes and ano:
				key = (mes, ano)
				if key not in mapas_por_periodo:
					mapas_por_periodo[key] = []
				mapas_por_periodo[key].append(mapa)
			else:
				print(f"⚠️ Mapa sem mes/ano detectável: {mapa.get('id', 'sem id')}")
		
		all_saved = True
		for (mes, ano), mapas_periodo in mapas_por_periodo.items():
			ok = _save_mapas_partitioned(mapas_periodo, mes, ano)
			if not ok:
				all_saved = False
				print(f"❌ Falha ao salvar mapas de {mes:02d}/{ano}")
		
		if not all_saved:
			return {'success': False, 'error': 'Erro ao salvar alguns arquivos de mapas'}
		
		if len(saved_records) == 1:
			ret = {'success': True, 'id': saved_records[0]['id'], 'registro': saved_records[0]}
			if 'operacoes' in locals() and isinstance(operacoes, list) and len(operacoes) == 1:
				ret['operacao'] = operacoes[0]
			return ret
		ret = {'success': True, 'ids': saved_ids, 'registros': saved_records}
		if 'operacoes' in locals() and isinstance(operacoes, list):
			ret['operacoes'] = operacoes
		return ret
	except Exception:
		return {'success': False, 'error': 'Erro ao salvar mapas'}


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
	
	if mes < 1 or mes > 12:
		return {'success': False, 'error': 'Mês deve estar entre 1 e 12'}
	
	mapas_existentes = _load_mapas_partitioned(mes, ano)
	if mapas_existentes is None:
		return {
			'success': False,
			'error': f'Nenhum mapa encontrado para {mes:02d}/{ano}. Não há dados para excluir.'
		}
	
	mapa_encontrado = None
	indice_mapa = None
	for i, m in enumerate(mapas_existentes):
		if not isinstance(m, dict):
			continue
		m_unidade = str(m.get('unidade', '')).strip()
		m_mes = m.get('mes')
		m_ano = m.get('ano')
		
		try:
			if (m_unidade.lower() == unidade.lower() and 
				int(m_mes) == int(mes) and
				int(m_ano) == int(ano)):
				if lote_id is not None:
					m_lote_id = m.get('lote_id')
					if int(m_lote_id) != int(lote_id):
						continue
				mapa_encontrado = m
				indice_mapa = i
				break
		except Exception:
			continue
	
	if mapa_encontrado is None:
		msg_extra = f' e Lote {lote_id}' if lote_id is not None else ''
		return {
			'success': False,
			'error': f'Mapa não encontrado para Unidade "{unidade}", período {mes:02d}/{ano}{msg_extra}.'
		}
	
	mapa_id = mapa_encontrado.get('id')
	
	mapas_existentes.pop(indice_mapa)
	
	if len(mapas_existentes) == 0:
		filepath = _get_mapas_filepath(mes, ano)
		try:
			if os.path.isfile(filepath):
				os.remove(filepath)
				print(f"🗑️ Arquivo vazio deletado: {filepath}")
		except Exception as e:
			print(f"⚠️ Aviso: Não foi possível deletar arquivo vazio: {e}")
	else:
		if not _save_mapas_partitioned(mapas_existentes, mes, ano):
			return {'success': False, 'error': 'Erro ao salvar dados após exclusão'}
	
	return {
		'success': True,
		'mensagem': f'Mapa {mapa_id} da unidade "{unidade}" ({mes:02d}/{ano}) excluído com sucesso.',
		'id': mapa_id
	}


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
	meses_por_lote = defaultdict(set)
	totais_refeicoes_por_lote = {}
	totais_custos_por_lote = {}
	totais_desvios_por_lote = {}
	
	for m in (mapas or []):
		try:
			lote_id = int(m.get('lote_id'))
		except Exception:
			continue
		
		mes = m.get('mes') or m.get('month') or m.get('mes_num') or m.get('month_num')
		ano = m.get('ano') or m.get('year')
		
		if (mes is None or ano is None) and isinstance(m.get('datas'), list) and len(m.get('datas')) > 0:
			try:
				parts = str(m.get('datas')[0]).split('/')
				if len(parts) >= 3:
					mes = int(parts[1])
					ano = int(parts[2])
			except Exception:
				pass
		
		try:
			mes_i = int(mes)
			ano_i = int(ano)
		except Exception:
			continue
		
		meses_por_lote[lote_id].add((mes_i, ano_i))
		
		try:
			total = int(m.get('refeicoes_mes') or 0)
		except Exception:
			try:
				total = int(float(m.get('refeicoes_mes') or 0))
			except Exception:
				total = 0
		
		totais_refeicoes_por_lote[lote_id] = totais_refeicoes_por_lote.get(lote_id, 0) + total
		
		custo_mapa = 0.0
		desvio_mapa = 0.0
		lote_do_mapa = None
		for l_temp in lotes:
			try:
				if int(l_temp.get('id')) == lote_id:
					lote_do_mapa = l_temp
					break
			except Exception:
				continue
		
		if lote_do_mapa and isinstance(lote_do_mapa.get('precos'), dict):
			precos = lote_do_mapa.get('precos', {})
			
			# Função auxiliar para obter preço (suporta ambos formatos)
			def get_preco(refeicao, tipo):
				# Tentar formato aninhado primeiro: cafe.interno
				if isinstance(precos.get(refeicao), dict):
					valor = precos[refeicao].get(tipo, 0)
				else:
					# Formato plano: cafe_interno
					chave = f"{refeicao}_{tipo}"
					valor = precos.get(chave, 0)
				
				# Converter para float se for string
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
						pass
			
			# Calcular desvios baseado em discrepâncias SIISP
			for i in range(len(m.get('data', []))):
				siisp = m.get('n_siisp', [])[i] if m.get('n_siisp') and i < len(m.get('n_siisp', [])) else 0
				if siisp > 0:
					# Usar colunas _siisp se disponíveis
					if m.get('cafe_interno_siisp') and i < len(m.get('cafe_interno_siisp', [])):
						excedente_cafe = max(0, m['cafe_interno_siisp'][i])
						desvio_mapa += excedente_cafe * get_preco('cafe', 'interno')
					if m.get('almoco_interno_siisp') and i < len(m.get('almoco_interno_siisp', [])):
						excedente_almoco = max(0, m['almoco_interno_siisp'][i])
						desvio_mapa += excedente_almoco * get_preco('almoco', 'interno')
					if m.get('lanche_interno_siisp') and i < len(m.get('lanche_interno_siisp', [])):
						excedente_lanche = max(0, m['lanche_interno_siisp'][i])
						desvio_mapa += excedente_lanche * get_preco('lanche', 'interno')
					if m.get('jantar_interno_siisp') and i < len(m.get('jantar_interno_siisp', [])):
						excedente_jantar = max(0, m['jantar_interno_siisp'][i])
						desvio_mapa += excedente_jantar * get_preco('jantar', 'interno')
		
		totais_custos_por_lote[lote_id] = totais_custos_por_lote.get(lote_id, 0.0) + custo_mapa
		totais_desvios_por_lote[lote_id] = totais_desvios_por_lote.get(lote_id, 0.0) + desvio_mapa
	
	# Atualizar os lotes com as métricas calculadas
	for lote in lotes:
		lote_id = lote.get('id')
		meses_count = len(meses_por_lote.get(lote_id, []))
		lote['meses_cadastrados'] = meses_count
		
		# Totais acumulados (sem dividir)
		custo_total = totais_custos_por_lote.get(lote_id, 0.0)
		desvio_total = totais_desvios_por_lote.get(lote_id, 0.0)
		
		# Dividir por quantidade de meses para obter MÉDIA mensal
		if meses_count > 0:
			lote['refeicoes_mes'] = totais_refeicoes_por_lote.get(lote_id, 0) / meses_count
			lote['custo_mes'] = custo_total / meses_count
			lote['desvio_mes'] = desvio_total / meses_count
		else:
			lote['refeicoes_mes'] = 0
			lote['custo_mes'] = 0.0
			lote['desvio_mes'] = 0.0
		
		# Calcular percentual executado: (custo total / valor contratual) * 100
		valor_contratual = lote.get('valor_contratual', 0)
		try:
			valor_contratual = float(valor_contratual)
		except (ValueError, TypeError):
			valor_contratual = 0.0
		
		if valor_contratual > 0:
			lote['percentual_executado'] = round((custo_total / valor_contratual) * 100, 1)
		else:
			lote['percentual_executado'] = 0.0
		
		# Manter conformidade para compatibilidade com dashboard.html e lote-detalhes.html
		if lote['custo_mes'] > 0:
			lote['conformidade'] = round(max(0, ((lote['custo_mes'] - lote['desvio_mes']) / lote['custo_mes']) * 100), 1)
		else:
			lote['conformidade'] = 0.0
