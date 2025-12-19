def to_int_list(unidades):
	result = []
	for u in unidades:
		try:
			result.append(int(u))
		except Exception:
			continue
	return result
# Função para carregar lotes do banco de dados (substitui o antigo carregamento do JSON)
def _load_lotes_data():
	"""Retorna todos os lotes cadastrados no banco de dados."""
	lotes = Lote.query.all()
	return [lote_to_dict(l) for l in lotes]
# Função para calcular a última atividade dos lotes
def calcular_ultima_atividade_lotes(lotes, mapas=None):
	"""Retorna a data da última atividade dos lotes ou mapas."""
	datas = []
	if lotes:
		datas += [lote.get('data_criacao') for lote in lotes if 'data_criacao' in lote and lote.get('data_criacao')]
	if mapas:
		datas += [mapa.get('atualizado_em') for mapa in mapas if 'atualizado_em' in mapa and mapa.get('atualizado_em')]
	datas = [d for d in datas if d]
	return max(datas) if datas else None

from .models import Lote, Unidade, db
from datetime import datetime
from .unidades import criar_unidade

import json

def copiar_unidades_de_predecessor(lote_predecessor_id, novo_lote_id):
	"""
	Copia todas as unidades (incluindo subunidades) do lote predecessor para o novo lote.
	Recalcula valor_contratual_unidade usando os NOVOS preços do lote destino.
	Retorna a lista de IDs das novas unidades criadas.
	"""
	# Buscar o novo lote para pegar os preços atualizados
	novo_lote = Lote.query.get(novo_lote_id)
	if not novo_lote:
		print(f"Erro: Novo lote {novo_lote_id} não encontrado")
		return []
	
	# Parse dos preços do novo lote
	try:
		novos_precos = json.loads(novo_lote.precos) if isinstance(novo_lote.precos, str) else novo_lote.precos
	except Exception:
		novos_precos = {}
	
	# Buscar unidades principais do predecessor (sem unidade_principal_id)
	unidades_predecessor = Unidade.query.filter_by(
		lote_id=lote_predecessor_id, 
		unidade_principal_id=None
	).all()
	
	novos_ids = []
	mapeamento_ids = {}  # predecessor_id -> novo_id
	
	# Primeiro, copiar unidades principais
	for unidade in unidades_predecessor:
		# Recalcular valor_contratual_unidade com os NOVOS preços
		quantitativos_unidade = unidade.quantitativos_unidade
		try:
			qtds = json.loads(quantitativos_unidade) if isinstance(quantitativos_unidade, str) else quantitativos_unidade
		except Exception:
			qtds = {}
		
		novo_valor_contratual = 0.0
		if qtds and novos_precos:
			for refeicao, tipos in qtds.items():
				if isinstance(tipos, dict) and refeicao in novos_precos:
					for tipo, qtd in tipos.items():
						if tipo in novos_precos[refeicao]:
							preco = float(novos_precos[refeicao][tipo] or 0)
							novo_valor_contratual += preco * int(qtd or 0)
		
		nova_unidade = Unidade(
			nome=unidade.nome,
			lote_id=novo_lote_id,
			unidade_principal_id=None,
			quantitativos_unidade=unidade.quantitativos_unidade,
			valor_contratual_unidade=novo_valor_contratual,  # NOVO VALOR CALCULADO
			criado_em=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
			ativo=unidade.ativo
		)
		db.session.add(nova_unidade)
		db.session.flush()  # Para obter o ID
		
		novos_ids.append(nova_unidade.id)
		mapeamento_ids[unidade.id] = nova_unidade.id
	
	# Depois, copiar subunidades e vincular às novas principais
	subunidades_predecessor = Unidade.query.filter(
		Unidade.lote_id == lote_predecessor_id,
		Unidade.unidade_principal_id.isnot(None)
	).all()
	
	for subunidade in subunidades_predecessor:
		# Buscar o novo ID da unidade principal correspondente
		nova_principal_id = mapeamento_ids.get(subunidade.unidade_principal_id)
		if nova_principal_id:
			# Recalcular valor_contratual_unidade com os NOVOS preços
			quantitativos_unidade = subunidade.quantitativos_unidade
			try:
				qtds = json.loads(quantitativos_unidade) if isinstance(quantitativos_unidade, str) else quantitativos_unidade
			except Exception:
				qtds = {}
			
			novo_valor_contratual = 0.0
			if qtds and novos_precos:
				for refeicao, tipos in qtds.items():
					if isinstance(tipos, dict) and refeicao in novos_precos:
						for tipo, qtd in tipos.items():
							if tipo in novos_precos[refeicao]:
								preco = float(novos_precos[refeicao][tipo] or 0)
								novo_valor_contratual += preco * int(qtd or 0)
			
			nova_subunidade = Unidade(
				nome=subunidade.nome,
				lote_id=novo_lote_id,
				unidade_principal_id=nova_principal_id,
				quantitativos_unidade=subunidade.quantitativos_unidade,
				valor_contratual_unidade=novo_valor_contratual,  # NOVO VALOR CALCULADO
				criado_em=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
				ativo=subunidade.ativo
			)
			db.session.add(nova_subunidade)
			db.session.flush()  # Para obter o ID
			novos_ids.append(nova_subunidade.id)  # Adicionar ID da subunidade à lista
	
	db.session.commit()
	print(f"✅ Copiadas {len(unidades_predecessor)} unidades principais e {len(subunidades_predecessor)} subunidades do predecessor")
	print(f"✅ Valores contratuais recalculados com os novos preços do lote {novo_lote_id}")
	print(f"✅ Total de IDs retornados: {len(novos_ids)}")
	
	return novos_ids

