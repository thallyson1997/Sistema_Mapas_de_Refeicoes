import json
import os
from typing import Optional, Any


def get_base_dir():
	"""
	Retorna o diretório base do projeto (um nível acima de functions/)
	"""
	return os.path.dirname(os.path.dirname(__file__))


def get_dados_dir():
	"""
	Retorna o diretório de dados (dados/)
	"""
	return os.path.join(get_base_dir(), 'dados')


def get_file_path(filename):
	"""
	Retorna o caminho completo para um arquivo no diretório de dados
	"""
	return os.path.join(get_dados_dir(), filename)


def ensure_dir_exists(filepath):
	"""
	Garante que o diretório do arquivo existe, criando-o se necessário
	"""
	directory = os.path.dirname(filepath)
	if directory:
		os.makedirs(directory, exist_ok=True)


# ----- Generic JSON Operations -----
def load_json_file(filepath: str, default: Any = None) -> Any:
	"""
	Carrega um arquivo JSON
	
	Args:
		filepath: Caminho do arquivo
		default: Valor padrão a retornar se o arquivo não existir ou houver erro
	
	Returns:
		Dados do JSON ou valor padrão
	"""
	if not os.path.isfile(filepath):
		return default
	
	try:
		with open(filepath, 'r', encoding='utf-8') as f:
			return json.load(f)
	except Exception as e:
		print(f"Erro ao carregar {filepath}: {e}")
		return default


def save_json_file(filepath: str, data: Any, indent: int = 2) -> bool:
	"""
	Salva dados em um arquivo JSON de forma atômica (usando arquivo temporário)
	
	Args:
		filepath: Caminho do arquivo
		data: Dados a salvar
		indent: Indentação do JSON (padrão: 2)
	
	Returns:
		True se salvou com sucesso, False caso contrário
	"""
	try:
		ensure_dir_exists(filepath)
		tmp_path = filepath + '.tmp'
		
		with open(tmp_path, 'w', encoding='utf-8') as f:
			json.dump(data, f, ensure_ascii=False, indent=indent)
		
		# Substituição atômica
		os.replace(tmp_path, filepath)
		return True
	except Exception as e:
		print(f"Erro ao salvar {filepath}: {e}")
		# Tentar limpar arquivo temporário em caso de erro
		try:
			if os.path.exists(tmp_path):
				os.remove(tmp_path)
		except Exception:
			pass
		return False


