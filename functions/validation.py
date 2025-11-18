import re


# ----- Number Conversion and Validation -----
def to_number(token):
	"""
	Converte um token (string, int, float) para número (int ou float)
	Retorna None se não for possível converter
	"""
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


def to_int(value, default=0):
	"""
	Converte um valor para inteiro, retornando default se falhar
	"""
	if value is None:
		return default
	try:
		return int(value)
	except (ValueError, TypeError):
		try:
			return int(float(value))
		except (ValueError, TypeError):
			return default


def to_float(value, default=0.0):
	"""
	Converte um valor para float, retornando default se falhar
	"""
	if value is None:
		return default
	try:
		if isinstance(value, str):
			value = value.replace(',', '.')
		return float(value)
	except (ValueError, TypeError):
		return default


def is_int_like(x):
	"""
	Verifica se um valor pode ser convertido para inteiro
	"""
	try:
		int(x)
		return True
	except Exception:
		return False


# ----- Array Normalization -----
def normalizar_array(arr):
	"""
	Normaliza um array, convertendo valores None, '', 'null' para 0
	e tentando converter todos os valores para inteiros
	"""
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


def coerce_to_list(value, default=None):
	"""
	Garante que um valor seja uma lista
	"""
	if isinstance(value, list):
		return value
	if default is not None:
		return default
	return []


# ----- Roman Numerals -----
def int_to_roman(num):
	"""
	Converte um número inteiro para numeral romano
	"""
	val = [
		1000, 900, 500, 400,
		100, 90, 50, 40,
		10, 9, 5, 4,
		1
	]
	syms = [
		"M", "CM", "D", "CD",
		"C", "XC", "L", "XL",
		"X", "IX", "V", "IV",
		"I"
	]
	roman_num = ''
	i = 0
	while num > 0:
		for _ in range(num // val[i]):
			roman_num += syms[i]
			num -= val[i]
		i += 1
	return roman_num


def roman_to_int(s):
	"""
	Converte um numeral romano para inteiro
	"""
	roman_values = {
		'I': 1, 'V': 5, 'X': 10, 'L': 50,
		'C': 100, 'D': 500, 'M': 1000
	}
	total = 0
	prev_value = 0
	for char in reversed(s.upper()):
		value = roman_values.get(char, 0)
		if value < prev_value:
			total -= value
		else:
			total += value
		prev_value = value
	return total


# ----- String Validation -----
def is_valid_email(email):
	"""
	Validação básica de email
	"""
	if not email or not isinstance(email, str):
		return False
	pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
	return bool(re.match(pattern, email))


def is_valid_cpf(cpf):
	"""
	Validação básica de CPF (formato)
	"""
	if not cpf or not isinstance(cpf, str):
		return False
	cpf = re.sub(r'[^0-9]', '', cpf)
	return len(cpf) == 11


def is_valid_phone(phone):
	"""
	Validação básica de telefone brasileiro
	"""
	if not phone or not isinstance(phone, str):
		return False
	phone = re.sub(r'[^0-9]', '', phone)
	return len(phone) >= 10 and len(phone) <= 11


# ----- Date Validation -----
def is_valid_date_format(date_str, format='DD/MM/YYYY'):
	"""
	Valida se uma string está no formato de data especificado
	"""
	if not date_str or not isinstance(date_str, str):
		return False
	
	if format == 'DD/MM/YYYY':
		pattern = r'^\d{2}/\d{2}/\d{4}$'
		return bool(re.match(pattern, date_str))
	elif format == 'YYYY-MM-DD':
		pattern = r'^\d{4}-\d{2}-\d{2}$'
		return bool(re.match(pattern, date_str))
	
	return False


def parse_date_parts(date_str):
	"""
	Extrai dia, mês e ano de uma string de data
	Retorna (dia, mes, ano) ou (None, None, None) se falhar
	"""
	if not date_str or not isinstance(date_str, str):
		return None, None, None
	
	# Formato DD/MM/YYYY
	match = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', date_str)
	if match:
		dia = int(match.group(1))
		mes = int(match.group(2))
		ano = int(match.group(3))
		return dia, mes, ano
	
	# Formato YYYY-MM-DD
	match = re.match(r'^(\d{4})-(\d{1,2})-(\d{1,2})$', date_str)
	if match:
		ano = int(match.group(1))
		mes = int(match.group(2))
		dia = int(match.group(3))
		return dia, mes, ano
	
	return None, None, None


# ----- Data Structure Validation -----
def is_valid_dict(value, required_keys=None):
	"""
	Valida se um valor é um dicionário e opcionalmente verifica chaves obrigatórias
	"""
	if not isinstance(value, dict):
		return False
	
	if required_keys:
		for key in required_keys:
			if key not in value:
				return False
	
	return True


def is_valid_list_of_type(value, expected_type):
	"""
	Valida se um valor é uma lista e todos os elementos são do tipo esperado
	"""
	if not isinstance(value, list):
		return False
	
	return all(isinstance(item, expected_type) for item in value)


# ----- Range Validation -----
def is_in_range(value, min_val=None, max_val=None):
	"""
	Verifica se um valor numérico está dentro de um intervalo
	"""
	try:
		num = float(value)
		if min_val is not None and num < min_val:
			return False
		if max_val is not None and num > max_val:
			return False
		return True
	except (ValueError, TypeError):
		return False


def is_valid_month(month):
	"""
	Valida se um valor é um mês válido (1-12)
	"""
	try:
		m = int(month)
		return 1 <= m <= 12
	except (ValueError, TypeError):
		return False


def is_valid_year(year, min_year=1900, max_year=2100):
	"""
	Valida se um valor é um ano válido
	"""
	try:
		y = int(year)
		return min_year <= y <= max_year
	except (ValueError, TypeError):
		return False


# ----- String Sanitization -----
def sanitize_string(value, max_length=None):
	"""
	Sanitiza uma string, removendo espaços extras e limitando tamanho
	"""
	if not isinstance(value, str):
		value = str(value)
	
	value = value.strip()
	value = re.sub(r'\s+', ' ', value)
	
	if max_length and len(value) > max_length:
		value = value[:max_length]
	
	return value


def remove_special_chars(value, keep_spaces=True):
	"""
	Remove caracteres especiais de uma string
	"""
	if not isinstance(value, str):
		value = str(value)
	
	if keep_spaces:
		return re.sub(r'[^a-zA-Z0-9\s]', '', value)
	else:
		return re.sub(r'[^a-zA-Z0-9]', '', value)


# ----- Empty Value Checks -----
def is_empty(value):
	"""
	Verifica se um valor está vazio (None, '', [], {})
	"""
	if value is None:
		return True
	if isinstance(value, str) and value.strip() == '':
		return True
	if isinstance(value, (list, dict)) and len(value) == 0:
		return True
	return False


def get_first_present(*values):
	"""
	Retorna o primeiro valor não vazio da lista de argumentos
	"""
	for value in values:
		if not is_empty(value):
			return value
	return None
