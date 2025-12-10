# Função de normalização ultra tolerante para nomes de unidade
def ultra_normalizar_nome(nome):
	if not isinstance(nome, str):
		nome = str(nome)
	nome = nome.lower().strip()
	nome = nome.replace('ups', '').replace('upsl', '').replace('unidade', '').replace('posto', '')
	nome = nome.replace('-', ' ').replace('_', ' ').replace('.', ' ')
	nome = ''.join(c for c in nome if c.isalnum() or c.isspace())
	nome = ' '.join(nome.split())
	return nome
import json
import calendar
from datetime import datetime
from .mapas import (
	_calcular_campos_comparativos_siisp,
	parse_texto_tabular,
	_load_mapas_partitioned,
	_save_mapas_partitioned,
	_get_lote_data_inicio,
	_get_lote_data_fim
)


# ----- SIISP Operations -----
def adicionar_siisp_em_mapa(payload):
	if not isinstance(payload, dict):
		return {'success': False, 'error': 'Payload inválido'}
	
	unidade = payload.get('unidade', '').strip()
	mes = payload.get('mes')
	ano = payload.get('ano')
	lote_id = payload.get('lote_id')
	dados_siisp_raw = payload.get('dados_siisp')
	
	if not unidade or not mes or not ano or lote_id is None:
		return {'success': False, 'error': 'Campos obrigatórios ausentes: unidade, mes, ano, lote_id'}
	
	try:
		mes = int(mes)
		ano = int(ano)
		lote_id = int(lote_id)
	except Exception:
		return {'success': False, 'error': 'Valores inválidos para mes, ano ou lote_id'}
	
	if mes < 1 or mes > 12:
		return {'success': False, 'error': 'Mês deve estar entre 1 e 12'}
	
	try:
		dias_esperados = calendar.monthrange(ano, mes)[1]
	except Exception:
		return {'success': False, 'error': 'Combinação inválida de mês/ano'}
	
	dados_siisp_list = []
	if isinstance(dados_siisp_raw, str):
		parsed = parse_texto_tabular(dados_siisp_raw)
		if not parsed.get('ok'):
			return {'success': False, 'error': f'Erro ao processar dados SIISP: {parsed.get("error")}'}
		
		colunas = parsed.get('colunas', {})
		primeira_coluna_key = 'coluna_0'
		if primeira_coluna_key in colunas:
			dados_siisp_list = colunas[primeira_coluna_key]
		else:
			return {'success': False, 'error': 'Dados SIISP não encontrados na primeira coluna'}
	elif isinstance(dados_siisp_raw, list):
		for item in dados_siisp_raw:
			try:
				if isinstance(item, (int, float)):
					dados_siisp_list.append(int(item))
				elif isinstance(item, str):
					num = int(item.strip())
					dados_siisp_list.append(num)
				else:
					dados_siisp_list.append(0)
			except Exception:
				dados_siisp_list.append(0)
	elif dados_siisp_raw is None or dados_siisp_raw == '':
		return {'success': False, 'error': 'Dados SIISP não fornecidos'}
	else:
		return {'success': False, 'error': f'Formato de dados SIISP inválido: tipo {type(dados_siisp_raw).__name__}. Esperado: string ou lista'}
	
	if len(dados_siisp_list) != dias_esperados:
		return {
			'success': False, 
			'error': f'Quantidade de dados SIISP ({len(dados_siisp_list)}) não corresponde aos dias do mês ({dias_esperados} dias em {mes:02d}/{ano})'
		}
	
	# Validar data de início e fim do contrato
	data_inicio = _get_lote_data_inicio(lote_id)
	data_fim = _get_lote_data_fim(lote_id)
	
	if data_inicio or data_fim:
		# Verificar se o mês/ano está fora do período do contrato
		data_primeiro_dia_mes = datetime(ano, mes, 1)
		try:
			data_ultimo_dia_mes = datetime(ano, mes, dias_esperados)
		except:
			data_ultimo_dia_mes = datetime(ano, mes, 28)
		
		# Se o último dia do mês é anterior ao início do contrato, rejeitar
		if data_inicio and data_ultimo_dia_mes < data_inicio:
			return {
				'success': False,
				'error': f'Mês {mes:02d}/{ano} é anterior à data de início do contrato ({data_inicio.strftime("%d/%m/%Y")}). Dados SIISP não podem ser adicionados.'
			}
		
		# Se o primeiro dia do mês é posterior ao fim do contrato, rejeitar
		if data_fim and data_primeiro_dia_mes > data_fim:
			return {
				'success': False,
				'error': f'Mês {mes:02d}/{ano} é posterior à data de fim do contrato ({data_fim.strftime("%d/%m/%Y")}). Dados SIISP não podem ser adicionados.'
			}
		
		# Filtrar dados: considerar apenas dias dentro do período do contrato
		indices_validos = []
		for dia in range(1, dias_esperados + 1):
			data_dia = datetime(ano, mes, dia)
			valido = True
			if data_inicio and data_dia < data_inicio:
				valido = False
			if data_fim and data_dia > data_fim:
				valido = False
			if valido:
				indices_validos.append(dia - 1)  # índice 0-based
		
		if len(indices_validos) < len(dados_siisp_list):
			dados_siisp_filtrados = [dados_siisp_list[i] for i in indices_validos]
			
			msg_filtro = f"📅 Filtrando SIISP: Contrato"
			if data_inicio:
				msg_filtro += f" inicia em {data_inicio.strftime('%d/%m/%Y')}"
			if data_fim:
				msg_filtro += f" termina em {data_fim.strftime('%d/%m/%Y')}"
			print(msg_filtro)
			print(f"   Original: {len(dados_siisp_list)} elementos")
			print(f"   Filtrado: {len(dados_siisp_filtrados)} elementos")
			
			dados_siisp_list = dados_siisp_filtrados
	
	mapas_raw = _load_mapas_partitioned(mes, ano)
	from .mapas import serialize_mapa
	mapas_existentes = [serialize_mapa(m) for m in mapas_raw]
	if not mapas_existentes:
		print(f'❌ DEBUG: Nenhum mapa encontrado para mes={mes}, ano={ano} pelo _load_mapas_partitioned.')
		return {
			'success': False,
			'error': f'Nenhum mapa encontrado para {mes:02d}/{ano}. Adicione dados de refeições primeiro.'
		}

	unidade_normalizada = ultra_normalizar_nome(unidade)
	print('🔍 DEBUG SIISP: Buscando mapa para:')
	print(f'    Unidade: "{unidade}" (normalizada: "{unidade_normalizada}")')
	print(f'    lote_id: {lote_id} | mes: {mes} | ano: {ano}')
	print(f'    Total de mapas carregados para o período: {len(mapas_existentes)}')
	for i, m in enumerate(mapas_existentes):
		if not isinstance(m, dict):
			continue
		m_unidade = str(m.get('unidade', '')).strip()
		m_lote_id = m.get('lote_id')
		m_mes = m.get('mes')
		m_ano = m.get('ano')
		m_unidade_normalizada = ultra_normalizar_nome(m_unidade)
		print(f'  - [{i}] Unidade: "{m_unidade}" (normalizada: "{m_unidade_normalizada}") | lote_id: {m_lote_id} | mes: {m_mes} | ano: {m_ano}')
		try:
			match_unidade = (m_unidade_normalizada == unidade_normalizada)
			match_lote = (int(m_lote_id) == int(lote_id))
			match_mes = (int(m_mes) == int(mes))
			match_ano = (int(m_ano) == int(ano))
			print(f'      Comparação: unidade={match_unidade}, lote={match_lote}, mes={match_mes}, ano={match_ano}')
			if match_unidade and match_lote and match_mes and match_ano:
				print(f'      >>> MAPA ENCONTRADO!')
				mapa_encontrado = m
				indice_mapa = i
				break
		except Exception as e:
			print(f'      Erro na comparação: {e}')
			continue
	
	mapa_encontrado = None
	indice_mapa = None
	for i, m in enumerate(mapas_existentes):
		if not isinstance(m, dict):
			continue
		m_unidade = str(m.get('unidade', '')).strip()
		m_lote_id = m.get('lote_id')
		m_mes = m.get('mes')
		m_ano = m.get('ano')
		
		try:
			if (m_unidade.lower() == unidade.lower() and 
				int(m_lote_id) == int(lote_id) and
				int(m_mes) == int(mes) and
				int(m_ano) == int(ano)):
				mapa_encontrado = m
				indice_mapa = i
				break
		except Exception:
			continue
	
	if mapa_encontrado is None:
		return {
			'success': False,
			'error': f'Mapa não encontrado para Unidade "{unidade}", Lote {lote_id}, período {mes:02d}/{ano}. Adicione dados de refeições primeiro.'
		}
	
	# Verificar se o mapa já está filtrado (campo 'linhas' indica dados filtrados)
	linhas_mapa = mapa_encontrado.get('linhas')
	if linhas_mapa and linhas_mapa < dias_esperados:
		# Mapa está filtrado, ajustar SIISP para o mesmo tamanho
		if len(dados_siisp_list) != linhas_mapa:
			# Se SIISP tem mais elementos, usar apenas os necessários
			if len(dados_siisp_list) > linhas_mapa:
				# Pegar os últimos N elementos (dias válidos do final do mês)
				dados_siisp_list = dados_siisp_list[-linhas_mapa:]
				print(f"⚠️ Ajustando SIISP para {linhas_mapa} elementos (mapa filtrado)")
			else:
				return {
					'success': False,
					'error': f'Dados SIISP insuficientes: mapa possui {linhas_mapa} dias, mas SIISP tem apenas {len(dados_siisp_list)} elementos'
				}
	
	mapa_encontrado['dados_siisp'] = dados_siisp_list
	mapa_encontrado['atualizado_em'] = datetime.now().isoformat()
	
	_calcular_campos_comparativos_siisp(mapa_encontrado)
	
	mapas_existentes[indice_mapa] = mapa_encontrado
	
	if not _save_mapas_partitioned(mapas_existentes, mes, ano):
		return {'success': False, 'error': 'Erro ao salvar dados'}
	
	return {
		'success': True,
		'registro': mapa_encontrado,
		'mensagem': f'Dados SIISP adicionados com sucesso ao mapa {mapa_encontrado.get("id")}'
	}