def load_json_from_dados(filename: str, default: Any = None) -> Any:
	"""
	Carrega um arquivo JSON do diretório de dados
	"""
	Carrega um arquivo JSON do diretório de dados

	Args:
		filename: Nome do arquivo (ex: 'usuarios.json', 'unidades.json', etc.)
		default: Valor padrão a retornar se o arquivo não existir ou houver erro

	ATENÇÃO: Para dados de lotes, utilize sempre o banco de dados (SQLAlchemy) e não arquivos JSON.

	Returns:
		Dados do JSON ou valor padrão
	"""


def save_json_to_dados(filename: str, data: Any, indent: int = 2) -> bool:
	"""
	Salva dados em um arquivo JSON no diretório de dados

	Args:
		filename: Nome do arquivo (ex: 'usuarios.json', 'unidades.json', etc.)
		data: Dados a salvar
		indent: Indentação do JSON (padrão: 2)

	ATENÇÃO: Para dados de lotes, utilize sempre o banco de dados (SQLAlchemy) e não arquivos JSON.

	Returns:
		True se salvou com sucesso, False caso contrário
	"""
	filepath = get_file_path(filename)
	return save_json_file(filepath, data, indent)


def file_exists(filename: str) -> bool:
	"""
	Verifica se um arquivo existe no diretório de dados
	
	Args:
		filename: Nome do arquivo
	
	Returns:
		True se o arquivo existe, False caso contrário
	"""
	filepath = get_file_path(filename)
	return os.path.isfile(filepath)


def delete_file(filename: str) -> bool:
	"""
	Deleta um arquivo do diretório de dados
	
	Args:
		filename: Nome do arquivo
	
	Returns:
		True se deletou com sucesso, False caso contrário
	"""
	filepath = get_file_path(filename)
	try:
		if os.path.isfile(filepath):
			os.remove(filepath)
			return True
		return False
	except Exception as e:
		print(f"Erro ao deletar {filepath}: {e}")
		return False


def list_files_in_dados(pattern: Optional[str] = None) -> list:
	"""
	Lista arquivos no diretório de dados, opcionalmente filtrando por padrão
	
	Args:
		pattern: Padrão glob opcional (ex: '*.json', 'mapas_*.json')
	
	Returns:
		Lista de nomes de arquivos
	"""
	dados_dir = get_dados_dir()
	
	if not os.path.isdir(dados_dir):
		return []
	
	if pattern:
		import glob
		pattern_path = os.path.join(dados_dir, pattern)
		files = glob.glob(pattern_path)
		return [os.path.basename(f) for f in files]
	else:
		try:
			return [f for f in os.listdir(dados_dir) if os.path.isfile(os.path.join(dados_dir, f))]
		except Exception:
			return []


def backup_file(filename: str, suffix: str = '.backup') -> bool:
	"""
	Cria uma cópia de backup de um arquivo
	
	Args:
		filename: Nome do arquivo
		suffix: Sufixo para o arquivo de backup (padrão: '.backup')
	
	Returns:
		True se o backup foi criado, False caso contrário
	"""
	import shutil
	
	filepath = get_file_path(filename)
	if not os.path.isfile(filepath):
		return False
	
	backup_path = filepath + suffix
	try:
		shutil.copy2(filepath, backup_path)
		return True
	except Exception as e:
		print(f"Erro ao criar backup de {filepath}: {e}")
		return False


def restore_from_backup(filename: str, suffix: str = '.backup') -> bool:
	"""
	Restaura um arquivo a partir de seu backup
	
	Args:
		filename: Nome do arquivo
		suffix: Sufixo do arquivo de backup (padrão: '.backup')
	
	Returns:
		True se restaurou com sucesso, False caso contrário
	"""
	import shutil
	
	filepath = get_file_path(filename)
	backup_path = filepath + suffix
	
	if not os.path.isfile(backup_path):
		return False
	
	try:
		shutil.copy2(backup_path, filepath)
		return True
	except Exception as e:
		print(f"Erro ao restaurar backup de {filepath}: {e}")
		return False


def get_file_size(filename: str) -> int:
	"""
	Retorna o tamanho de um arquivo em bytes
	
	Args:
		filename: Nome do arquivo
	
	Returns:
		Tamanho em bytes, ou 0 se o arquivo não existir
	"""
	filepath = get_file_path(filename)
	try:
		return os.path.getsize(filepath)
	except Exception:
		return 0


def read_text_file(filename: str, encoding: str = 'utf-8') -> Optional[str]:
	"""
	Lê o conteúdo de um arquivo de texto
	
	Args:
		filename: Nome do arquivo
		encoding: Codificação do arquivo (padrão: 'utf-8')
	
	Returns:
		Conteúdo do arquivo ou None se houver erro
	"""
	filepath = get_file_path(filename)
	try:
		with open(filepath, 'r', encoding=encoding) as f:
			return f.read()
	except Exception as e:
		print(f"Erro ao ler {filepath}: {e}")
		return None


def write_text_file(filename: str, content: str, encoding: str = 'utf-8') -> bool:
	"""
	Escreve conteúdo em um arquivo de texto
	
	Args:
		filename: Nome do arquivo
		content: Conteúdo a escrever
		encoding: Codificação do arquivo (padrão: 'utf-8')
	
	Returns:
		True se salvou com sucesso, False caso contrário
	"""
	filepath = get_file_path(filename)
	try:
		ensure_dir_exists(filepath)
		with open(filepath, 'w', encoding=encoding) as f:
			f.write(content)
		return True
	except Exception as e:
		print(f"Erro ao escrever {filepath}: {e}")
		return False


def append_to_text_file(filename: str, content: str, encoding: str = 'utf-8') -> bool:
	"""
	Adiciona conteúdo ao final de um arquivo de texto
	
	Args:
		filename: Nome do arquivo
		content: Conteúdo a adicionar
		encoding: Codificação do arquivo (padrão: 'utf-8')
	
	Returns:
		True se salvou com sucesso, False caso contrário
	"""
	filepath = get_file_path(filename)
	try:
		ensure_dir_exists(filepath)
		with open(filepath, 'a', encoding=encoding) as f:
			f.write(content)
		return True
	except Exception as e:
		print(f"Erro ao adicionar conteúdo em {filepath}: {e}")
		return False
