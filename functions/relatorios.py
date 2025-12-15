"""
Funções para geração de relatórios e dados para gráficos
"""
from datetime import datetime, timedelta
from collections import defaultdict
from functions.models import db, Mapa, Lote
from sqlalchemy import and_, or_
import json


def buscar_dados_graficos(lotes_ids, unidades, periodo='mes', data_inicio=None, data_fim=None, modo='acumulado'):
    """
    Busca dados de mapas para gerar gráficos
    
    Args:
        lotes_ids: Lista de IDs dos lotes
        unidades: Lista de nomes das unidades
        periodo: 'dia', 'semana', 'mes' ou 'ano'
        data_inicio: Data de início (opcional)
        data_fim: Data de fim (opcional)
        modo: 'acumulado', 'unidade' ou 'lote'
    
    Returns:
        dict com dados agregados para o gráfico
    """
    try:
        # Se não houver lotes ou unidades selecionadas, retornar vazio
        if not lotes_ids or len(lotes_ids) == 0:
            print("⚠️ Nenhum lote selecionado - retornando dados vazios")
            return {
                'success': True,
                'dados': {
                    'labels': [],
                    'labels_formatados': [],
                    'datasets': {
                        'cafe_interno': [],
                        'cafe_funcionario': [],
                        'almoco_interno': [],
                        'almoco_funcionario': [],
                        'lanche_interno': [],
                        'lanche_funcionario': [],
                        'jantar_interno': [],
                        'jantar_funcionario': [],
                        'dados_siisp': [],
                        'total_refeicoes': []
                    }
                },
                'total_registros': 0
            }
        
        if not unidades or len(unidades) == 0:
            print("⚠️ Nenhuma unidade selecionada - retornando dados vazios")
            return {
                'success': True,
                'dados': {
                    'labels': [],
                    'labels_formatados': [],
                    'datasets': {
                        'cafe_interno': [],
                        'cafe_funcionario': [],
                        'almoco_interno': [],
                        'almoco_funcionario': [],
                        'lanche_interno': [],
                        'lanche_funcionario': [],
                        'jantar_interno': [],
                        'jantar_funcionario': [],
                        'dados_siisp': [],
                        'total_refeicoes': []
                    }
                },
                'total_registros': 0
            }
        
        # Construir query base
        query = db.session.query(Mapa)
        
        # Filtrar por lotes (obrigatório)
        query = query.filter(Mapa.lote_id.in_(lotes_ids))
        
        # Filtrar por unidades (obrigatório)
        query = query.filter(Mapa.unidade.in_(unidades))
        
        # Filtrar por período se especificado
        if data_inicio:
            query = query.filter(Mapa.ano >= data_inicio.year)
        if data_fim:
            query = query.filter(Mapa.ano <= data_fim.year)
        
        mapas = query.all()
        
        print(f"📊 Buscar dados gráficos: {len(mapas)} mapas encontrados")
        print(f"   Lotes: {lotes_ids}, Unidades: {unidades}, Período: {periodo}, Modo: {modo}")
        
        # Agregar dados por período e modo
        if modo == 'acumulado':
            dados_agregados = agregar_por_periodo(mapas, periodo)
        elif modo == 'unidade':
            dados_agregados = agregar_por_grupo(mapas, periodo, 'unidade')
        elif modo == 'lote':
            dados_agregados = agregar_por_grupo(mapas, periodo, 'lote', lotes_ids)
        else:
            dados_agregados = agregar_por_periodo(mapas, periodo)
        
        return {
            'success': True,
            'dados': dados_agregados,
            'total_registros': len(mapas)
        }
    
    except Exception as e:
        print(f"❌ Erro ao buscar dados gráficos: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def agregar_por_periodo(mapas, periodo='mes'):
    """
    Agrega dados de mapas por período
    
    Returns:
        dict com labels e valores para o gráfico
    """
    dados_por_periodo = defaultdict(lambda: {
        'cafe_interno': 0,
        'cafe_funcionario': 0,
        'almoco_interno': 0,
        'almoco_funcionario': 0,
        'lanche_interno': 0,
        'lanche_funcionario': 0,
        'jantar_interno': 0,
        'jantar_funcionario': 0,
        'dados_siisp': 0,
        'total_refeicoes': 0
    })
    
    campos_refeicoes = [
        'cafe_interno', 'cafe_funcionario', 
        'almoco_interno', 'almoco_funcionario',
        'lanche_interno', 'lanche_funcionario', 
        'jantar_interno', 'jantar_funcionario'
    ]
    
    for mapa in mapas:
        # Criar chave baseada no período
        if periodo == 'dia':
            # Precisamos iterar por cada dia do mapa
            datas = mapa.datas or []
            for i, data_str in enumerate(datas):
                chave = data_str  # YYYY-MM-DD
                for campo in campos_refeicoes:
                    valores = getattr(mapa, campo, []) or []
                    if i < len(valores):
                        dados_por_periodo[chave][campo] += valores[i]
                        dados_por_periodo[chave]['total_refeicoes'] += valores[i]
                
                # SIISP
                valores_siisp = mapa.dados_siisp or []
                if i < len(valores_siisp):
                    dados_por_periodo[chave]['dados_siisp'] += valores_siisp[i]
        
        elif periodo == 'mes':
            # Agrupar por mês (YYYY-MM)
            chave = f"{mapa.ano}-{mapa.mes:02d}"
            
            print(f"📅 Processando mapa: {chave}, Unidade: {mapa.unidade}, Lote ID: {mapa.lote_id}")
            
            for campo in campos_refeicoes:
                valores = getattr(mapa, campo, []) or []
                print(f"  {campo}: tipo={type(valores)}, len={len(valores) if isinstance(valores, list) else 'N/A'}, sample={valores[:3] if isinstance(valores, list) and len(valores) > 0 else valores}")
                
                # Verificar se é string JSON que precisa ser parseado
                if isinstance(valores, str):
                    try:
                        import json
                        valores = json.loads(valores)
                    except:
                        valores = []
                
                total_campo = sum(valores) if isinstance(valores, list) else 0
                dados_por_periodo[chave][campo] += total_campo
                dados_por_periodo[chave]['total_refeicoes'] += total_campo
                
                if total_campo > 0:
                    print(f"  ✅ {campo}: {total_campo}")
            
            valores_siisp = mapa.dados_siisp or []
            if isinstance(valores_siisp, str):
                try:
                    import json
                    valores_siisp = json.loads(valores_siisp)
                except:
                    valores_siisp = []
            total_siisp = sum(valores_siisp) if isinstance(valores_siisp, list) else 0
            dados_por_periodo[chave]['dados_siisp'] += total_siisp
            
            print(f"  Total do período {chave}: {dados_por_periodo[chave]['total_refeicoes']}")
        
        elif periodo == 'ano':
            # Agrupar por ano
            chave = str(mapa.ano)
            
            print(f"📅 Processando mapa ANO: {chave}, Unidade: {mapa.unidade}, Lote ID: {mapa.lote_id}")
            
            for campo in campos_refeicoes:
                valores = getattr(mapa, campo, []) or []
                
                # Verificar se é string JSON
                if isinstance(valores, str):
                    try:
                        import json
                        valores = json.loads(valores)
                    except:
                        valores = []
                
                total_campo = sum(valores) if isinstance(valores, list) else 0
                dados_por_periodo[chave][campo] += total_campo
                dados_por_periodo[chave]['total_refeicoes'] += total_campo
                
                if total_campo > 0:
                    print(f"  ✅ {campo}: {total_campo}")
            
            valores_siisp = mapa.dados_siisp or []
            if isinstance(valores_siisp, str):
                try:
                    import json
                    valores_siisp = json.loads(valores_siisp)
                except:
                    valores_siisp = []
            total_siisp = sum(valores_siisp) if isinstance(valores_siisp, list) else 0
            dados_por_periodo[chave]['dados_siisp'] += total_siisp
            
            print(f"  Total do período {chave}: {dados_por_periodo[chave]['total_refeicoes']}")
    
    # Ordenar por período
    labels_ordenados = sorted(dados_por_periodo.keys())
    
    # Preparar dados para o gráfico
    resultado = {
        'labels': labels_ordenados,
        'datasets': {}
    }
    
    # Adicionar cada tipo de refeição
    for campo in campos_refeicoes + ['dados_siisp', 'total_refeicoes']:
        resultado['datasets'][campo] = [dados_por_periodo[label][campo] for label in labels_ordenados]
    
    return resultado


def formatar_label_periodo(chave, periodo):
    """
    Formata a label do período para exibição no gráfico
    """
    if periodo == 'mes':
        # Formato: 2025-01 -> Jan/2025
        try:
            data = datetime.strptime(chave, '%Y-%m')
            meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
                     'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            return f"{meses[data.month - 1]}/{data.year}"
        except:
            return chave
    
    elif periodo == 'ano':
        return chave
    
    return chave


def agregar_por_grupo(mapas, periodo='mes', tipo_grupo='unidade', lotes_ids=None):
    """
    Agrega dados de mapas por grupo (unidade ou lote) e período
    
    Args:
        mapas: Lista de objetos Mapa
        periodo: 'dia', 'semana', 'mes' ou 'ano'
        tipo_grupo: 'unidade' ou 'lote'
        lotes_ids: Lista de IDs de lotes (usado para pegar nomes dos lotes)
    
    Returns:
        dict com labels, grupos e valores para múltiplas linhas no gráfico
    """
    from collections import defaultdict
    import json
    
    # Estrutura: {grupo_nome: {periodo: total}}
    dados_por_grupo = defaultdict(lambda: defaultdict(int))
    
    campos_refeicoes = [
        'cafe_interno', 'cafe_funcionario', 
        'almoco_interno', 'almoco_funcionario',
        'lanche_interno', 'lanche_funcionario', 
        'jantar_interno', 'jantar_funcionario'
    ]
    
    # Processar cada mapa
    for mapa in mapas:
        # Determinar o nome do grupo
        if tipo_grupo == 'unidade':
            grupo_nome = mapa.unidade
        else:  # tipo_grupo == 'lote'
            # Buscar nome do lote
            from functions.lotes import Lote
            lote = db.session.get(Lote, mapa.lote_id)
            grupo_nome = lote.nome if lote else f"Lote {mapa.lote_id}"
        
        # Determinar a chave do período
        if periodo == 'mes':
            chave_periodo = f"{mapa.ano}-{mapa.mes:02d}"
        elif periodo == 'ano':
            chave_periodo = str(mapa.ano)
        else:
            chave_periodo = f"{mapa.ano}-{mapa.mes:02d}"
        
        # Para períodos agregados (mes, semana, ano)
        total = 0
        for campo in campos_refeicoes:
            valores = getattr(mapa, campo, []) or []
            if isinstance(valores, str):
                try:
                    valores = json.loads(valores)
                except:
                    valores = []
            total += sum(valores) if isinstance(valores, list) else 0
        
        dados_por_grupo[grupo_nome][chave_periodo] += total
    
    # Obter todos os períodos únicos e ordenar
    todos_periodos = set()
    for grupo_dados in dados_por_grupo.values():
        todos_periodos.update(grupo_dados.keys())
    
    periodos_ordenados = sorted(list(todos_periodos))
    
    # Preparar dados no formato esperado pelo frontend
    grupos = []
    for grupo_nome in sorted(dados_por_grupo.keys()):
        valores = [dados_por_grupo[grupo_nome].get(periodo, 0) for periodo in periodos_ordenados]
        grupos.append({
            'nome': grupo_nome,
            'valores': valores
        })
    
    print(f"✅ Agregação por {tipo_grupo}: {len(grupos)} grupos, {len(periodos_ordenados)} períodos")
    
    return {
        'labels': periodos_ordenados,
        'grupos': grupos,
        'datasets': {}  # Vazio pois usamos grupos
    }


def calcular_projecao(dados, periodo='mes', meses_futuros=6):
    """
    Calcula projeção de dados futuros baseada em dados históricos
    
    Args:
        dados: dict com labels e datasets/grupos dos dados históricos
        periodo: 'mes' ou 'ano'
        meses_futuros: número de meses a projetar (padrão: 6)
    
    Returns:
        dict com labels e valores projetados (ou grupos_projetados para modo separado)
    """
    try:
        from datetime import datetime, timedelta
        from dateutil.relativedelta import relativedelta
        import statistics
        
        labels_historicos = dados.get('labels', [])
        
        if not labels_historicos or len(labels_historicos) == 0:
            return {
                'labels_projetados': [],
                'valores_projetados': [],
                'grupos_projetados': [],
                'media_historica': 0,
                'tendencia': 'estável'
            }
        
        # Verificar se é modo separado (por unidade ou lote)
        if 'grupos' in dados and dados['grupos']:
            # Modo separado - calcular projeção para cada grupo
            grupos_projetados = []
            
            for grupo in dados['grupos']:
                valores_grupo = grupo.get('valores', [])
                
                if not valores_grupo or len(valores_grupo) == 0:
                    continue
                
                # Usar Média Móvel Ponderada com limite de variação (mais conservador)
                n = len(valores_grupo)
                
                # Calcular média ponderada dos últimos períodos
                if n >= 3:
                    ultimos_valores = valores_grupo[-3:]
                    pesos = [0.2, 0.3, 0.5]
                    media_ponderada_grupo = sum(v * p for v, p in zip(ultimos_valores, pesos))
                else:
                    media_ponderada_grupo = statistics.mean(valores_grupo) if valores_grupo else 0
                
                # Calcular tendência baseada na variação recente
                if n >= 2:
                    variacao_recente = valores_grupo[-1] - valores_grupo[-2]
                    percentual_variacao = (variacao_recente / valores_grupo[-2] * 100) if valores_grupo[-2] != 0 else 0
                    
                    # Limitar variação máxima por período a ±5%
                    if percentual_variacao > 5:
                        percentual_variacao = 5
                    elif percentual_variacao < -5:
                        percentual_variacao = -5
                    
                    fator_crescimento_grupo = 1 + (percentual_variacao / 100)
                else:
                    fator_crescimento_grupo = 1.0
                    percentual_variacao = 0
                
                # Detectar tendência
                if percentual_variacao > 1:
                    tendencia_grupo = 'crescimento'
                elif percentual_variacao < -1:
                    tendencia_grupo = 'decrescimento'
                else:
                    tendencia_grupo = 'estável'
                
                # Calcular valores projetados usando média móvel + tendência limitada
                valores_projetados_grupo = []
                valor_base = media_ponderada_grupo
                for i in range(1, meses_futuros + 1):
                    valor_projetado = valor_base * (fator_crescimento_grupo ** i)
                    valor_projetado = max(0, valor_projetado)
                    valores_projetados_grupo.append(round(valor_projetado))
                
                # Calcular média dos últimos 3 períodos como referência
                ultimos_3 = valores_grupo[-3:] if len(valores_grupo) >= 3 else valores_grupo
                media_recente = statistics.mean(ultimos_3) if ultimos_3 else 0
                
                grupos_projetados.append({
                    'nome': grupo.get('nome'),
                    'valores': valores_projetados_grupo,
                    'media': round(media_recente),
                    'tendencia': tendencia_grupo,
                    'inclinacao': round(percentual_variacao, 2)
                })
            
            # Calcular total para estatísticas gerais
            valores_historicos = []
            for grupo in dados['grupos']:
                for i, valor in enumerate(grupo.get('valores', [])):
                    if i >= len(valores_historicos):
                        valores_historicos.append(0)
                    valores_historicos[i] += valor
        else:
            # Modo acumulado
            grupos_projetados = []
            valores_historicos = dados['datasets'].get('total_refeicoes', [])
        
        if not valores_historicos or len(valores_historicos) == 0:
            return {
                'labels_projetados': [],
                'valores_projetados': [],
                'media_historica': 0,
                'tendencia': 'estável'
            }
        
        # Usar Média Móvel Ponderada com limite de variação (mais conservador)
        n = len(valores_historicos)
        
        # Calcular média dos últimos períodos (mais peso nos recentes)
        if n >= 3:
            # Pesos: último período = 50%, penúltimo = 30%, antepenúltimo = 20%
            ultimos_valores = valores_historicos[-3:]
            pesos = [0.2, 0.3, 0.5]
            media_ponderada = sum(v * p for v, p in zip(ultimos_valores, pesos))
        else:
            media_ponderada = statistics.mean(valores_historicos) if valores_historicos else 0
        
        # Calcular tendência baseada na diferença entre últimos períodos
        if n >= 2:
            variacao_recente = valores_historicos[-1] - valores_historicos[-2]
            percentual_variacao = (variacao_recente / valores_historicos[-2] * 100) if valores_historicos[-2] != 0 else 0
            
            # Limitar variação máxima por período a ±5%
            if percentual_variacao > 5:
                percentual_variacao = 5
            elif percentual_variacao < -5:
                percentual_variacao = -5
            
            fator_crescimento = 1 + (percentual_variacao / 100)
        else:
            fator_crescimento = 1.0
            percentual_variacao = 0
        
        # Detectar tendência
        if percentual_variacao > 1:
            tendencia = 'crescimento'
        elif percentual_variacao < -1:
            tendencia = 'decrescimento'
        else:
            tendencia = 'estável'
        
        # Calcular média dos últimos 3 períodos para métricas
        ultimos_3 = valores_historicos[-3:] if len(valores_historicos) >= 3 else valores_historicos
        media_historica = statistics.mean(ultimos_3) if ultimos_3 else 0
        
        fator_tendencia = fator_crescimento
        
        # Gerar labels e valores projetados
        labels_projetados = []
        valores_projetados = []
        
        # Pegar última data dos dados históricos
        ultima_label = labels_historicos[-1]
        
        if periodo == 'mes':
            # Parse última data (formato: YYYY-MM)
            try:
                ultima_data = datetime.strptime(ultima_label, '%Y-%m')
            except:
                ultima_data = datetime.now()
            
            # Gerar próximos 6 meses usando média móvel ponderada + tendência limitada
            valor_base = media_ponderada
            for i in range(1, meses_futuros + 1):
                proxima_data = ultima_data + relativedelta(months=i)
                label_projetado = proxima_data.strftime('%Y-%m')
                labels_projetados.append(label_projetado)
                
                # Aplicar tendência de forma gradual e limitada
                valor_projetado = valor_base * (fator_crescimento ** i)
                valor_projetado = max(0, valor_projetado)  # Não permitir valores negativos
                valores_projetados.append(round(valor_projetado))
        
        elif periodo == 'ano':
            # Para ano, projetar apenas 1 ano à frente
            try:
                ultimo_ano = int(ultima_label)
            except:
                ultimo_ano = datetime.now().year
            
            proximo_ano = ultimo_ano + 1
            labels_projetados.append(str(proximo_ano))
            
            # Usar média ponderada com tendência limitada
            valor_projetado = media_ponderada * fator_crescimento
            valor_projetado = max(0, valor_projetado)
            valores_projetados.append(round(valor_projetado))
        
        print(f"📊 Projeção calculada: {len(labels_projetados)} períodos, média histórica: {media_historica:.0f}, tendência: {tendencia}")
        if grupos_projetados:
            print(f"📊 Grupos projetados: {len(grupos_projetados)} grupos")
        
        return {
            'labels_projetados': labels_projetados,
            'valores_projetados': valores_projetados,
            'grupos_projetados': grupos_projetados,
            'media_historica': round(media_historica),
            'tendencia': tendencia,
            'fator_tendencia': fator_tendencia
        }
    
    except Exception as e:
        print(f"❌ Erro ao calcular projeção: {e}")
        import traceback
        traceback.print_exc()
        return {
            'labels_projetados': [],
            'valores_projetados': [],
            'grupos_projetados': [],
            'media_historica': 0,
            'tendencia': 'estável'
        }


def buscar_dados_gastos(lotes_ids, unidades, periodo='mes', data_inicio=None, data_fim=None, modo='acumulado'):
    """
    Busca dados de gastos com refeições para gerar gráficos
    
    Args:
        lotes_ids: Lista de IDs dos lotes
        unidades: Lista de nomes das unidades
        periodo: 'dia', 'semana', 'mes' ou 'ano'
        data_inicio: Data de início (opcional)
        data_fim: Data de fim (opcional)
        modo: 'acumulado', 'unidade' ou 'lote'
    
    Returns:
        dict com dados de gastos agregados para o gráfico
    """
    try:
        if not lotes_ids or len(lotes_ids) == 0:
            print("⚠️ Nenhum lote selecionado - retornando gastos vazios")
            return {
                'success': True,
                'dados': {'labels': [], 'labels_formatados': [], 'datasets': {}, 'grupos': []},
                'total_registros': 0
            }
        
        if not unidades or len(unidades) == 0:
            print("⚠️ Nenhuma unidade selecionada - retornando gastos vazios")
            return {
                'success': True,
                'dados': {'labels': [], 'labels_formatados': [], 'datasets': {}, 'grupos': []},
                'total_registros': 0
            }
        
        # Buscar preços dos lotes
        precos_por_lote = {}
        for lote_id in lotes_ids:
            lote = db.session.get(Lote, lote_id)
            print(f"💰 Verificando lote {lote_id}: encontrado={lote is not None}")
            if lote:
                print(f"💰 Lote {lote_id} - precos={lote.precos}, tipo={type(lote.precos)}")
            
            if lote and lote.precos:
                try:
                    precos = json.loads(lote.precos) if isinstance(lote.precos, str) else lote.precos
                    precos_por_lote[lote_id] = precos
                    print(f"💰 Preços carregados do lote {lote_id}: {precos}")
                except Exception as e:
                    print(f"❌ Erro ao parsear preços do lote {lote_id}: {e}")
                    precos_por_lote[lote_id] = {}
            else:
                print(f"⚠️ Lote {lote_id} sem preços definidos")
                precos_por_lote[lote_id] = {}
        
        # Buscar mapas
        query = db.session.query(Mapa)
        query = query.filter(Mapa.lote_id.in_(lotes_ids))
        query = query.filter(Mapa.unidade.in_(unidades))
        
        if data_inicio:
            query = query.filter(Mapa.ano >= data_inicio.year)
        if data_fim:
            query = query.filter(Mapa.ano <= data_fim.year)
        
        mapas = query.all()
        print(f"💰 Buscar gastos: {len(mapas)} mapas encontrados")
        
        # Agregar gastos por período e modo
        if modo == 'acumulado':
            dados_agregados = agregar_gastos_por_periodo(mapas, periodo, precos_por_lote)
        elif modo == 'unidade':
            dados_agregados = agregar_gastos_por_grupo(mapas, periodo, 'unidade', precos_por_lote)
        elif modo == 'lote':
            dados_agregados = agregar_gastos_por_grupo(mapas, periodo, 'lote', precos_por_lote, lotes_ids)
        else:
            dados_agregados = agregar_gastos_por_periodo(mapas, periodo, precos_por_lote)
        
        return {
            'success': True,
            'dados': dados_agregados,
            'total_registros': len(mapas)
        }
    
    except Exception as e:
        print(f"❌ Erro ao buscar gastos: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


def agregar_gastos_por_periodo(mapas, periodo='mes', precos_por_lote=None):
    """
    Agrega gastos de mapas por período
    
    Returns:
        dict com labels e valores de gastos para o gráfico
    """
    if precos_por_lote is None:
        precos_por_lote = {}
    
    dados_por_periodo = defaultdict(lambda: {
        'cafe_interno': 0, 'cafe_funcionario': 0,
        'almoco_interno': 0, 'almoco_funcionario': 0,
        'lanche_interno': 0, 'lanche_funcionario': 0,
        'jantar_interno': 0, 'jantar_funcionario': 0,
        'total_gastos': 0
    })
    
    campos_refeicoes = [
        'cafe_interno', 'cafe_funcionario', 
        'almoco_interno', 'almoco_funcionario',
        'lanche_interno', 'lanche_funcionario', 
        'jantar_interno', 'jantar_funcionario'
    ]
    
    for mapa in mapas:
        # Obter preços do lote
        precos = precos_por_lote.get(mapa.lote_id, {})
        
        # Criar chave baseada no período
        if periodo == 'mes':
            chave = f"{mapa.ano}-{mapa.mes:02d}"
        elif periodo == 'ano':
            chave = str(mapa.ano)
        else:
            chave = f"{mapa.ano}-{mapa.mes:02d}"
        
        print(f"💰 Processando gastos: {chave}, Unidade: {mapa.unidade}, Lote ID: {mapa.lote_id}")
        
        for campo in campos_refeicoes:
            valores = getattr(mapa, campo, []) or []
            
            if isinstance(valores, str):
                try:
                    valores = json.loads(valores)
                except:
                    valores = []
            
            total_refeicoes = sum(valores) if isinstance(valores, list) else 0
            
            # Mapear campo para estrutura de preços
            # cafe_interno -> cafe.interno, cafe_funcionario -> cafe.funcionario
            partes = campo.split('_')  # ['cafe', 'interno'] ou ['almoco', 'funcionario']
            if len(partes) == 2:
                tipo_refeicao = partes[0]  # 'cafe', 'almoco', 'lanche', 'jantar'
                tipo_pessoa = partes[1]     # 'interno', 'funcionario'
                
                # Buscar preço na estrutura: precos['cafe']['interno']
                preco = 0
                if tipo_refeicao in precos and tipo_pessoa in precos[tipo_refeicao]:
                    preco_str = precos[tipo_refeicao][tipo_pessoa]
                    try:
                        preco = float(preco_str)
                    except:
                        preco = 0
            else:
                preco = 0
            
            gasto_campo = total_refeicoes * preco
            
            dados_por_periodo[chave][campo] += gasto_campo
            dados_por_periodo[chave]['total_gastos'] += gasto_campo
            
            if gasto_campo > 0:
                print(f"  ✅ {campo}: {total_refeicoes} refeições × R$ {preco:.2f} = R$ {gasto_campo:.2f}")
        
        print(f"  Total gastos período {chave}: R$ {dados_por_periodo[chave]['total_gastos']:.2f}")
    
    # Ordenar por período
    labels_ordenados = sorted(dados_por_periodo.keys())
    
    # Preparar dados para o gráfico
    resultado = {
        'labels': labels_ordenados,
        'datasets': {}
    }
    
    # Adicionar cada tipo de refeição e total
    for campo in campos_refeicoes + ['total_gastos']:
        resultado['datasets'][campo] = [dados_por_periodo[label][campo] for label in labels_ordenados]
    
    return resultado


def agregar_gastos_por_grupo(mapas, periodo='mes', tipo_grupo='unidade', precos_por_lote=None, lotes_ids=None):
    """
    Agrega gastos de mapas por grupo (unidade ou lote) e período
    
    Returns:
        dict com labels, grupos e valores de gastos para múltiplas linhas no gráfico
    """
    if precos_por_lote is None:
        precos_por_lote = {}
    
    # Estrutura: {grupo_nome: {periodo: total}}
    dados_por_grupo = defaultdict(lambda: defaultdict(float))
    
    campos_refeicoes = [
        'cafe_interno', 'cafe_funcionario', 
        'almoco_interno', 'almoco_funcionario',
        'lanche_interno', 'lanche_funcionario', 
        'jantar_interno', 'jantar_funcionario'
    ]
    
    for mapa in mapas:
        # Determinar o nome do grupo
        if tipo_grupo == 'unidade':
            grupo_nome = mapa.unidade
        else:  # tipo_grupo == 'lote'
            lote = db.session.get(Lote, mapa.lote_id)
            grupo_nome = lote.nome if lote else f"Lote {mapa.lote_id}"
        
        # Determinar a chave do período
        if periodo == 'mes':
            chave_periodo = f"{mapa.ano}-{mapa.mes:02d}"
        elif periodo == 'ano':
            chave_periodo = str(mapa.ano)
        else:
            chave_periodo = f"{mapa.ano}-{mapa.mes:02d}"
        
        # Obter preços do lote
        precos = precos_por_lote.get(mapa.lote_id, {})
        
        # Calcular gastos
        total_gastos = 0
        for campo in campos_refeicoes:
            valores = getattr(mapa, campo, []) or []
            if isinstance(valores, str):
                try:
                    valores = json.loads(valores)
                except:
                    valores = []
            
            total_refeicoes = sum(valores) if isinstance(valores, list) else 0
            
            # Mapear campo para estrutura de preços
            partes = campo.split('_')
            if len(partes) == 2:
                tipo_refeicao = partes[0]
                tipo_pessoa = partes[1]
                
                preco = 0
                if tipo_refeicao in precos and tipo_pessoa in precos[tipo_refeicao]:
                    preco_str = precos[tipo_refeicao][tipo_pessoa]
                    try:
                        preco = float(preco_str)
                    except:
                        preco = 0
            else:
                preco = 0
            
            gasto_campo = total_refeicoes * preco
            total_gastos += gasto_campo
        
        dados_por_grupo[grupo_nome][chave_periodo] += total_gastos
    
    # Obter todos os períodos únicos e ordenar
    todos_periodos = set()
    for grupo_dados in dados_por_grupo.values():
        todos_periodos.update(grupo_dados.keys())
    
    periodos_ordenados = sorted(list(todos_periodos))
    
    # Preparar dados no formato esperado pelo frontend
    grupos = []
    for grupo_nome in sorted(dados_por_grupo.keys()):
        valores = [dados_por_grupo[grupo_nome].get(periodo, 0) for periodo in periodos_ordenados]
        grupos.append({
            'nome': grupo_nome,
            'valores': valores
        })
    
    print(f"✅ Agregação gastos por {tipo_grupo}: {len(grupos)} grupos, {len(periodos_ordenados)} períodos")
    
    return {
        'labels': periodos_ordenados,
        'grupos': grupos,
        'datasets': {}
    }
