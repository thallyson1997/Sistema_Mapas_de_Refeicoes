"""
Funções para geração de relatórios e dados para gráficos
"""
from datetime import datetime, timedelta
from collections import defaultdict
from functions.models import db, Mapa
from sqlalchemy import and_, or_


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
        dict com labels e valores projetados
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
                'media_historica': 0,
                'tendencia': 'estável'
            }
        
        # Calcular valores totais históricos para análise de tendência
        valores_historicos = []
        
        if 'grupos' in dados and dados['grupos']:
            # Modo separado (por unidade ou lote) - somar todos os grupos
            for grupo in dados['grupos']:
                for i, valor in enumerate(grupo.get('valores', [])):
                    if i >= len(valores_historicos):
                        valores_historicos.append(0)
                    valores_historicos[i] += valor
        elif 'datasets' in dados and dados['datasets'].get('total_refeicoes'):
            # Modo acumulado
            valores_historicos = dados['datasets']['total_refeicoes']
        else:
            valores_historicos = []
        
        if not valores_historicos or len(valores_historicos) == 0:
            return {
                'labels_projetados': [],
                'valores_projetados': [],
                'media_historica': 0,
                'tendencia': 'estável'
            }
        
        # Calcular média dos últimos períodos (até 6 períodos)
        ultimos_valores = valores_historicos[-6:] if len(valores_historicos) >= 6 else valores_historicos
        media_historica = statistics.mean(ultimos_valores) if ultimos_valores else 0
        
        # Detectar tendência (crescimento, decrescimento, estável)
        tendencia = 'estável'
        if len(valores_historicos) >= 3:
            primeira_metade = valores_historicos[:len(valores_historicos)//2]
            segunda_metade = valores_historicos[len(valores_historicos)//2:]
            
            media_primeira = statistics.mean(primeira_metade) if primeira_metade else 0
            media_segunda = statistics.mean(segunda_metade) if segunda_metade else 0
            
            diferenca_percentual = ((media_segunda - media_primeira) / media_primeira * 100) if media_primeira > 0 else 0
            
            if diferenca_percentual > 5:
                tendencia = 'crescimento'
            elif diferenca_percentual < -5:
                tendencia = 'decrescimento'
        
        # Calcular fator de tendência
        fator_tendencia = 1.0
        if tendencia == 'crescimento':
            fator_tendencia = 1.02  # 2% de crescimento por período
        elif tendencia == 'decrescimento':
            fator_tendencia = 0.98  # 2% de decrescimento por período
        
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
            
            # Gerar próximos 6 meses
            for i in range(1, meses_futuros + 1):
                proxima_data = ultima_data + relativedelta(months=i)
                label_projetado = proxima_data.strftime('%Y-%m')
                labels_projetados.append(label_projetado)
                
                # Valor projetado com tendência aplicada
                valor_projetado = media_historica * (fator_tendencia ** i)
                valores_projetados.append(round(valor_projetado))
        
        elif periodo == 'ano':
            # Para ano, projetar apenas 1 ano à frente
            try:
                ultimo_ano = int(ultima_label)
            except:
                ultimo_ano = datetime.now().year
            
            proximo_ano = ultimo_ano + 1
            labels_projetados.append(str(proximo_ano))
            
            # Multiplicar média mensal por 12 para estimativa anual
            valor_projetado = media_historica * fator_tendencia
            valores_projetados.append(round(valor_projetado))
        
        print(f"📊 Projeção calculada: {len(labels_projetados)} períodos, média histórica: {media_historica:.0f}, tendência: {tendencia}")
        
        return {
            'labels_projetados': labels_projetados,
            'valores_projetados': valores_projetados,
            'media_historica': round(media_historica),
            'tendencia': tendencia,
            'fator_tendencia': fator_tendencia
        }
    
    except Exception as e:
        print(f"❌ Erro ao calcular projeção: {e}")
        return {
            'labels_projetados': [],
            'valores_projetados': [],
            'media_historica': 0,
            'tendencia': 'estável'
        }
