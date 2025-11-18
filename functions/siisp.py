import json
import calendar
from datetime import datetime
from .mapas import (
	_calcular_campos_comparativos_siisp,
	parse_texto_tabular,
	_load_mapas_partitioned,
	_save_mapas_partitioned
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
	
	mapas_existentes = _load_mapas_partitioned(mes, ano)
	if mapas_existentes is None:
		return {
			'success': False,
			'error': f'Nenhum mapa encontrado para {mes:02d}/{ano}. Adicione dados de refeições primeiro.'
		}
	
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