def lote_to_dict(lote):
	# Garantir que quantitativos seja carregado mesmo se houver problema de cache do SQLAlchemy
	quantitativos_value = None
	try:
		quantitativos_value = lote.quantitativos
	except AttributeError:
		# Se o atributo não existe no modelo (cache antigo), buscar diretamente do banco
		import sqlite3
		import os
		BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
		DADOS_DIR = os.path.join(BASE_DIR, 'dados')
		db_path = os.path.join(DADOS_DIR, 'dados.db')
		conn = sqlite3.connect(db_path)
		cursor = conn.cursor()
		cursor.execute("SELECT quantitativos FROM lotes WHERE id = ?", (lote.id,))
		result = cursor.fetchone()
		conn.close()
		if result:
			quantitativos_value = result[0]
	
	# Debug: verificar predecessor_id
	predecessor_id_value = lote.lote_predecessor_id if hasattr(lote, 'lote_predecessor_id') else None
	if predecessor_id_value:
		print(f"[DEBUG lote_to_dict] Lote {lote.id}: lote_predecessor_id = {predecessor_id_value}")
	
	return {
		'id': lote.id,
		'nome': lote.nome,
		'empresa': lote.empresa,
		'numero_contrato': lote.numero_contrato,
		'numero': lote.numero,
		'data_inicio': lote.data_inicio,
		'data_fim': lote.data_fim,
		'valor_contratual': lote.valor_contratual,
		'unidades': json.loads(lote.unidades) if lote.unidades else [],
		'precos': json.loads(lote.precos) if lote.precos else {},
		'quantitativos': json.loads(quantitativos_value) if quantitativos_value else {},
		'ativo': lote.ativo,
		'criado_em': lote.criado_em,
		'data_criacao': lote.data_criacao,
		'data_contrato': lote.data_contrato,
		'status': lote.status,
		'descricao': lote.descricao,
		'lote_predecessor_id': predecessor_id_value,
	}

def listar_lotes():
	lotes = Lote.query.all()
	return [lote_to_dict(l) for l in lotes]

