from flask import Flask, request, jsonify, render_template, session, flash, redirect, url_for, abort, send_file
from flask_sqlalchemy import SQLAlchemy
import os
import json
import re
import io
import calendar
from datetime import datetime
from copy import copy
from functions.models import db, Usuario, Lote
from functions.utils import (
    cadastrar_novo_usuario,
    validar_cadastro_no_usuario,
    validar_cpf,
    validar_email,
    validar_telefone,
    validar_matricula,
    validar_username,
    validar_senha,
    validar_login,
    salvar_novo_lote,
    editar_lote,
    _load_lotes_data,
    _load_unidades_data,
    carregar_lotes_para_dashboard,
    normalizar_precos,
    salvar_mapas_raw,
    calcular_metricas_lotes,
    preparar_dados_entrada_manual,
    reordenar_registro_mapas,
    adicionar_siisp_em_mapa,
    excluir_mapa,
    _load_mapas_partitioned,
    gerar_excel_exportacao,
    gerar_excel_exportacao_multiplos_lotes,
    calcular_ultima_atividade_lotes
)

app = Flask(__name__)
app.secret_key = 'sgmrp_seap_2025_secret_key_desenvolvimento'
app.config['DEBUG'] = True

# Configuração do banco SQLite

# Garante que o diretório 'dados/' existe antes de inicializar o banco
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.join(BASE_DIR, 'dados')
os.makedirs(DADOS_DIR, exist_ok=True)

