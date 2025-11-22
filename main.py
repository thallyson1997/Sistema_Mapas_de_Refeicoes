from flask import Flask, request, jsonify, render_template, session, flash, redirect, url_for, abort, send_file
import os
import json
import re
import io
import calendar
from datetime import datetime
from copy import copy
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
    calcular_ultima_atividade_lotes
)

app = Flask(__name__)
app.secret_key = 'sgmrp_seap_2025_secret_key_desenvolvimento'
app.config['DEBUG'] = True

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.join(BASE_DIR, 'dados')

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
            return redirect(url_for('dashboard', login='1'))
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

@app.route('/dashboard')
def dashboard():
    #Página do dashboard
    mostrar_login_sucesso = request.args.get('login') == '1'
    usuario_nome = session.get('usuario_nome', '')
    dashboard_data = carregar_lotes_para_dashboard()
    lotes = dashboard_data.get('lotes', [])
    mapas_dados = dashboard_data.get('mapas_dados', [])

    return render_template('dashboard.html', lotes=lotes, mapas_dados=mapas_dados,
                           mostrar_login_sucesso=mostrar_login_sucesso,
                           usuario_nome=usuario_nome)

@app.route('/lotes')
def lotes():
    #Página de listagem de lotes
    data = carregar_lotes_para_dashboard()
    lotes = data.get('lotes', [])
    mapas = data.get('mapas_dados', [])

    calcular_metricas_lotes(lotes, mapas)
    calcular_ultima_atividade_lotes(lotes, mapas)

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
    data = carregar_lotes_para_dashboard()
    lotes = data.get('lotes', [])
    mapas_dados = data.get('mapas_dados', [])

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

    lote['precos'] = normalizar_precos(lote.get('precos'))

    unidades_lote = lote.get('unidades') or []

    mapas_lote = []
    for m in (mapas_dados or []):
        try:
            if int(m.get('lote_id')) == int(lote.get('id')):
                mapas_lote.append(m)
        except Exception:
            continue

    return render_template('lote-detalhes.html', lote=lote, unidades_lote=unidades_lote, mapas_lote=mapas_lote)

@app.route('/api/adicionar-dados', methods=['POST'])
def api_adicionar_dados():
    # Endpoint para adicionar dados de mapas via API
    try:
        data = request.get_json(force=True, silent=True)
        res = salvar_mapas_raw(data)
        if res.get('success'):
            registro = res.get('registro') if res.get('registro') is not None else data
            extra_id = res.get('id')
            registros_processados = 0
            dias_esperados = 0
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
            dias_salvos = registros_processados
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
            
            print(f"🔍 DEBUG entrada-manual: linhas={registro.get('linhas')}, len(datas)={len(registro.get('datas', []))}, dias_salvos={dias_salvos}")
            
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
        
        print('🔍 DEBUG adicionar-siisp - Payload recebido:')
        print(f'  - unidade: {data.get("unidade")}')
        print(f'  - mes: {data.get("mes")}')
        print(f'  - ano: {data.get("ano")}')
        print(f'  - lote_id: {data.get("lote_id")}')
        print(f'  - dados_siisp tipo: {type(data.get("dados_siisp"))}')
        print(f'  - dados_siisp: {data.get("dados_siisp")}')
        
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
        
        print('🔍 DEBUG excluir-dados - Payload recebido:')
        print(f'  - unidade: {data.get("unidade")}')
        print(f'  - mes: {data.get("mes")}')
        print(f'  - ano: {data.get("ano")}')
        print(f'  - lote_id: {data.get("lote_id")}')
        
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