def validar_dados_siisp(dados_siisp, mes, ano):
	if not dados_siisp:
		return {'valido': False, 'mensagem': 'Dados SIISP não fornecidos'}
	
	if mes < 1 or mes > 12:
		return {'valido': False, 'mensagem': 'Mês inválido'}
	
	try:
		dias_esperados = calendar.monthrange(ano, mes)[1]
	except Exception:
		return {'valido': False, 'mensagem': 'Ano inválido'}
	
	if isinstance(dados_siisp, str):
		parsed = parse_texto_tabular(dados_siisp)
		if not parsed.get('ok'):
			return {'valido': False, 'mensagem': f'Erro ao processar: {parsed.get("error")}'}
		
		colunas = parsed.get('colunas', {})
		if 'coluna_0' not in colunas:
			return {'valido': False, 'mensagem': 'Dados não encontrados'}
		
		dados_lista = colunas['coluna_0']
	elif isinstance(dados_siisp, list):
		dados_lista = dados_siisp
	else:
		return {'valido': False, 'mensagem': 'Formato inválido'}
	
	if len(dados_lista) != dias_esperados:
		return {
			'valido': False,
			'mensagem': f'Esperado {dias_esperados} dias, recebido {len(dados_lista)}'
		}
	
	for i, valor in enumerate(dados_lista):
		if valor is None:
			continue
		try:
			int(valor)
		except (ValueError, TypeError):
			return {
				'valido': False,
				'mensagem': f'Valor inválido na posição {i+1}: {valor}'
			}
	
	return {'valido': True, 'mensagem': 'Dados SIISP válidos'}