def deletar_lote(lote_id, db):
	"""
	Deleta um lote pelo ID e todos os dados associados (mapas e unidades).
	IMPORTANTE: Lotes predecessores NÃO são apagados (apenas o vínculo é removido).
	"""
	from .models import Mapa, Unidade
	
	lote = db.session.query(Lote).filter_by(id=lote_id).first()
	if not lote:
		return False
	
	try:
		# 0. Se este lote tem um predecessor, preservá-lo (apenas limpar vínculo em outros lotes que apontam para este)
		# Buscar lotes que tem este lote como predecessor
		lotes_sucessores = db.session.query(Lote).filter_by(lote_predecessor_id=lote_id).all()
		if lotes_sucessores:
			print(f"⚠️ Lote {lote_id} é predecessor de {len(lotes_sucessores)} lote(s). Removendo vínculos...")
			for sucessor in lotes_sucessores:
				sucessor.lote_predecessor_id = None
		
		# 1. Excluir todos os mapas associados ao lote
		mapas_deletados = db.session.query(Mapa).filter_by(lote_id=lote_id).delete()
		print(f"🗑️ Excluídos {mapas_deletados} mapas do lote {lote_id}")
		
		# 2. Excluir todas as unidades associadas ao lote (incluindo subunidades)
		unidades_deletadas = db.session.query(Unidade).filter_by(lote_id=lote_id).delete()
		print(f"🗑️ Excluídas {unidades_deletadas} unidades do lote {lote_id}")
		
		# 3. Excluir o lote (predecessor fica intacto)
		db.session.delete(lote)
		
		# 4. Commit de todas as alterações
		db.session.commit()
		
		print(f"✅ Lote {lote_id} e seus dados associados foram excluídos com sucesso")
		if lote.lote_predecessor_id:
			print(f"ℹ️ Lote predecessor (ID {lote.lote_predecessor_id}) foi preservado")
		return True
		
	except Exception as e:
		db.session.rollback()
		print(f"❌ Erro ao excluir lote {lote_id}: {e}")
		return False

def obter_lote_por_id(lote_id):
	try:
		lote_id = int(lote_id)
	except Exception:
		return None
	lote = Lote.query.get(lote_id)
	if lote:
		return lote_to_dict(lote)
	return None


def salvar_novo_lote(payload: dict):
    if not isinstance(payload, dict):
        return {'success': False, 'error': 'Payload inválido'}

    nome = payload.get('nome_lote') or payload.get('nome') or payload.get('nomeLote') or ''
    empresa = payload.get('empresa') or payload.get('nome_empresa', '')
    numero_contrato = payload.get('numero_contrato') or payload.get('contrato') or ''
    numero = payload.get('numero') or numero_contrato or ''
    data_inicio = payload.get('data_inicio', '')
    data_fim = payload.get('data_fim', '')
    # Normalizar data_fim para YYYY-MM-DD
    if data_fim:
        import re
        match = re.match(r'(\d{2})/(\d{2})/(\d{4})', data_fim)
        if match:
            data_fim = f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
        else:
            match_iso = re.match(r'(\d{4})[-/](\d{2})[-/](\d{2})', data_fim)
            if match_iso:
                data_fim = f"{match_iso.group(1)}-{match_iso.group(2)}-{match_iso.group(3)}"
    unidades_nomes = payload.get('unidades', [])
    precos = payload.get('precos', {})
    quantitativos = payload.get('quantitativos', {})
    
    # Calcular valor_contratual baseado em preços × quantitativos
    valor_contratual = 0.0
    for refeicao, tipos in precos.items():
        if isinstance(tipos, dict):
            for tipo, preco in tipos.items():
                qtd = quantitativos.get(refeicao, {}).get(tipo, 0) if isinstance(quantitativos.get(refeicao), dict) else 0
                valor_contratual += float(preco or 0) * int(qtd or 0)
    
    ativo = payload.get('ativo', True)
    if isinstance(ativo, str):
        ativo = ativo.lower() in ['true', '1', 'sim', 'ativo']
    criado_em = payload.get('criado_em') or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data_criacao = payload.get('data_criacao') or criado_em
    data_contrato = payload.get('data_contrato', '')
    status = payload.get('status', 'ativo')
    descricao = payload.get('descricao', '')

    if not nome or not numero:
        return {'success': False, 'error': 'Campos obrigatórios faltando'}

    if Lote.query.filter_by(nome=nome).first():
        return {'success': False, 'error': f'Já existe um lote com o nome "{nome}". Escolha um nome diferente.'}

    # Validar predecessor se fornecido
    lote_predecessor_id = payload.get('lote_predecessor_id')
    if lote_predecessor_id:
        try:
            lote_predecessor_id = int(lote_predecessor_id) if lote_predecessor_id else None
            
            if lote_predecessor_id:
                predecessor = Lote.query.get(lote_predecessor_id)
                if not predecessor:
                    return {'success': False, 'error': 'Lote predecessor não encontrado'}
                
                if predecessor.ativo:
                    return {'success': False, 'error': 'Lote predecessor deve estar INATIVO'}
                
                # Verificar se predecessor já tem sucessor
                sucessor_existente = Lote.query.filter_by(lote_predecessor_id=lote_predecessor_id).first()
                if sucessor_existente:
                    return {'success': False, 'error': f'Lote predecessor já tem um sucessor: "{sucessor_existente.nome}"'}
        except ValueError:
            lote_predecessor_id = None

    novo_lote = Lote(
        nome=nome,
        empresa=empresa,
        numero_contrato=numero_contrato,
        numero=numero,
        data_inicio=data_inicio,
        data_fim=data_fim,
        valor_contratual=valor_contratual,
        unidades="[]",  # será atualizado após criar as unidades
        precos=json.dumps(precos),
        quantitativos=json.dumps(quantitativos),
        ativo=ativo,
        criado_em=criado_em,
        data_criacao=data_criacao,
        data_contrato=data_contrato,
        status=status,
        descricao=descricao,
        lote_predecessor_id=lote_predecessor_id
    )
    db.session.add(novo_lote)
    db.session.commit()

    # Criar unidades e associar ao lote
    unidade_ids = []
    
    # Se tem predecessor, copiar unidades dele automaticamente
    if lote_predecessor_id:
        print(f"Copiando unidades do predecessor {lote_predecessor_id} para o novo lote {novo_lote.id}")
        unidade_ids = copiar_unidades_de_predecessor(lote_predecessor_id, novo_lote.id)
    else:
        # Criar unidades manualmente fornecidas
        for nome_unidade in unidades_nomes:
            res = criar_unidade(nome_unidade, lote_id=novo_lote.id)
            if res.get('success'):
                unidade_ids.append(res['id'])
    
    # Atualizar campo unidades do lote
    novo_lote.unidades = json.dumps(unidade_ids)
    db.session.commit()
    return {'success': True, 'id': novo_lote.id}