db_path = os.path.join(DADOS_DIR, 'dados.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.join(BASE_DIR, 'dados')

# Teste de conexão ao banco de dados
import sqlite3
try:
    conn = sqlite3.connect(os.path.join(DADOS_DIR, 'dados.db'))
    conn.close()
    print('✅ Conexão com dados/dados.db funcionando!')
except Exception as e:
    print(f'❌ Erro ao conectar ao banco: {e}')

#FEITOS
@app.route('/')
def index():
    #Página inicial
    return render_template('index.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    #Página de cadastro
    if request.method == 'POST':
        form_data = request.form.to_dict()
        resp = cadastrar_novo_usuario(form_data)

        accept = request.headers.get('Accept', '')
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if request.is_json or is_ajax or 'application/json' in accept:
            return jsonify(resp), (200 if resp.get('ok') else 400)

        if resp.get('ok'):
            flash(resp.get('mensagem', 'Usuário cadastrado com sucesso. Aguarde a aprovação do seu cadastro.'))
            return redirect(url_for('login'))
        else:
            flash(resp.get('mensagem', 'Erro ao cadastrar usuário'))
            return render_template('cadastro.html', form_data=form_data, erro=resp.get('mensagem'))

    return render_template('cadastro.html')

@app.route('/api/validar-campo', methods=['POST'])
def api_validar_campo():
    # Endpoint para validação de campos via API
    try:
        data = request.get_json(force=True, silent=True) or {}
        campo = data.get('campo')
        valor = data.get('valor')
        form = data.get('form')
        if isinstance(form, dict):
            result = validar_cadastro_no_usuario(form)
            return jsonify(result), 200

        if campo and valor is not None:
            campo = campo.lower()
            if campo == 'cpf':
                res = validar_cpf(valor)
                if isinstance(res, dict):
                    res['campo'] = 'cpf'
                return jsonify(res), 200
            if campo == 'email':
                res = validar_email(valor)
                if isinstance(res, dict):
                    res['campo'] = 'email'
                return jsonify(res), 200
            if campo == 'telefone':
                res = validar_telefone(valor)
                if isinstance(res, dict):
                    res['campo'] = 'telefone'
                return jsonify(res), 200
            if campo == 'matricula':
                res = validar_matricula(valor)
                if isinstance(res, dict):
                    res['campo'] = 'matricula'
                return jsonify(res), 200
            if campo == 'usuario':
                res = validar_username(valor)
                if isinstance(res, dict):
                    res['campo'] = 'usuario'
                return jsonify(res), 200
            if campo == 'senha':
                res = {'valido': True, 'mensagem': 'OK', 'campo': 'senha'}
                return jsonify(res), 200

        default_res = {'valido': True, 'mensagem': 'OK'}
        if campo:
            default_res['campo'] = campo
        return jsonify(default_res), 200
    except Exception:
        return jsonify({'valido': False, 'mensagem': 'Erro interno'}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    #Página de login
    if request.method == 'POST':
        form = request.form.to_dict()
        login_val = form.get('usuario') or form.get('email') or form.get('login') or form.get('username')
        senha = form.get('senha')

        result = validar_login(login_val, senha)

        accept = request.headers.get('Accept', '')
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if request.is_json or is_ajax or 'application/json' in accept:
            return jsonify(result), (200 if result.get('ok') else 400)

        if result.get('ok'):
            user = result.get('user') or {}
            session['usuario_logado'] = True
            session['usuario_id'] = user.get('id')
            session['usuario_nome'] = user.get('nome') or user.get('usuario')
            return redirect(url_for('home', login='1'))
        else:
            flash(result.get('mensagem', 'Credenciais inválidas'))
            return render_template('login.html', erro=result.get('mensagem'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    # Limpa a sessão do usuário e redireciona para a página de login.
    session.pop('usuario_logado', None)
    session.pop('usuario_id', None)
    session.pop('usuario_nome', None)

    accept = request.headers.get('Accept', '')
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if request.is_json or is_ajax or 'application/json' in accept:
        return jsonify({'ok': True, 'mensagem': 'Logout realizado com sucesso.'}), 200

    flash('Você saiu com sucesso.')
    return redirect(url_for('login'))

@app.route('/api/novo-lote', methods=['POST'])
def api_novo_lote():
    # Endpoint para salvar um novo lote via API
    try:
        data = request.get_json(force=True, silent=True) or {}
        res = salvar_novo_lote(data)
        if res.get('success'):
            return jsonify({'success': True, 'id': res.get('id')}), 200
        else:
            return jsonify({'success': False, 'error': res.get('error', 'Erro ao salvar')}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': 'Erro interno'}), 500

@app.route('/api/editar-lote/<int:lote_id>', methods=['PUT', 'POST'])
def api_editar_lote(lote_id):
    # Endpoint para editar um lote existente via API
    try:
        data = request.get_json(force=True, silent=True) or {}
        res = editar_lote(lote_id, data)
        if res.get('success'):
            return jsonify({'success': True, 'lote': res.get('lote')}), 200
        else:
            return jsonify({'success': False, 'error': res.get('error', 'Erro ao editar')}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': 'Erro interno'}), 500

@app.route('/api/editar-lote/<int:lote_id>', methods=['DELETE'])
def api_excluir_lote(lote_id):
    # Endpoint para excluir um lote existente via API
    try:
        from functions.lotes import deletar_lote
        success = deletar_lote(lote_id, db)
        if success:
            return jsonify({'success': True, 'id': lote_id}), 200
        else:
            return jsonify({'success': False, 'error': f'Lote {lote_id} não encontrado'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erro interno: {e}'}), 500

# ----- Rotas API para Unidades -----
@app.route('/api/adicionar-unidade', methods=['POST'])
def api_adicionar_unidade_route():
    """Adiciona uma nova unidade ao lote"""
    try:
        from functions.unidades import api_adicionar_unidade
        data = request.get_json()
        
        if not data.get('lote_id'):
            return jsonify({'success': False, 'message': 'ID do lote é obrigatório'}), 400
        
        if not data.get('nome'):
            return jsonify({'success': False, 'message': 'Nome da unidade é obrigatório'}), 400
        
        resultado = api_adicionar_unidade(
            lote_id=data['lote_id'],
            nome=data['nome'],
            quantitativos_unidade=data.get('quantitativos_unidade', '{}'),
            valor_contratual_unidade=data.get('valor_contratual_unidade', 0.0),
            unidade_principal_id=data.get('unidade_principal_id'),
            sub_empresa=data.get('sub_empresa', False),
            delegacia=data.get('delegacia', False)
        )
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 400
            
    except Exception as e:
        print(f'Erro na rota adicionar-unidade: {str(e)}')
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500


@app.route('/api/editar-unidade/<int:unidade_id>', methods=['POST', 'PUT'])
def api_editar_unidade_route(unidade_id):
    """Edita uma unidade existente"""
    try:
        from functions.unidades import api_editar_unidade
        data = request.get_json()
        
        resultado = api_editar_unidade(
            unidade_id=unidade_id,
            nome=data.get('nome'),
            quantitativos_unidade=data.get('quantitativos_unidade'),
            valor_contratual_unidade=data.get('valor_contratual_unidade'),
            ativo=data.get('ativo'),
            unidade_principal_id=data.get('unidade_principal_id'),
            sub_empresa=data.get('sub_empresa'),
            delegacia=data.get('delegacia')
        )
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 400
            
    except Exception as e:
        print(f'Erro na rota editar-unidade: {str(e)}')
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500


@app.route('/api/excluir-unidade/<int:unidade_id>', methods=['DELETE'])
def api_excluir_unidade_route(unidade_id):
    """Exclui uma unidade"""
    try:
        from functions.unidades import api_excluir_unidade
        
        resultado = api_excluir_unidade(unidade_id)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 400
            
    except Exception as e:
        print(f'Erro na rota excluir-unidade: {str(e)}')
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500


@app.route('/api/listar-unidades/<int:lote_id>', methods=['GET'])
def api_listar_unidades_route(lote_id):
    """Lista todas as unidades de um lote"""
    try:
        from functions.unidades import api_listar_unidades
        
        resultado = api_listar_unidades(lote_id)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 400
            
    except Exception as e:
        print(f'Erro na rota listar-unidades: {str(e)}')
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500
@app.route('/home')
def home():
    #Página inicial
    mostrar_login_sucesso = request.args.get('login') == '1'
    usuario_nome = session.get('usuario_nome', '')
    dashboard_data = carregar_lotes_para_dashboard()
    lotes = dashboard_data.get('lotes', [])
    from functions.mapas import carregar_mapas_db, serialize_mapa
    mapas_dados = carregar_mapas_db()
    # Agrupar mapas por lote_id
    mapas_por_lote = {}
    for mapa in mapas_dados:
        lid = str(mapa.get('lote_id'))
        if lid not in mapas_por_lote:
            mapas_por_lote[lid] = []
        mapas_por_lote[lid].append(mapa)
    # Calcular total de refeições por lote
    campos_refeicoes = [
        'cafe_interno', 'cafe_funcionario', 'almoco_interno', 'almoco_funcionario',
        'lanche_interno', 'lanche_funcionario', 'jantar_interno', 'jantar_funcionario'
    ]
    for lote in lotes:
        lid = str(lote.get('id'))
        mapas_lote = mapas_por_lote.get(lid, [])
        total_refeicoes = 0
        for mapa in mapas_lote:
            for campo in campos_refeicoes:
                vals = mapa.get(campo, [])
                if isinstance(vals, list):
                    total_refeicoes += sum(int(x) if x is not None else 0 for x in vals)
        lote['total_refeicoes'] = total_refeicoes
    
    # Ordenar lotes: ativos primeiro, depois inativos
    lotes.sort(key=lambda x: (not x.get('ativo', True), x.get('id', 0)))
    
    return render_template('home.html', lotes=lotes, mapas_dados=mapas_dados,
                           mostrar_login_sucesso=mostrar_login_sucesso,
                           usuario_nome=usuario_nome)

@app.route('/lotes')
def lotes():
    #Página de listagem de lotes
    data = carregar_lotes_para_dashboard()
    lotes = data.get('lotes', [])
    from functions.mapas import carregar_mapas_db
    mapas = carregar_mapas_db()
    # Nota: calcular_metricas_lotes já foi chamada dentro de carregar_lotes_para_dashboard()
    # Nota: calcular_ultima_atividade_lotes já foi chamada dentro de _load_lotes_data() via lote_to_dict()
    # Não precisamos chamar novamente, pois isso sobrescreveria os valores

    # Debug: Mostrar cálculo de refeições por mês
    for lote in lotes:
        if 'refeicoes_por_mes' in lote:
            total_refeicoes = sum(lote['refeicoes_por_mes'].values())
            num_meses = len(lote['refeicoes_por_mes'])
            media = total_refeicoes / num_meses if num_meses > 0 else 0

    # Calcular refeições por mês para cada lote
    campos_refeicoes = [
        'cafe_interno', 'cafe_funcionario', 'almoco_interno', 'almoco_funcionario',
        'lanche_interno', 'lanche_funcionario', 'jantar_interno', 'jantar_funcionario'
    ]
    # Nota: calcular_metricas_lotes já calcula refeicoes_por_mes incluindo predecessores
    # Removido código duplicado que estava sobrescrevendo os valores

    empresas = []
    seen = set()
    for l in lotes:
        e = (l.get('empresa') or '').strip()
        if e and e not in seen:
            seen.add(e)
            empresas.append(e)
    empresas.sort()
    return render_template('lotes.html', lotes=lotes, empresas=empresas)

@app.route('/lote/<int:lote_id>')
def lote_detalhes(lote_id):
    #Página de detalhes do lote
    # Forçar recarregamento dos dados para evitar cache
    from functions.lotes import _load_lotes_data
    
    lotes = _load_lotes_data()

    lote = None
    for l in lotes:
        try:
            if int(l.get('id')) == int(lote_id):
                lote = l
                break
        except Exception:
            continue

    if lote is None:
        abort(404)
    
    # Converter todos os preços para float, inclusive aninhados
    precos = lote.get('precos', {})
    for tipo_refeicao in precos:
        if isinstance(precos[tipo_refeicao], dict):
            for subcampo in precos[tipo_refeicao]:
                try:
                    precos[tipo_refeicao][subcampo] = float(precos[tipo_refeicao][subcampo])
                except Exception:
                    precos[tipo_refeicao][subcampo] = 0.0
        else:
            try:
                precos[tipo_refeicao] = float(precos[tipo_refeicao])
            except Exception:
                precos[tipo_refeicao] = 0.0
    lote['precos'] = precos

    # Buscar nomes das unidades pelo campo unidades (lista de IDs)
    unidades_ids = lote.get('unidades') or []
    from functions.unidades import Unidade
    unidades_lote = []
    if unidades_ids:
        from flask import current_app
        session = db.session
        for uid in unidades_ids:
            unidade = session.get(Unidade, uid)
            if unidade:
                unidades_lote.append(unidade.nome)

    from functions.mapas import carregar_mapas_db, serialize_mapa
    
    # Buscar mapas do lote atual
    mapas_lote = carregar_mapas_db({'lote_id': lote.get('id')})
    
    # Se o lote tiver predecessor, buscar também os mapas do predecessor
    predecessor_id = lote.get('lote_predecessor_id')
    predecessor_data = None
    
    
    if predecessor_id:
        # Buscar dados do predecessor
        predecessor_lote = None
        for l in lotes:
            try:
                if int(l.get('id')) == int(predecessor_id):
                    predecessor_lote = l
                    break
            except Exception:
                continue
        
        if predecessor_lote:
            # Converter preços do predecessor para float
            precos_predecessor = predecessor_lote.get('precos', {})
            for tipo_refeicao in precos_predecessor:
                if isinstance(precos_predecessor[tipo_refeicao], dict):
                    for subcampo in precos_predecessor[tipo_refeicao]:
                        try:
                            precos_predecessor[tipo_refeicao][subcampo] = float(precos_predecessor[tipo_refeicao][subcampo])
                        except Exception:
                            precos_predecessor[tipo_refeicao][subcampo] = 0.0
                else:
                    try:
                        precos_predecessor[tipo_refeicao] = float(precos_predecessor[tipo_refeicao])
                    except Exception:
                        precos_predecessor[tipo_refeicao] = 0.0
            
            # Buscar mapas do predecessor
            mapas_predecessor = carregar_mapas_db({'lote_id': predecessor_id})
            
            # Adicionar mapas do predecessor à lista (mantendo lote_id original para cálculos)
            mapas_lote.extend(mapas_predecessor)
            
            # Passar dados do predecessor para o template
            predecessor_data = {
                'id': predecessor_lote.get('id'),
                'nome': predecessor_lote.get('nome'),
                'precos': precos_predecessor
            }
    
    return render_template('lote-detalhes.html', 
                         lote=lote, 
                         unidades_lote=unidades_lote, 
                         mapas_lote=mapas_lote,
                         predecessor_data=predecessor_data)

@app.route('/api/adicionar-dados', methods=['POST'])
def api_adicionar_dados():
    # Endpoint para adicionar dados de mapas via API
    try:
        data = request.get_json(force=True, silent=True)

        # --- Validação ANTES de salvar no banco ---
        lote_id = None
        data_inicio = None
        data_fim = None
        mes = None
        ano = None
        if isinstance(data, dict):
            lote_id = data.get('lote_id')
            mes = data.get('mes')
            ano = data.get('ano')
            if lote_id:
                try:
                    from functions.models import Lote
                    session_db = db.session
                    lote = session_db.get(Lote, lote_id)
                    if lote:
                        data_inicio = getattr(lote, 'data_inicio', None)
                        data_fim = getattr(lote, 'data_fim', None)
                except Exception as e:
                    pass
            pass
        # num_dias só pode ser calculado corretamente após o processamento dos dados (salvar_mapas_raw)

        # Validar se o mês/ano do mapa está dentro do período do lote
        periodo_invalido = False
        msg_erro_periodo = None
        if data_inicio and data_fim and mes and ano:
            try:
                # Considera o primeiro e último dia do mês informado
                data_mapa_inicio = datetime(int(ano), int(mes), 1)
                ultimo_dia = calendar.monthrange(int(ano), int(mes))[1]
                data_mapa_fim = datetime(int(ano), int(mes), ultimo_dia)
                if data_mapa_fim < datetime.strptime(str(data_inicio), "%Y-%m-%d") or data_mapa_inicio > datetime.strptime(str(data_fim), "%Y-%m-%d"):
                    periodo_invalido = True
                    msg_erro_periodo = f"O mapa ({mes}/{ano}) está fora do período do lote ({data_inicio} a {data_fim}) e não será salvo."
            except Exception as e:
                pass

        if periodo_invalido:
            # Tenta calcular num_dias do registro processado, se possível
            num_dias = 0
            try:
                registro_tmp = None
                # Se já for possível processar os dados para contar os dias
                campos_refeicoes = [
                    'cafe_interno', 'cafe_funcionario', 'almoco_interno', 'almoco_funcionario',
                    'lanche_interno', 'lanche_funcionario', 'jantar_interno', 'jantar_funcionario'
                ]
                for campo in campos_refeicoes:
                    vals = data.get(campo)
                    if isinstance(vals, list):
                        num_dias = max(num_dias, len(vals))
            except Exception:
                pass
            print(f"❌ {msg_erro_periodo} num_dias={num_dias}")
            return jsonify({'success': False, 'error': msg_erro_periodo}), 400


        # --- Só salva se o período for válido ---
        # Recorte dos dados do mapa para salvar apenas os dias dentro do contrato
        num_dias_validos = None
        if data_inicio and data_fim and mes and ano:
            try:
                # Converter datas para datetime
                data_inicio_dt = datetime.strptime(str(data_inicio), "%Y-%m-%d")
                data_fim_dt = datetime.strptime(str(data_fim), "%Y-%m-%d")
                # Dias do mês do mapa
                dias_do_mes = [datetime(int(ano), int(mes), d+1) for d in range(calendar.monthrange(int(ano), int(mes))[1])]
                # Índices dos dias dentro do contrato
                indices_validos = [i for i, dia in enumerate(dias_do_mes) if data_inicio_dt <= dia <= data_fim_dt]
                num_dias_validos = len(indices_validos)
                # Recortar arrays de refeições e datas
                campos_refeicoes = [
                    'cafe_interno', 'cafe_funcionario', 'almoco_interno', 'almoco_funcionario',
                    'lanche_interno', 'lanche_funcionario', 'jantar_interno', 'jantar_funcionario'
                ]
                for campo in campos_refeicoes:
                    vals = data.get(campo)
                    if isinstance(vals, list):
                        recortado = [vals[i] for i in indices_validos]
                        data[campo] = recortado
                # Recortar campo 'datas' se existir
                if 'datas' in data and isinstance(data['datas'], list):
                    recortado_datas = [data['datas'][i] for i in indices_validos]
                    data['datas'] = recortado_datas
            except Exception as e:
                pass

        # Preencher dados_siisp com zeros apenas se não enviado ou vazio
        if 'dados_siisp' not in data or not data['dados_siisp']:
            # Tenta usar o número de dias válidos, senão tenta pelo campo 'datas', senão calcula pelo mês
            if num_dias_validos is not None:
                data['dados_siisp'] = [0] * num_dias_validos
            elif 'datas' in data and isinstance(data['datas'], list):
                data['dados_siisp'] = [0] * len(data['datas'])
            elif mes and ano:
                dias_mes = calendar.monthrange(int(ano), int(mes))[1]
                data['dados_siisp'] = [0] * dias_mes

        # Inclui data_inicio e data_fim no dicionário para garantir recorte após parsing tabular

        # Garante que data_inicio/data_fim estejam no dicionário para debug
        if lote_id:
            try:
                from functions.models import Lote
                session_db = db.session
                lote = session_db.get(Lote, lote_id)
                if lote:
                    di = getattr(lote, 'data_inicio', None)
                    df = getattr(lote, 'data_fim', None)
                    if di:
                        data['data_inicio'] = di
                    if df:
                        data['data_fim'] = df
            except Exception:
                pass

        campos_refeicoes = [
            'cafe_interno', 'cafe_funcionario', 'almoco_interno', 'almoco_funcionario',
            'lanche_interno', 'lanche_funcionario', 'jantar_interno', 'jantar_funcionario', 'dados_siisp'
        ]
        for campo in campos_refeicoes:
            vals = data.get(campo)
            if isinstance(vals, list):
                print(f"  {campo}: {vals}")
        if 'datas' in data and isinstance(data['datas'], list):
            print(f"  datas: {data['datas']}")

        res = salvar_mapas_raw(data)
        if res.get('success'):
            registro = res.get('registro') if res.get('registro') is not None else data
            extra_id = res.get('id')
            registros_processados = 0
            dias_esperados = 0
            # Calcular num_dias real do registro recortado
            num_dias = 0
            try:
                datas = data.get('datas')
                if isinstance(datas, list):
                    num_dias = len(datas)
            except Exception:
                pass
            try:
                if isinstance(registro, dict):
                    registros_processados = int(registro.get('linhas') or 0)
                    dias_esperados = int(registro.get('colunas_count') or 0)
            except Exception:
                registros_processados = 0
                dias_esperados = 0


            validacao = {
                'valido': True,
                'refeicoes': {
                    'registros_processados': registros_processados,
                    'dias_esperados': dias_esperados
                },
                'siisp': {
                    'mensagem': 'N/A'
                },
                'mensagem_geral': 'Dados salvos'
            }

            # Calcular estatísticas
            dias_salvos = num_dias
            total_refeicoes = 0
            if isinstance(registro, dict):
                meal_fields = []
                for key in ['cafe_interno', 'cafe_funcionario', 'almoco_interno', 'almoco_funcionario', 'lanche_interno', 'lanche_funcionario', 'jantar_interno', 'jantar_funcionario']:
                    vals = registro.get(key, [])
                    if isinstance(vals, list):
                        meal_fields.extend(vals)
                total_refeicoes = sum(meal_fields)
            
            estatisticas = {
                'registros_processados': dias_salvos,
                'total_refeicoes': total_refeicoes
            }

            operacao = res.get('operacao')
            if not operacao and isinstance(res.get('operacoes'), list) and len(res.get('operacoes')) == 1:
                operacao = res.get('operacoes')[0]

            resp = {'success': True, 'registro': registro, 'validacao': validacao, 'estatisticas': estatisticas}
            if extra_id is not None:
                resp['id'] = extra_id
            if operacao is not None:
                resp['operacao'] = operacao
            return jsonify(resp), 200
        else:
            return jsonify({'success': False, 'error': res.get('error', 'Erro ao salvar')}), 200
    except Exception:
        return jsonify({'success': False, 'error': 'Erro interno'}), 200

@app.route('/api/entrada-manual', methods=['POST'])
def api_entrada_manual():
    # Endpoint para adicionar dados de mapas via entrada manual
    try:
        data = request.get_json(force=True, silent=True) or {}
        
        dados_preparados = preparar_dados_entrada_manual(data)
        if not dados_preparados.get('success'):
            return jsonify({'success': False, 'error': dados_preparados.get('error', 'Erro ao preparar dados')}), 200

        res = salvar_mapas_raw(dados_preparados['data'])

        if res.get('success'):
            registro = res.get('registro') if res.get('registro') is not None else dados_preparados['data']
            extra_id = res.get('id')

            reordenar_registro_mapas(extra_id)

            # Usar 'linhas' que reflete os dados realmente salvos (após filtragem)
            # Se 'linhas' não existir, usar o tamanho do array 'datas'
            dias_salvos = int(registro.get('linhas', 0))
            if dias_salvos == 0 and 'datas' in registro:
                dias_salvos = len(registro.get('datas', []))

            # Mensagem de debug padronizada
            lote_id = data.get('lote_id')
            mes = data.get('mes')
            ano = data.get('ano')
            # Buscar datas de contrato usando funções utilitárias
            from functions.mapas import _get_lote_data_inicio, _get_lote_data_fim
            data_inicio = _get_lote_data_inicio(lote_id) if lote_id else None
            data_fim = _get_lote_data_fim(lote_id) if lote_id else None
            # Formatar datas para exibir apenas YYYY-MM-DD
            data_inicio_str = data_inicio.strftime('%Y-%m-%d') if data_inicio else None
            data_fim_str = data_fim.strftime('%Y-%m-%d') if data_fim else None

            # Calcular total de refeições
            meal_fields = [
                'cafe_interno', 'cafe_funcionario',
                'almoco_interno', 'almoco_funcionario',
                'lanche_interno', 'lanche_funcionario',
                'jantar_interno', 'jantar_funcionario'
            ]
            total_refeicoes = 0
            for field in meal_fields:
                if field in registro and isinstance(registro[field], list):
                    total_refeicoes += sum(int(x) if x is not None else 0 for x in registro[field])

            validacao = {
                'valido': True,
                'refeicoes': {
                    'registros_processados': dias_salvos,
                    'dias_esperados': dias_salvos
                },
                'mensagem_geral': 'Dados salvos via entrada manual'
            }

            estatisticas = {
                'registros_processados': dias_salvos,
                'total_refeicoes': total_refeicoes
            }

            operacao = res.get('operacao')
            if not operacao and isinstance(res.get('operacoes'), list) and len(res.get('operacoes')) == 1:
                operacao = res.get('operacoes')[0]

            resp = {'success': True, 'registro': registro, 'validacao': validacao, 'estatisticas': estatisticas}
            if extra_id is not None:
                resp['id'] = extra_id
            if operacao is not None:
                resp['operacao'] = operacao
            return jsonify(resp), 200
        else:
            return jsonify({'success': False, 'error': res.get('error', 'Erro ao salvar')}), 200
    except Exception:
        return jsonify({'success': False, 'error': 'Erro interno'}), 200

@app.route('/api/adicionar-siisp', methods=['POST'])
def api_adicionar_siisp():
    try:
        data = request.get_json(force=True, silent=True) or {}
        
        res = adicionar_siisp_em_mapa(data)
        
        if res.get('success'):
            registro = res.get('registro', {})
            
            dias_esperados = len(registro.get('dados_siisp', []))
            
            validacao = {
                'valido': True,
                'siisp': {
                    'registros_processados': dias_esperados,
                    'dias_esperados': dias_esperados,
                    'mensagem': res.get('mensagem', 'Dados SIISP adicionados')
                },
                'mensagem_geral': res.get('mensagem', 'Dados SIISP adicionados com sucesso')
            }
            
            resp = {
                'success': True, 
                'registro': registro, 
                'validacao': validacao,
                'id': registro.get('id')
            }
            return jsonify(resp), 200
        else:
            print(f'❌ Erro: {res.get("error")}')
            return jsonify({'success': False, 'error': res.get('error', 'Erro ao adicionar SIISP')}), 200
    except Exception as e:
        print(f'❌ Exception: {str(e)}')
        return jsonify({'success': False, 'error': 'Erro interno'}), 200

@app.route('/api/excluir-dados', methods=['DELETE'])
def api_excluir_dados():
    try:
        data = request.get_json(force=True, silent=True) or {}
        
        res = excluir_mapa(data)
        
        if res.get('success'):
            resp = {
                'success': True,
                'mensagem': res.get('mensagem', 'Mapa excluído com sucesso'),
                'id': res.get('id')
            }
            print(f'✅ Mapa excluído: ID {res.get("id")}')
            return jsonify(resp), 200
        else:
            print(f'❌ Erro: {res.get("error")}')
            return jsonify({'success': False, 'error': res.get('error', 'Erro ao excluir mapa')}), 200
    except Exception as e:
        print(f'❌ Exception: {str(e)}')
        return jsonify({'success': False, 'error': 'Erro interno'}), 200

@app.route('/exportar-tabela')
def exportar_tabela():
    """Rota para exportação de dados em formato Excel"""
    # Receber filtros da query string
    lote_id = request.args.get('lote_id', type=int)
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    unidades = request.args.get('unidades')
    unidades_list = unidades.split(',') if unidades else []

    print(f"📊 Exportação solicitada - Lote: {lote_id}, Unidades: {unidades_list}")

    if lote_id is None:
        print("❌ Erro: lote_id não fornecido")
        return jsonify({'error': 'lote_id é obrigatório'}), 400

    # Chamar função auxiliar para gerar Excel
    resultado = gerar_excel_exportacao(lote_id, unidades_list, data_inicio, data_fim)
    
    if not resultado.get('success'):
        erro = resultado.get('error', 'Erro desconhecido')
        print(f"❌ Erro: {erro}")
        return jsonify({'error': erro}), 500
    
    print(f"✅ Arquivo gerado: {resultado['filename']}")
    
    return send_file(
        resultado['output'],
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=resultado['filename']
    )

@app.route('/exportar-dashboard')
def exportar_dashboard():
    """Rota para exportação de todos os lotes de um mês (dashboard)"""
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    exportar_todos = request.args.get('exportar_todos_lotes', 'false') == 'true'
    lote_id = request.args.get('lote_id', type=int)

    print(f"📊 Exportação Dashboard - Exportar todos: {exportar_todos}, Lote: {lote_id}")

    if not data_inicio or not data_fim:
        print("❌ Erro: data_inicio e data_fim são obrigatórios")
        return jsonify({'error': 'data_inicio e data_fim são obrigatórios'}), 400

    if exportar_todos:
        # Exportar todos os lotes do período
        resultado = gerar_excel_exportacao_multiplos_lotes(data_inicio, data_fim)
    else:
        # Exportar apenas um lote específico
        if lote_id is None:
            print("❌ Erro: lote_id não fornecido")
            return jsonify({'error': 'lote_id é obrigatório quando exportar_todos_lotes=false'}), 400
        resultado = gerar_excel_exportacao(lote_id, [], data_inicio, data_fim)
    
    if not resultado.get('success'):
        erro = resultado.get('error', 'Erro desconhecido')
        print(f"❌ Erro: {erro}")
        
        # Se o erro for por falta de dados, retornar 204 ao invés de 500
        if 'Nenhum' in erro and ('dados' in erro or 'lote' in erro):
            return jsonify({'error': erro, 'no_data': True}), 204
        
        return jsonify({'error': erro}), 500
    
    print(f"✅ Arquivo gerado: {resultado['filename']}")
    
    return send_file(
        resultado['output'],
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=resultado['filename']
    )

@app.route('/dashboard')
def dashboard():
    #Página de dashboard e análises gráficas
    # Forçar recarregamento direto do banco para evitar cache
    from functions.lotes import _load_lotes_data
    lotes_raw = _load_lotes_data()
    
    # Filtrar apenas lotes ATIVOS e adicionar informação de predecessores
    from functions.lotes import Lote
    from functions.unidades import Unidade
    
    lotes = []
    for lote_dict in lotes_raw:
        lote_id = lote_dict.get('id')
        lote_obj = db.session.get(Lote, lote_id)
        
        if lote_obj and lote_obj.ativo:
            # Contar quantos predecessores este lote tem (cadeia histórica)
            num_predecessores = 0
            predecessor_id = lote_obj.lote_predecessor_id
            
            while predecessor_id:
                num_predecessores += 1
                predecessor = db.session.get(Lote, predecessor_id)
                predecessor_id = predecessor.lote_predecessor_id if predecessor else None
            
            # Adicionar indicação de histórico no nome
            lote_dict_modificado = lote_dict.copy()
            if num_predecessores > 0:
                lote_dict_modificado['nome_display'] = f"{lote_dict['nome']} (+ {num_predecessores} período{'s' if num_predecessores > 1 else ''} histórico{'s' if num_predecessores > 1 else ''})"
            else:
                lote_dict_modificado['nome_display'] = lote_dict['nome']
            
            lotes.append(lote_dict_modificado)
    
    # Criar mapeamento de lote_id -> unidades e lista completa de unidades
    lotes_unidades = {}  # {lote_id: [unidade1, unidade2, ...]}
    unidades_set = set()
    
    for lote in lotes:
        lote_id = lote.get('id')
        unidades_ids = lote.get('unidades') or []
        lotes_unidades[lote_id] = []
        
        if unidades_ids:
            # Buscar todas as unidades do lote
            unidades_lote = Unidade.query.filter(
                Unidade.id.in_(unidades_ids),
                Unidade.ativo == True
            ).all()
            
            # Contar subunidades por principal
            subunidades_count = {}
            for u in unidades_lote:
                if u.unidade_principal_id:
                    subunidades_count[u.unidade_principal_id] = subunidades_count.get(u.unidade_principal_id, 0) + 1
            
            # Adicionar apenas unidades principais (não subunidades)
            for unidade in unidades_lote:
                if not unidade.unidade_principal_id:  # Apenas independentes
                    # Contar quantas subunidades esta principal tem
                    num_agregadas = subunidades_count.get(unidade.id, 0)
                    nome_exibicao = f"{unidade.nome} (+ {num_agregadas} agregada{'s' if num_agregadas != 1 else ''})" if num_agregadas > 0 else unidade.nome
                    
                    lotes_unidades[lote_id].append(nome_exibicao)
                    unidades_set.add(nome_exibicao)
    
    unidades = sorted(list(unidades_set))
    
    return render_template('dashboard.html', lotes=lotes, unidades=unidades, lotes_unidades=lotes_unidades)

@app.route('/api/dashboard/grafico-refeicoes', methods=['POST'])
def api_dashboard_grafico_refeicoes():
    """Endpoint para buscar dados do gráfico de refeições"""
    try:
        data = request.get_json(force=True, silent=True) or {}
        
        lotes_ids = data.get('lotes', [])  # Lista de IDs dos lotes selecionados
        unidades_ids = data.get('unidades', [])  # Lista de IDs das unidades selecionadas
        tipo_visualizacao = data.get('tipo', 'normal')  # 'normal' ou 'acumulada'
        tipo_agrupamento = data.get('agrupamento', 'total')  # 'total', 'por-lote' ou 'por-unidade'
        
        print(f"\n{'='*80}")
        print(f"📊 API GRÁFICO REFEIÇÕES")
        print(f"{'='*80}")
        print(f"Lotes recebidos: {lotes_ids}")
        print(f"Unidades recebidas (RAW): {unidades_ids}")
        print(f"Tipo visualização: {tipo_visualizacao}")
        print(f"Tipo agrupamento: {tipo_agrupamento}")
        print(f"{'='*80}\n")
        
        # Validar entrada
        if not lotes_ids or len(lotes_ids) == 0:
            return jsonify({'success': False, 'error': 'Nenhum lote selecionado'}), 400
        
        # Converter IDs para inteiros
        lotes_ids = [int(lid) for lid in lotes_ids if lid]
        unidades_ids = [int(uid) for uid in unidades_ids if uid] if unidades_ids else []
        
        print(f"🔍 Unidades recebidas: {unidades_ids}")
        print(f"🔍 Tipo de agrupamento: {tipo_agrupamento}")
        
        # Buscar mapas dos lotes selecionados + predecessores
        from functions.mapas import carregar_mapas_db
        from functions.lotes import Lote
        from functions.unidades import Unidade
        
        mapas_dados = []
        lotes_info = {}
        
        # Mapear cada lote selecionado para seus predecessores
        lote_para_grupo = {}  # {lote_id_qualquer: lote_principal_id}
        
        # Função recursiva para buscar predecessores
        def buscar_predecessores_recursivo(lote_id, lote_principal_id):
            """Busca recursivamente todos os predecessores de um lote e mapeia para o lote principal"""
            lote = db.session.get(Lote, lote_id)
            if lote:
                lote_para_grupo[lote_id] = lote_principal_id
                
                # Buscar info do lote
                lotes_info[lote_id] = {
                    'id': lote_id,
                    'nome': lote.nome,
                    'empresa': lote.empresa
                }
                
                # Se tem predecessor, continuar recursão
                if lote.lote_predecessor_id and lote.lote_predecessor_id not in lote_para_grupo:
                    print(f"  📦 Lote {lote_id} -> Predecessor: Lote {lote.lote_predecessor_id} (grupo: {lote_principal_id})")
                    buscar_predecessores_recursivo(lote.lote_predecessor_id, lote_principal_id)
        
        # Para cada lote selecionado, buscar seus predecessores
        for lote_id in lotes_ids:
            print(f"📦 Processando Lote {lote_id} e seus predecessores...")
            buscar_predecessores_recursivo(lote_id, lote_id)  # O lote é seu próprio grupo
        
        print(f"📊 Mapeamento lote->grupo: {lote_para_grupo}")
        
        # Buscar mapas de todos os lotes (principais + predecessores)
        for lote_id in lote_para_grupo.keys():
            mapas = carregar_mapas_db({'lote_id': lote_id})
            for mapa in mapas:
                mapa['lote_info'] = lotes_info[lote_id]
                mapa['lote_grupo'] = lote_para_grupo[lote_id]  # Adicionar grupo
                mapas_dados.append(mapa)
        
        if not mapas_dados:
            return jsonify({'success': False, 'error': 'Nenhum dado encontrado para os lotes selecionados'}), 404
        
        # Organizar dados por período (ano-mês)
        # Estrutura depende do tipo de agrupamento
        if tipo_agrupamento == 'por-unidade':
            periodos_dados = {}  # {periodo: {unidade_id: total_refeicoes}}
        else:
            periodos_dados = {}  # {periodo: {lote_grupo_id: total_refeicoes}}
        
        # Criar mapeamento de unidade_id -> nome para o agrupamento por unidade
        unidades_info = {}
        # Criar mapeamento de nome -> id para converter os nomes dos mapas em IDs
        # (Necessário para filtrar por unidades em todos os modos)
        unidade_nome_para_id = {}
        # Criar mapeamento de subunidade -> unidade principal
        subunidade_para_principal = {}
        
        todas_unidades = Unidade.query.all()
        for u in todas_unidades:
            unidade_nome_para_id[u.nome] = u.id
            
            # Se é subunidade, mapear para a unidade principal
            if u.unidade_principal_id:
                subunidade_para_principal[u.id] = u.unidade_principal_id
            
            if tipo_agrupamento == 'por-unidade':
                if not unidades_ids or u.id in unidades_ids:
                    unidades_info[u.id] = {
                        'id': u.id,
                        'nome': u.nome,
                        'lote_id': u.lote_id
                    }
        
        campos_refeicoes = [
            'cafe_interno', 'cafe_funcionario',
            'almoco_interno', 'almoco_funcionario',
            'lanche_interno', 'lanche_funcionario',
            'jantar_interno', 'jantar_funcionario'
        ]
        
        print(f"🔍 Total de mapas a processar: {len(mapas_dados)}")
        mapas_com_unidade = sum(1 for m in mapas_dados if m.get('unidade'))
        unidades_unicas = set(m.get('unidade') for m in mapas_dados if m.get('unidade'))
        print(f"🔍 Mapas com unidade definida: {mapas_com_unidade}")
        print(f"🔍 Nomes de unidades encontrados nos mapas: {sorted(unidades_unicas) if unidades_unicas else 'Nenhum'}")
        if len(mapas_dados) > 0:
            exemplos = mapas_dados[:3]
            for i, ex in enumerate(exemplos, 1):
                print(f"🔍 Exemplo mapa {i}: lote_id={ex.get('lote_id')}, unidade={ex.get('unidade')}, ano={ex.get('ano')}, mes={ex.get('mes')}")
        
        mapas_processados = 0
        mapas_filtrados = 0
        
        for mapa in mapas_dados:
            ano = mapa.get('ano')
            mes = mapa.get('mes')
            lote_grupo = mapa.get('lote_grupo')
            unidade_nome = mapa.get('unidade')
            # Converter nome da unidade para ID (necessário para filtrar por unidades)
            unidade_id = unidade_nome_para_id.get(unidade_nome) if unidade_nome else None
            
            # Se é subunidade, agregar na unidade principal
            if unidade_id and unidade_id in subunidade_para_principal:
                unidade_id = subunidade_para_principal[unidade_id]
            
            if not ano or not mes:
                continue
            
            # Se há unidades selecionadas, filtrar apenas essas unidades (aplica em todos os modos)
            if unidades_ids and unidade_id and unidade_id not in unidades_ids:
                mapas_filtrados += 1
                continue
            
            mapas_processados += 1
            
            periodo = f"{ano}-{mes:02d}"
            
            if periodo not in periodos_dados:
                periodos_dados[periodo] = {}
            
            # Determinar a chave de agrupamento
            if tipo_agrupamento == 'por-unidade':
                if not unidade_id:
                    print(f"⚠️ Mapa sem unidade válida (nome: '{unidade_nome}') - Lote: {mapa.get('lote_id')}, Ano/Mês: {ano}/{mes}")
                    continue
                grupo_key = unidade_id
            else:
                if not lote_grupo:
                    continue
                grupo_key = lote_grupo
            
            if grupo_key not in periodos_dados[periodo]:
                periodos_dados[periodo][grupo_key] = 0
            
            # Calcular total de refeições no mapa
            total_mapa = 0
            for campo in campos_refeicoes:
                valores = mapa.get(campo, [])
                if isinstance(valores, list):
                    total_mapa += sum(int(v) if v is not None else 0 for v in valores)
            
            periodos_dados[periodo][grupo_key] += total_mapa
        
        print(f"🔍 Mapas processados: {mapas_processados}, Mapas filtrados por unidade: {mapas_filtrados}")
        
        # Ordenar períodos
        periodos_ordenados = sorted(periodos_dados.keys())
        
        # Preparar resposta baseada no tipo de agrupamento
        if tipo_agrupamento == 'total':
            # Somar todos os lotes/unidades
            valores = []
            for periodo in periodos_ordenados:
                total_periodo = sum(periodos_dados[periodo].values())
                valores.append(total_periodo)
            
            # Acumular se necessário
            if tipo_visualizacao == 'acumulada':
                valores_acumulados = []
                acumulado = 0
                for v in valores:
                    acumulado += v
                    valores_acumulados.append(acumulado)
                valores = valores_acumulados
            
            resultado = {
                'success': True,
                'labels': periodos_ordenados,
                'datasets': [{
                    'label': 'Total de Refeições',
                    'data': valores
                }],
                'tipo': tipo_visualizacao,
                'agrupamento': tipo_agrupamento
            }
        
        elif tipo_agrupamento == 'por-lote':
            # Separar por lote (cada lote inclui seus predecessores)
            datasets = []
            
            for lote_id in lotes_ids:
                lote_nome = lotes_info.get(lote_id, {}).get('nome', f'Lote {lote_id}')
                valores = []
                
                for periodo in periodos_ordenados:
                    # Buscar dados do grupo (lote + predecessores)
                    valor = periodos_dados[periodo].get(lote_id, 0)
                    valores.append(valor)
                
                # Acumular se necessário
                if tipo_visualizacao == 'acumulada':
                    valores_acumulados = []
                    acumulado = 0
                    for v in valores:
                        acumulado += v
                        valores_acumulados.append(acumulado)
                    valores = valores_acumulados
                
                datasets.append({
                    'label': lote_nome,
                    'data': valores,
                    'lote_id': lote_id
                })
            
            resultado = {
                'success': True,
                'labels': periodos_ordenados,
                'datasets': datasets,
                'tipo': tipo_visualizacao,
                'agrupamento': tipo_agrupamento
            }
        
        else:  # por-unidade
            # Separar por unidade
            datasets = []
            
            print(f"🔍 Modo por-unidade - unidades_ids recebidas: {unidades_ids}")
            print(f"🔍 Períodos dados keys (primeiros 3): {list(periodos_dados.keys())[:3]}")
            if periodos_dados:
                primeiro_periodo = list(periodos_dados.keys())[0]
                print(f"🔍 Exemplo - período {primeiro_periodo}: {periodos_dados[primeiro_periodo]}")
            
            # Verificar se há mapas com unidade válida
            if mapas_com_unidade == 0:
                return jsonify({
                    'success': False, 
                    'error': 'Os mapas deste lote não possuem unidades associadas. Para usar o agrupamento "Por Unidade", os mapas precisam ter a informação de unidade preenchida.'
                }), 400
            
            # Se unidades_ids está vazio, usar todas as unidades que aparecem nos dados
            if not unidades_ids:
                unidades_ids_processadas = set()
                for periodo_data in periodos_dados.values():
                    unidades_ids_processadas.update(periodo_data.keys())
                unidades_ids = sorted(unidades_ids_processadas)
                
                print(f"🔍 Nenhuma unidade selecionada - usando todas: {unidades_ids}")
                
                # Carregar info das unidades
                for uid in unidades_ids:
                    if uid not in unidades_info:
                        unidade = db.session.get(Unidade, uid)
                        if unidade:
                            unidades_info[uid] = {
                                'id': uid,
                                'nome': unidade.nome,
                                'lote_id': unidade.lote_id
                            }
            
            print(f"🔍 Total de unidades a processar: {len(unidades_ids)}")
            
            for unidade_id in unidades_ids:
                unidade_nome = unidades_info.get(unidade_id, {}).get('nome', f'Unidade {unidade_id}')
                valores = []
                
                for periodo in periodos_ordenados:
                    valor = periodos_dados[periodo].get(unidade_id, 0)
                    valores.append(valor)
                
                print(f"🔍 Unidade {unidade_id} ({unidade_nome}): {len(valores)} valores, soma={sum(valores)}")
                
                # Acumular se necessário
                if tipo_visualizacao == 'acumulada':
                    valores_acumulados = []
                    acumulado = 0
                    for v in valores:
                        acumulado += v
                        valores_acumulados.append(acumulado)
                    valores = valores_acumulados
                
                datasets.append({
                    'label': unidade_nome,
                    'data': valores,
                    'unidade_id': unidade_id
                })
            
            resultado = {
                'success': True,
                'labels': periodos_ordenados,
                'datasets': datasets,
                'tipo': tipo_visualizacao,
                'agrupamento': tipo_agrupamento
            }
        
        print(f"✅ Retornando dados: {len(periodos_ordenados)} períodos, {len(resultado['datasets'])} dataset(s)")
        return jsonify(resultado), 200
    
    except Exception as e:
        print(f"❌ Erro na API gráfico refeições: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/dashboard/grafico-gastos', methods=['POST'])
def api_dashboard_grafico_gastos():
    """Endpoint para buscar dados do gráfico de gastos (R$)"""
    try:
        import json
        data = request.get_json(force=True, silent=True) or {}

        lotes_ids = data.get('lotes', [])
        unidades_ids = data.get('unidades', [])
        tipo_visualizacao = data.get('tipo', 'normal')
        tipo_agrupamento = data.get('agrupamento', 'total')

        # Validar entrada
        if not lotes_ids or len(lotes_ids) == 0:
            return jsonify({'success': False, 'error': 'Nenhum lote selecionado'}), 400

        # Converter IDs para inteiros
        lotes_ids = [int(lid) for lid in lotes_ids if lid]
        unidades_ids = [int(uid) for uid in unidades_ids if uid] if unidades_ids else []

        # Buscar mapas dos lotes selecionados + predecessores
        from functions.mapas import carregar_mapas_db
        from functions.lotes import Lote
        from functions.unidades import Unidade

        mapas_dados = []
        lotes_info = {}

        # Mapear cada lote selecionado para seus predecessores
        lote_para_grupo = {}  # {lote_id_qualquer: lote_principal_id}

        def buscar_predecessores_recursivo(lote_id, lote_principal_id):
            lote = db.session.get(Lote, lote_id)
            if not lote:
                return
            lote_para_grupo[lote_id] = lote_principal_id
            # Guardar preços do lote (podem diferir dos predecessores)
            try:
                precos = json.loads(lote.precos) if lote.precos else {}
            except Exception:
                precos = {}
            lotes_info[lote_id] = {
                'id': lote_id,
                'nome': lote.nome,
                'precos': precos
            }

            # Mapas do lote (não do grupo), mas agregaremos no grupo
            mapas = carregar_mapas_db({'lote_id': lote_id})
            for mapa in mapas:
                mapa['lote_grupo'] = lote_principal_id
                mapa['lote_id'] = lote_id  # para pegar o preço correto
                mapas_dados.append(mapa)

            if lote.lote_predecessor_id and lote.lote_predecessor_id not in lote_para_grupo:
                buscar_predecessores_recursivo(lote.lote_predecessor_id, lote_principal_id)

        for lote_id in lotes_ids:
            buscar_predecessores_recursivo(lote_id, lote_id)

        if not mapas_dados:
            return jsonify({'success': False, 'error': 'Nenhum dado encontrado para os lotes selecionados'}), 404

        # Estruturas por período
        if tipo_agrupamento == 'por-unidade':
            periodos_dados = {}  # {periodo: {unidade_id: total_gastos}}
        else:
            periodos_dados = {}  # {periodo: {lote_grupo_id: total_gastos}}

        # Mapear nomes de unidade para IDs e subunidades -> principal
        unidades_info = {}
        unidade_nome_para_id = {}
        subunidade_para_principal = {}
        todas_unidades = Unidade.query.all()
        for u in todas_unidades:
            unidade_nome_para_id[u.nome] = u.id
            if u.unidade_principal_id:
                subunidade_para_principal[u.id] = u.unidade_principal_id
            if tipo_agrupamento == 'por-unidade':
                if not unidades_ids or u.id in unidades_ids:
                    unidades_info[u.id] = {
                        'id': u.id,
                        'nome': u.nome,
                        'lote_id': u.lote_id
                    }

        # Campos de refeições e respectivos preços no lote
        campos_refeicoes = [
            'cafe_interno', 'cafe_funcionario',
            'almoco_interno', 'almoco_funcionario',
            'lanche_interno', 'lanche_funcionario',
            'jantar_interno', 'jantar_funcionario'
        ]

        # Helper para obter preço considerando estrutura de preços aninhada ou chaves planas
        def get_preco(precos, campo):
            try:
                if not isinstance(precos, dict):
                    return 0.0
                # campo ex: 'cafe_interno' -> refeicao='cafe', tipo='interno'
                parts = campo.split('_', 1)
                refeicao = parts[0] if len(parts) > 0 else ''
                tipo = parts[1] if len(parts) > 1 else ''
                valor = 0
                if refeicao and tipo and isinstance(precos.get(refeicao), dict):
                    valor = precos.get(refeicao, {}).get(tipo, 0)
                else:
                    valor = precos.get(campo, 0)
                # Converter para float, aceitando strings com vírgula/ponto
                try:
                    return float(str(valor).replace(',', '.'))
                except (ValueError, TypeError):
                    return 0.0
            except Exception:
                return 0.0

        # Processar mapas
        for mapa in mapas_dados:
            ano = mapa.get('ano')
            mes = mapa.get('mes')
            lote_grupo = mapa.get('lote_grupo')
            lote_id_origem = mapa.get('lote_id')
            unidade_nome = mapa.get('unidade')
            unidade_id = unidade_nome_para_id.get(unidade_nome) if unidade_nome else None
            if unidade_id and unidade_id in subunidade_para_principal:
                unidade_id = subunidade_para_principal[unidade_id]

            if not ano or not mes:
                continue

            # Filtrar por unidades, se houver
            if unidades_ids and unidade_id and unidade_id not in unidades_ids:
                continue

            periodo = f"{ano}-{mes:02d}"
            if periodo not in periodos_dados:
                periodos_dados[periodo] = {}

            # Determinar agrupamento
            if tipo_agrupamento == 'por-unidade':
                if not unidade_id:
                    continue
                grupo_key = unidade_id
            else:
                if not lote_grupo:
                    continue
                grupo_key = lote_grupo

            if grupo_key not in periodos_dados[periodo]:
                periodos_dados[periodo][grupo_key] = 0.0

            # Calcular gasto do mapa usando preços do lote de origem
            precos_lote = lotes_info.get(lote_id_origem, {}).get('precos', {})
            gasto_mapa = 0.0
            for campo in campos_refeicoes:
                valores = mapa.get(campo, [])
                preco = get_preco(precos_lote, campo)
                if isinstance(valores, list) and preco:
                    try:
                        quantidade = sum(int(v) if v is not None else 0 for v in valores)
                    except Exception:
                        quantidade = 0
                    try:
                        gasto_mapa += quantidade * preco
                    except Exception:
                        pass

            periodos_dados[periodo][grupo_key] += gasto_mapa

        # Ordenar períodos
        periodos_ordenados = sorted(periodos_dados.keys())

        # Montar resposta
        if tipo_agrupamento == 'total':
            valores = []
            for periodo in periodos_ordenados:
                total_periodo = sum(periodos_dados[periodo].values())
                valores.append(total_periodo)
            if tipo_visualizacao == 'acumulada':
                acumulado = 0
                valores_acumulados = []
                for v in valores:
                    acumulado += v
                    valores_acumulados.append(acumulado)
                valores = valores_acumulados
            resultado = {
                'success': True,
                'labels': periodos_ordenados,
                'datasets': [{
                    'label': 'Total de Gastos (R$)',
                    'data': valores
                }],
                'tipo': tipo_visualizacao,
                'agrupamento': tipo_agrupamento
            }

        elif tipo_agrupamento == 'por-lote':
            datasets = []
            # Mostrar apenas lotes principais selecionados
            lotes_principais = sorted(set(lote_para_grupo[l] for l in lotes_ids))
            for lote_id in lotes_principais:
                lote_nome = lotes_info.get(lote_id, {}).get('nome', f'Lote {lote_id}')
                valores = []
                for periodo in periodos_ordenados:
                    valores.append(periodos_dados[periodo].get(lote_id, 0))
                if tipo_visualizacao == 'acumulada':
                    acumulado = 0
                    valores_acumulados = []
                    for v in valores:
                        acumulado += v
                        valores_acumulados.append(acumulado)
                    valores = valores_acumulados
                datasets.append({
                    'label': lote_nome,
                    'data': valores,
                    'lote_id': lote_id
                })
            resultado = {
                'success': True,
                'labels': periodos_ordenados,
                'datasets': datasets,
                'tipo': tipo_visualizacao,
                'agrupamento': tipo_agrupamento
            }

        else:  # por-unidade
            datasets = []
            # Se nenhuma unidade foi enviada, derivar das chaves presentes
            if not unidades_ids:
                unidades_ids_processadas = set()
                for periodo_data in periodos_dados.values():
                    unidades_ids_processadas.update(periodo_data.keys())
                unidades_ids = sorted(unidades_ids_processadas)
                for uid in unidades_ids:
                    if uid not in unidades_info:
                        unidade = db.session.get(Unidade, uid)
                        if unidade:
                            unidades_info[uid] = {
                                'id': uid,
                                'nome': unidade.nome,
                                'lote_id': unidade.lote_id
                            }
            for unidade_id in unidades_ids:
                unidade_nome = unidades_info.get(unidade_id, {}).get('nome', f'Unidade {unidade_id}')
                valores = []
                for periodo in periodos_ordenados:
                    valores.append(periodos_dados[periodo].get(unidade_id, 0))
                if tipo_visualizacao == 'acumulada':
                    acumulado = 0
                    valores_acumulados = []
                    for v in valores:
                        acumulado += v
                        valores_acumulados.append(acumulado)
                    valores = valores_acumulados
                datasets.append({
                    'label': unidade_nome,
                    'data': valores,
                    'unidade_id': unidade_id
                })
            resultado = {
                'success': True,
                'labels': periodos_ordenados,
                'datasets': datasets,
                'tipo': tipo_visualizacao,
                'agrupamento': tipo_agrupamento
            }

        return jsonify(resultado), 200

    except Exception as e:
        print(f"❌ Erro na API gráfico gastos: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/lote/<int:lote_id>/unidades', methods=['GET'])
def api_get_unidades_lote(lote_id):
    """Endpoint para buscar unidades de um lote"""
    try:
        from functions.unidades import Unidade
        
        # Buscar unidades do lote (apenas principais, sem subunidades)
        unidades = Unidade.query.filter_by(
            lote_id=lote_id,
            unidade_principal_id=None
        ).order_by(Unidade.nome).all()
        
        unidades_list = []
        for u in unidades:
            # Contar subunidades
            subunidades_count = Unidade.query.filter_by(
                unidade_principal_id=u.id
            ).count()
            
            unidades_list.append({
                'id': u.id,
                'nome': u.nome,
                'lote_id': u.lote_id,
                'subunidades_count': subunidades_count
            })
        
        print(f"✅ Retornando {len(unidades_list)} unidades do lote {lote_id}")
        return jsonify({'success': True, 'unidades': unidades_list}), 200
    
    except Exception as e:
        print(f"❌ Erro ao buscar unidades do lote {lote_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/lote/<int:lote_id>', methods=['GET'])
def api_get_lote(lote_id):
    """Endpoint para buscar dados completos de um lote"""
    try:
        lote = Lote.query.get(lote_id)
        if not lote:
            return jsonify({'success': False, 'error': 'Lote não encontrado'}), 404
        
        lote_data = {
            'id': lote.id,
            'nome': lote.nome,
            'empresa': lote.empresa,
            'sub_empresa': lote.sub_empresa,
            'numero_contrato': lote.numero_contrato,
            'numero': lote.numero,
            'data_inicio': lote.data_inicio,
            'data_fim': lote.data_fim,
            'valor_contratual': lote.valor_contratual,
            'ativo': lote.ativo,
            'status': lote.status,
            'descricao': lote.descricao
        }
        
        print(f"✅ Retornando dados do lote {lote_id}")
        return jsonify(lote_data), 200
    
    except Exception as e:
        print(f"❌ Erro ao buscar lote {lote_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/relatorios/dados-grafico', methods=['POST'])
def api_dados_grafico():
    """Endpoint para buscar dados do gráfico de relatórios"""
    try:
        from functions.relatorios import buscar_dados_graficos, formatar_label_periodo
        
        data = request.get_json(force=True, silent=True) or {}
        
        lotes_ids = data.get('lotes', [])
        unidades = data.get('unidades', [])
        periodo = data.get('periodo', 'mes')
        modo = data.get('modo', 'acumulado')
        incluir_projecao = data.get('projecao', False)
        
        print(f"📊 API Dados Gráfico - Lotes: {lotes_ids}, Unidades: {unidades}, Período: {periodo}, Modo: {modo}, Projeção: {incluir_projecao}")
        
        # Converter lotes_ids para inteiros
        lotes_ids = [int(lid) for lid in lotes_ids if lid]
        
        resultado = buscar_dados_graficos(lotes_ids, unidades, periodo, modo=modo)
        
        print(f"📊 Resultado da busca: success={resultado.get('success')}, registros={resultado.get('total_registros')}")
        
        if resultado.get('success'):
            # Formatar labels
            dados = resultado['dados']
            print(f"📊 Labels encontrados: {len(dados.get('labels', []))}")
            print(f"📊 Grupos encontrados: {len(dados.get('grupos', []))}")
            
            labels_formatados = [formatar_label_periodo(label, periodo) for label in dados['labels']]
            dados['labels_formatados'] = labels_formatados
            dados['modo'] = modo
            
            # Calcular projeção se solicitada
            if incluir_projecao:
                print(f"🔮 Calculando projeção para modo: {modo}")
                from functions.relatorios import calcular_projecao
                projecao = calcular_projecao(dados, periodo)
                
                print(f"🔮 Projeção calculada: {len(projecao.get('labels_projetados', []))} períodos")
                print(f"🔮 Valores projetados: {projecao.get('valores_projetados', [])}")
                
                # Formatar labels de projeção
                labels_projecao_formatados = [formatar_label_periodo(label, periodo) for label in projecao['labels_projetados']]
                
                dados['projecao'] = {
                    'labels': projecao['labels_projetados'],
                    'labels_formatados': labels_projecao_formatados,
                    'valores': projecao['valores_projetados'],
                    'grupos_projetados': projecao.get('grupos_projetados', []),
                    'media_historica': projecao['media_historica'],
                    'tendencia': projecao['tendencia']
                }
                
                print(f"🔮 Projeção adicionada: {len(projecao['labels_projetados'])} períodos, tendência: {projecao['tendencia']}")
            
            print(f"✅ Retornando dados: modo={dados['modo']}, tem_projecao={bool(dados.get('projecao'))}")
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 400
    
    except Exception as e:
        print(f"❌ Erro na API dados gráfico: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/relatorios/dados-gastos', methods=['POST'])
def api_dados_gastos():
    """Endpoint para buscar dados de gastos para gráficos"""
    try:
        from functions.relatorios import buscar_dados_gastos, formatar_label_periodo
        
        data = request.get_json(force=True, silent=True) or {}
        
        lotes_ids = data.get('lotes', [])
        unidades = data.get('unidades', [])
        periodo = data.get('periodo', 'mes')
        modo = data.get('modo', 'acumulado')
        incluir_projecao = data.get('projecao', False)
        
        print(f"💰 API Dados Gastos - Lotes: {lotes_ids}, Unidades: {unidades}, Período: {periodo}, Modo: {modo}")
        
        # Converter lotes_ids para inteiros
        lotes_ids = [int(lid) for lid in lotes_ids if lid]
        
        resultado = buscar_dados_gastos(lotes_ids, unidades, periodo, modo=modo)
        
        print(f"💰 Resultado: success={resultado.get('success')}, registros={resultado.get('total_registros')}")
        
        if resultado.get('success'):
            dados = resultado['dados']
            print(f"💰 Labels encontrados: {len(dados.get('labels', []))}")
            print(f"💰 Grupos encontrados: {len(dados.get('grupos', []))}")
            
            labels_formatados = [formatar_label_periodo(label, periodo) for label in dados['labels']]
            dados['labels_formatados'] = labels_formatados
            dados['modo'] = modo
            
            # Calcular projeção de gastos se solicitada
            if incluir_projecao:
                print(f"🔮 Calculando projeção de gastos para modo: {modo}")
                from functions.relatorios import calcular_projecao
                
                # Criar estrutura de dados compatível com calcular_projecao
                if modo == 'acumulado':
                    # Para modo acumulado, usar total_gastos como base
                    dados_para_projecao = {
                        'labels': dados['labels'],
                        'datasets': {'total_refeicoes': dados['datasets'].get('total_gastos', [])}
                    }
                else:
                    # Para modos separados, usar grupos diretamente
                    dados_para_projecao = dados
                
                projecao = calcular_projecao(dados_para_projecao, periodo)
                
                print(f"🔮 Projeção de gastos calculada: {len(projecao.get('labels_projetados', []))} períodos")
                
                labels_projecao_formatados = [formatar_label_periodo(label, periodo) for label in projecao['labels_projetados']]
                
                dados['projecao'] = {
                    'labels': projecao['labels_projetados'],
                    'labels_formatados': labels_projecao_formatados,
                    'valores': projecao['valores_projetados'],
                    'grupos_projetados': projecao.get('grupos_projetados', []),
                    'media_historica': projecao['media_historica'],
                    'tendencia': projecao['tendencia']
                }
            
            print(f"✅ Retornando gastos: modo={dados['modo']}, tem_projecao={bool(dados.get('projecao'))}")
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 400
    
    except Exception as e:
        print(f"❌ Erro na API dados gastos: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

#NÃO FEITOS

@app.route('/admin/usuarios')
def admin_usuarios():
    return jsonify({'ok': True})


@app.route('/admin/usuarios/<int:user_id>/aprovar', methods=['POST'])
def aprovar_usuario(user_id):
    return jsonify({'ok': True})

@app.route('/admin/usuarios/<int:user_id>/revogar', methods=['POST'])
def revogar_usuario(user_id):
    return jsonify({'ok': True})

@app.route('/api/lotes')
def api_lotes():
    return jsonify({'ok': True})

@app.template_filter('data_br')
def filtro_data_br(data_str):
    try:
        return data_str
    except Exception:
        return data_str


@app.template_filter('status_badge')
def filtro_status_badge(status):
    return 'secondary'


@app.context_processor
def contexto_global():
    # Tornar o contexto global sensível à sessão atual
    usuario_logado = session.get('usuario_logado', False)
    usuario_nome = session.get('usuario_nome', '')
    return {
        'app_nome': 'SGMRP',
        'app_versao': 'stub',
        'ano_atual': datetime.now().year,
        'usuario_logado': usuario_logado,
        'usuario_nome': usuario_nome,
    }


@app.errorhandler(404)
def pagina_nao_encontrada(error):
    return jsonify({'error': 'not found'}), 404


@app.errorhandler(500)
def erro_interno(error):
    return jsonify({'error': 'internal error'}), 500


if __name__ == '__main__':
    print("🚀 Iniciando SGMRP - Sistema de Gerenciamento de Mapas de Refeições Penitenciário")
    print(f"📁 Diretório base: {BASE_DIR}")
    print(f"💾 Dados JSON: {DADOS_DIR}")
    print("🔗 Acesse: http://localhost:5000")
    print("-" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=True)