def processar_texto_siisp(texto):
	if not texto or not isinstance(texto, str):
		return {'ok': False, 'error': 'Texto inválido'}
	
	parsed = parse_texto_tabular(texto)
	if not parsed.get('ok'):
		return {'ok': False, 'error': parsed.get('error')}
	
	colunas = parsed.get('colunas', {})
	if 'coluna_0' not in colunas:
		return {'ok': False, 'error': 'Nenhuma coluna encontrada'}
	
	dados_siisp = colunas['coluna_0']
	
	dados_numericos = []
	for valor in dados_siisp:
		if valor is None:
			dados_numericos.append(0)
		else:
			try:
				dados_numericos.append(int(valor))
			except (ValueError, TypeError):
				dados_numericos.append(0)
	
	return {
		'ok': True,
		'dados_siisp': dados_numericos,
		'total_dias': len(dados_numericos)
	}


def calcular_discrepancias_siisp(mapa):
	if not isinstance(mapa, dict):
		return None
	
	dados_siisp = mapa.get('dados_siisp', [])
	if not dados_siisp or not isinstance(dados_siisp, list):
		return None
	
	meal_fields = [
		'cafe_interno', 'cafe_funcionario',
		'almoco_interno', 'almoco_funcionario',
		'lanche_interno', 'lanche_funcionario',
		'jantar_interno', 'jantar_funcionario'
	]
	
	discrepancias = {}
	total_discrepancias = 0
	
	for field in meal_fields:
		if field not in mapa:
			continue
		
		field_data = mapa.get(field, [])
		if not isinstance(field_data, list):
			continue
		
		siisp_field = f"{field}_siisp"
		if siisp_field in mapa and isinstance(mapa[siisp_field], list):
			siisp_diff = mapa[siisp_field]
			
			total_diff = sum(abs(d) for d in siisp_diff if d is not None)
			discrepancias[field] = {
				'total_diferenca': total_diff,
				'diferenca_positiva': sum(d for d in siisp_diff if d is not None and d > 0),
				'diferenca_negativa': sum(d for d in siisp_diff if d is not None and d < 0),
				'dias_com_diferenca': sum(1 for d in siisp_diff if d is not None and d != 0)
			}
			total_discrepancias += total_diff
	
	return {
		'por_campo': discrepancias,
		'total_geral': total_discrepancias,
		'tem_discrepancias': total_discrepancias > 0
	}