def editar_lote(lote_id, payload: dict):
	if not isinstance(payload, dict):
		return {'success': False, 'error': 'Payload inválido'}
	try:
		lote_id = int(lote_id)
	except Exception as e:
		print(f'[ERRO editar_lote] ID inválido: {e}')
		return {'success': False, 'error': 'ID de lote inválido'}
	lote = Lote.query.get(lote_id)
	if not lote:
		return {'success': False, 'error': f'Lote {lote_id} não encontrado'}

	# Verificar se o nome está sendo alterado e se já existe outro lote com esse nome
	novo_nome = payload.get('nome')
	if novo_nome and novo_nome != lote.nome:
		lote_existente = Lote.query.filter_by(nome=novo_nome).first()
		if lote_existente:
			return {'success': False, 'error': f'Já existe um lote com o nome "{novo_nome}". Escolha um nome diferente.'}

	# Verificar se está tentando ativar um lote que é predecessor de outro
	if 'ativo' in payload:
		novo_status_ativo = payload.get('ativo')
		if isinstance(novo_status_ativo, str):
			novo_status_ativo = novo_status_ativo.lower() in ['true', '1', 'sim', 'ativo']
		
		# Se está tentando ativar um lote que está inativo
		if novo_status_ativo and not lote.ativo:
			# Verificar se este lote é predecessor de algum outro
			sucessor = Lote.query.filter_by(lote_predecessor_id=lote_id).first()
			if sucessor:
				return {
					'success': False, 
					'error': f'Este lote não pode ser ativado pois é predecessor do lote "{sucessor.nome}". Para reativá-lo, edite o lote sucessor e remova o vínculo de predecessor.'
				}

	# Validar predecessor se fornecido
	if 'lote_predecessor_id' in payload:
		lote_predecessor_id = payload.get('lote_predecessor_id')
		
		try:
			lote_predecessor_id = int(lote_predecessor_id) if lote_predecessor_id else None
			
			if lote_predecessor_id:
				# Não permitir self-reference
				if lote_predecessor_id == lote_id:
					return {'success': False, 'error': 'Um lote não pode ser predecessor de si mesmo'}
				
				predecessor = Lote.query.get(lote_predecessor_id)
				if not predecessor:
					return {'success': False, 'error': 'Lote predecessor não encontrado'}
				
				if predecessor.ativo:
					return {'success': False, 'error': 'Lote predecessor deve estar INATIVO'}
				
				# Verificar se predecessor já tem outro sucessor
				sucessor_existente = Lote.query.filter(
					Lote.lote_predecessor_id == lote_predecessor_id,
					Lote.id != lote_id
				).first()
				if sucessor_existente:
					return {'success': False, 'error': f'Lote predecessor já tem um sucessor: "{sucessor_existente.nome}"'}
		except ValueError:
			lote_predecessor_id = None
		
		payload['lote_predecessor_id'] = lote_predecessor_id
		
		# Se o predecessor foi alterado e agora tem um predecessor válido, copiar unidades
		predecessor_atual = lote.lote_predecessor_id
		if lote_predecessor_id and lote_predecessor_id != predecessor_atual:
			print(f"Predecessor alterado para {lote_predecessor_id}. Copiando unidades...")
			
			# Remover unidades antigas do lote (mas não deletar do banco, só desvincular)
			# Na verdade, vamos deletar as antigas e criar novas baseadas no predecessor
			unidades_antigas = Unidade.query.filter_by(lote_id=lote_id).all()
			for unidade in unidades_antigas:
				db.session.delete(unidade)
			db.session.commit()
			
			# Copiar unidades do novo predecessor
			unidade_ids = copiar_unidades_de_predecessor(lote_predecessor_id, lote_id)
			payload['unidades'] = json.dumps(unidade_ids)

	try:
		# Calcular valor_contratual se precos ou quantitativos forem atualizados
		if 'precos' in payload or 'quantitativos' in payload:
			precos = payload.get('precos', json.loads(lote.precos) if lote.precos else {})
			quantitativos = payload.get('quantitativos', json.loads(lote.quantitativos) if lote.quantitativos else {})
			
			valor_contratual = 0.0
			for refeicao, tipos in precos.items():
				if isinstance(tipos, dict):
					for tipo, preco in tipos.items():
						qtd = quantitativos.get(refeicao, {}).get(tipo, 0) if isinstance(quantitativos.get(refeicao), dict) else 0
						valor_contratual += float(preco or 0) * int(qtd or 0)
			
			payload['valor_contratual'] = valor_contratual
		
		for campo in [
			'nome', 'empresa', 'numero_contrato', 'numero', 'data_inicio', 'data_fim',
			'valor_contratual', 'unidades', 'precos', 'quantitativos', 'ativo', 'criado_em',
			'data_criacao', 'data_contrato', 'status', 'descricao', 'lote_predecessor_id'
		]:
			if campo in payload:
				valor = payload[campo]
				if campo == 'data_fim' and valor:
					import re
					match = re.match(r'(\d{2})/(\d{2})/(\d{4})', valor)
					if match:
						valor = f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
					else:
						match_iso = re.match(r'(\d{4})[-/](\d{2})[-/](\d{2})', valor)
						if match_iso:
							valor = f"{match_iso.group(1)}-{match_iso.group(2)}-{match_iso.group(3)}"
				if campo == 'ativo':
					if isinstance(valor, str):
						valor = valor.lower() in ['true', '1', 'sim', 'ativo']
				if campo == 'unidades':
					# Se vier nomes, gera novos IDs únicos (não repete)
					if valor and isinstance(valor[0], str):
						max_id = 0
						try:
							todos_lotes = Lote.query.all()
							for l in todos_lotes:
								ids = json.loads(l.unidades) if l.unidades else []
								if ids:
									max_id = max(max_id, max(ids))
						except Exception:
							pass
						valor = list(range(max_id + 1, max_id + 1 + len(valor)))
					else:
						valor = to_int_list(valor)
					valor = json.dumps(valor)
				elif campo == 'precos':
					valor = json.dumps(valor)
				elif campo == 'quantitativos':
					valor = json.dumps(valor)
				setattr(lote, campo, valor)
		db.session.commit()
		return {'success': True, 'lote': lote_to_dict(lote)}
	except Exception as e:
		print(f'[ERRO editar_lote] {e}')
		return {'success': False, 'error': f'Erro interno: {e}'}


# Função placeholder para normalizar preços dos lotes
def normalizar_precos(dados):
	"""Normaliza os preços dos lotes. Implemente a lógica conforme necessário."""
	return dados


