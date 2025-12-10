def _check_password(stored_hash, password):
	"""Verifica se o hash da senha informada corresponde ao hash salvo."""
	if not isinstance(password, str):
		password = str(password)
	return stored_hash == hashlib.sha256(password.encode('utf-8')).hexdigest()
import hashlib

def _hash_password(password):
	"""Retorna o hash SHA256 da senha como string hexadecimal."""
	if not isinstance(password, str):
		password = str(password)
	return hashlib.sha256(password.encode('utf-8')).hexdigest()
def _first_present(d, *keys):
	"""Retorna o primeiro valor presente e não vazio entre as chaves fornecidas."""
	for k in keys:
		v = d.get(k)
		if v not in (None, '', [], {}):
			return v
	return None

from .models import db, Usuario
from datetime import datetime
import json
import re

# ----- Main Functions -----
def cadastrar_novo_usuario(form_data=None):
	r = validar_cadastro_no_usuario(form_data)
	if not r.get('valido'):
		return {'ok': False, 'mensagem': r.get('mensagem', 'Validação falhou'), 'campo': r.get('campo')}

	try:
		# Calcula novo id
		last_user = Usuario.query.order_by(Usuario.id.desc()).first()
		new_id = (last_user.id + 1) if last_user else 1

		registro = Usuario(
			id=new_id,
			data_criacao=datetime.now().isoformat(),
			cpf=re.sub(r'\D', '', str(form_data.get('cpf') or '')),
			email=str(form_data.get('email') or '').strip(),
			telefone=re.sub(r'\D', '', str(form_data.get('telefone') or '')),
			usuario=str(form_data.get('usuario') or '').strip(),
			nome=str(form_data.get('nome') or form_data.get('nome_completo') or '').strip(),
			cargo=str(form_data.get('cargo') or '').strip(),
			unidade=str(form_data.get('unidade') or '').strip(),
			motivo=str(_first_present(form_data, 'motivo', 'motivo_solicitacao', 'justificativa', 'justificativa_acesso') or '').strip(),
			concordo=False,
			ativo=False,
			senha=_hash_password(form_data.get('senha') or '')
		)

		_concordo_raw = _first_present(
			form_data,
			'concordo',
			'concordo_termos',
			'aceito',
			'aceito_termos',
			'aceitarTermos',
			'aceitar_termos'
		)
		if _concordo_raw is not None:
			v = str(_concordo_raw).strip().lower()
			if v in ('1', 'true', 'on', 'yes', 'sim', 'y'):
				registro.concordo = True

		db.session.add(registro)
		db.session.commit()
		return {'ok': True, 'mensagem': 'Usuário cadastrado com sucesso. Aguarde a aprovação do seu cadastro.', 'id': new_id}
	except Exception as e:
		try:
			print('Erro ao salvar usuário:', e)
		except Exception:
			pass
		db.session.rollback()
		return {'ok': False, 'mensagem': 'Erro ao salvar usuário'}

def validar_login(login_value, senha):
	if not login_value:
		return {'ok': False, 'mensagem': 'Informe usuário ou e-mail'}

	is_email = ('@' in str(login_value))
	query = Usuario.query.filter_by(ativo=True)
	if is_email:
		user = query.filter(db.func.lower(Usuario.email) == str(login_value).lower()).first()
	else:
		user = query.filter(db.func.lower(Usuario.usuario) == str(login_value).lower()).first()
	if not user:
		return {'ok': False, 'mensagem': 'E-mail não cadastrado' if is_email else 'Usuário não cadastrado'}

	stored = user.senha
	if not _check_password(stored, senha):
		return {'ok': False, 'mensagem': 'Senha incorreta'}


	sanitized = {k: v for k, v in user.__dict__.items() if k != 'senha' and not k.startswith('_')}
	return {'ok': True, 'mensagem': 'Login efetuado com sucesso', 'user': sanitized}