def obter_resumo_siisp(mes, ano, lote_id=None, unidade=None):
	mapas = _load_mapas_partitioned(mes, ano)
	if not mapas:
		return {
			'total_mapas': 0,
			'mapas_com_siisp': 0,
			'mapas_sem_siisp': 0,
			'mapas': []
		}
	
	mapas_filtrados = []
	for mapa in mapas:
		if not isinstance(mapa, dict):
			continue
		
		if lote_id is not None:
			try:
				if int(mapa.get('lote_id')) != int(lote_id):
					continue
			except Exception:
				continue
		
		if unidade is not None:
			m_unidade = str(mapa.get('unidade', '')).strip().lower()
			if m_unidade != str(unidade).strip().lower():
				continue
		
		mapas_filtrados.append(mapa)
	
	com_siisp = 0
	sem_siisp = 0
	
	resumo_mapas = []
	for mapa in mapas_filtrados:
		dados_siisp = mapa.get('dados_siisp', [])
		tem_siisp = isinstance(dados_siisp, list) and len(dados_siisp) > 0 and any(d != 0 for d in dados_siisp)
		
		if tem_siisp:
			com_siisp += 1
		else:
			sem_siisp += 1
		
		resumo_mapas.append({
			'id': mapa.get('id'),
			'unidade': mapa.get('unidade'),
			'lote_id': mapa.get('lote_id'),
			'tem_siisp': tem_siisp,
			'total_siisp': sum(dados_siisp) if tem_siisp else 0
		})
	
	return {
		'mes': mes,
		'ano': ano,
		'total_mapas': len(mapas_filtrados),
		'mapas_com_siisp': com_siisp,
		'mapas_sem_siisp': sem_siisp,
		'mapas': resumo_mapas
	}