# ----- Validation Functions -----
def validar_cpf(cpf):
	if not cpf:
		return {'valido': False, 'mensagem': 'CPF inválido'}
	num = re.sub(r'\D', '', str(cpf))

	if len(num) != 11:
		return {'valido': False, 'mensagem': 'CPF inválido'}
	if re.match(r'^(\d)\1{10}$', num):
		return {'valido': False, 'mensagem': 'CPF inválido'}

	s = 0
	for i in range(9):
		s += int(num[i]) * (10 - i)
	d1 = 11 - (s % 11)
	if d1 >= 10:
		d1 = 0
	if d1 != int(num[9]):
		return {'valido': False, 'mensagem': 'CPF inválido'}

	s = 0
	for i in range(10):
		s += int(num[i]) * (11 - i)
	d2 = 11 - (s % 11)
	if d2 >= 10:
		d2 = 0
	if d2 != int(num[10]):
		return {'valido': False, 'mensagem': 'CPF inválido'}

	# Checagem no banco
	from .models import Usuario
	exists = Usuario.query.filter_by(cpf=num, ativo=True).first()
	if exists:
		return {'valido': False, 'mensagem': 'CPF já cadastrado'}

	return {'valido': True, 'mensagem': 'OK'}


def validar_email(email):
	if not email:
		return {'valido': False, 'mensagem': 'Email inválido'}
	email = email.strip()
	email_regex = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
	if not email_regex.match(email):
		return {'valido': False, 'mensagem': 'Email inválido'}
	try:
		from .models import db, Usuario
		email_norm = email.strip().lower()
		exists = Usuario.query.filter(db.func.lower(db.func.trim(Usuario.email)) == email_norm, Usuario.ativo == True).first()
		if exists:
			return {'valido': False, 'mensagem': 'Email já cadastrado'}
		return {'valido': True, 'mensagem': 'OK'}
	except Exception as e:
		return {'valido': False, 'mensagem': f'Erro interno: {str(e)}'}


def validar_telefone(telefone):
	if not telefone:
		return {'valido': False, 'mensagem': 'Telefone inválido'}
	num = re.sub(r'\D', '', str(telefone))
	if len(num) < 10 or len(num) > 11:
		return {'valido': False, 'mensagem': 'Telefone inválido'}
	if re.match(r'^(\d)\1{9,10}$', num):
		return {'valido': False, 'mensagem': 'Telefone inválido'}
	from .models import Usuario
	exists = Usuario.query.filter_by(telefone=num, ativo=True).first()
	if exists:
		return {'valido': False, 'mensagem': 'Telefone já cadastrado'}
	return {'valido': True, 'mensagem': 'OK'}


def validar_matricula(matricula):
	if not matricula:
		return {'valido': False, 'mensagem': 'Matrícula inválida'}
	mat = str(matricula).strip()
	from .models import Usuario
	exists = Usuario.query.filter_by(matricula=mat, ativo=True).first()
	if exists:
		return {'valido': False, 'mensagem': 'Matrícula já cadastrada'}
	return {'valido': True, 'mensagem': 'OK'}


def validar_username(username):
	if not username:
		return {'valido': False, 'mensagem': 'Nome de usuário inválido'}
	user = str(username).strip()
	try:
		from .models import db, Usuario
		user_norm = user.strip().lower()
		exists = Usuario.query.filter(db.func.lower(db.func.trim(Usuario.usuario)) == user_norm, Usuario.ativo == True).first()
		if exists:
			return {'valido': False, 'mensagem': 'Nome de usuário já existe'}
		return {'valido': True, 'mensagem': 'OK'}
	except Exception as e:
		return {'valido': False, 'mensagem': f'Erro interno: {str(e)}'}


def validar_senha(senha, confirmar):
	if senha is None or confirmar is None:
		return {'valido': False, 'mensagem': 'Senha inválida'}
	if str(senha) != str(confirmar):
		return {'valido': False, 'mensagem': 'Senhas não coincidem'}
	return {'valido': True, 'mensagem': 'OK'}


def validar_cadastro_no_usuario(form_data):
	if not isinstance(form_data, dict):
		return {'valido': False, 'mensagem': 'Dados do formulário inválidos'}

	cpf = form_data.get('cpf')
	email = form_data.get('email')
	telefone = form_data.get('telefone')
	matricula = form_data.get('matricula')
	usuario = form_data.get('usuario')
	senha = form_data.get('senha')
	confirmar = form_data.get('confirmarSenha') or form_data.get('confirmar')

	r = validar_cpf(cpf)
	if not r.get('valido'):
		return {'valido': False, 'mensagem': r.get('mensagem', 'CPF inválido'), 'campo': 'cpf'}

	r = validar_email(email)
	if not r.get('valido'):
		return {'valido': False, 'mensagem': r.get('mensagem', 'Email inválido'), 'campo': 'email'}

	r = validar_telefone(telefone)
	if not r.get('valido'):
		return {'valido': False, 'mensagem': r.get('mensagem', 'Telefone inválido'), 'campo': 'telefone'}

	r = validar_matricula(matricula)
	if not r.get('valido'):
		return {'valido': False, 'mensagem': r.get('mensagem', 'Matrícula inválida'), 'campo': 'matricula'}

	r = validar_username(usuario)
	if not r.get('valido'):
		return {'valido': False, 'mensagem': r.get('mensagem', 'Nome de usuário inválido'), 'campo': 'usuario'}

	r = validar_senha(senha, confirmar)
	if not r.get('valido'):
		return {'valido': False, 'mensagem': r.get('mensagem', 'Senhas não coincidem'), 'campo': 'senha'}

	return {'valido': True, 'mensagem': 'Validação OK'}



# ----- Main Functions -----
def cadastrar_novo_usuario(form_data=None):
	r = validar_cadastro_no_usuario(form_data)
	if not r.get('valido'):
		return {'ok': False, 'mensagem': r.get('mensagem', 'Validação falhou'), 'campo': r.get('campo')}

	try:
		# Calcula novo id
		last_user = Usuario.query.order_by(Usuario.id.desc()).first()
		new_id = (last_user.id + 1) if last_user else 1

		registro = Usuario(
			id=new_id,
			data_criacao=datetime.now().isoformat(),
			cpf=re.sub(r'\D', '', str(form_data.get('cpf') or '')),
			email=str(form_data.get('email') or '').strip(),
			telefone=re.sub(r'\D', '', str(form_data.get('telefone') or '')),
			matricula=str(form_data.get('matricula') or '').strip(),
			usuario=str(form_data.get('usuario') or '').strip(),
			nome=str(form_data.get('nome') or form_data.get('nome_completo') or '').strip(),
			cargo=str(form_data.get('cargo') or '').strip(),
			unidade=str(form_data.get('unidade') or '').strip(),
			motivo=str(_first_present(form_data, 'motivo', 'motivo_solicitacao', 'justificativa', 'justificativa_acesso') or '').strip(),
			concordo=False,
			ativo=False,
			senha=_hash_password(form_data.get('senha') or '')
		)

		_concordo_raw = _first_present(
			form_data,
			'concordo',
			'concordo_termos',
			'aceito',
			'aceito_termos',
			'aceitarTermos',
			'aceitar_termos'
		)
		if _concordo_raw is not None:
			v = str(_concordo_raw).strip().lower()
			if v in ('1', 'true', 'on', 'yes', 'sim', 'y'):
				registro.concordo = True

		db.session.add(registro)
		db.session.commit()
		return {'ok': True, 'mensagem': 'Usuário cadastrado com sucesso. Aguarde a aprovação do seu cadastro.', 'id': new_id}
	except Exception as e:
		try:
			print('Erro ao salvar usuário:', e)
		except Exception:
			pass
		db.session.rollback()
		return {'ok': False, 'mensagem': 'Erro ao salvar usuário'}



def validar_login(login_value, senha):
	if not login_value:
		return {'ok': False, 'mensagem': 'Informe usuário ou e-mail'}

	is_email = ('@' in str(login_value))
	query = Usuario.query.filter_by(ativo=True)
	if is_email:
		user = query.filter(db.func.lower(Usuario.email) == str(login_value).lower()).first()
	else:
		user = query.filter(db.func.lower(Usuario.usuario) == str(login_value).lower()).first()
	if not user:
		return {'ok': False, 'mensagem': 'E-mail não cadastrado' if is_email else 'Usuário não cadastrado'}

	stored = user.senha
	if not _check_password(stored, senha):
		return {'ok': False, 'mensagem': 'Senha incorreta'}

	sanitized = {k: v for k, v in user.__dict__.items() if k != 'senha' and not k.startswith('_')}
	return {'ok': True, 'mensagem': 'Login efetuado com sucesso', 'user': sanitized}
