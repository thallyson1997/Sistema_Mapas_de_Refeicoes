# Este arquivo foi refatorado. As funções foram movidas para:
# - auth.py: Autenticação e validação de usuários
# - mapas.py: Operações com mapas de refeições
# - siisp.py: Operações SIISP
# - lotes.py: Operações com lotes
# - unidades.py: Operações com unidades
# - validation.py: Funções de validação e conversão
# - file_utils.py: Operações com arquivos
# - helpers.py: Funções auxiliares de integração

# Importar e re-exportar funções principais para compatibilidade
from .helpers import carregar_lotes_para_dashboard, gerar_excel_exportacao
from .lotes import (
    salvar_novo_lote, editar_lote, deletar_lote,
    obter_lote_por_id, listar_lotes, normalizar_precos,
    calcular_ultima_atividade_lotes, editar_lote
)
from .unidades import (
    criar_unidade, editar_unidade, deletar_unidade,
    obter_unidade_por_id, obter_unidade_por_nome,
    listar_unidades, obter_mapa_unidades
)
from .mapas import (
    salvar_mapas_raw, preparar_dados_entrada_manual,
    reordenar_registro_mapas, excluir_mapa, calcular_metricas_lotes
)
from .siisp import (
    adicionar_siisp_em_mapa, validar_dados_siisp,
    processar_texto_siisp, calcular_discrepancias_siisp,
    obter_resumo_siisp
)
from .auth import (
    cadastrar_novo_usuario, validar_login,
    validar_cpf, validar_email, validar_telefone,
    validar_matricula, validar_username, validar_senha,
    validar_cadastro_no_usuario
)
from .lotes import _load_lotes_data
from .unidades import _load_unidades_data
from .mapas import _load_mapas_partitioned

__all__ = [
    # Helpers
    'carregar_lotes_para_dashboard',
    'gerar_excel_exportacao',
    # Lotes
    'salvar_novo_lote',
    'editar_lote',
    'deletar_lote',
    'obter_lote_por_id',
    'listar_lotes',
    'normalizar_precos',
    'calcular_ultima_atividade_lotes',
    '_load_lotes_data',
    'editar_lote',
    # Unidades
    'criar_unidade',
    'editar_unidade',
    'deletar_unidade',
    'obter_unidade_por_id',
    'obter_unidade_por_nome',
    'listar_unidades',
    'obter_mapa_unidades',
    '_load_unidades_data',
    # Mapas
    'salvar_mapas_raw',
    'preparar_dados_entrada_manual',
    'reordenar_registro_mapas',
    'excluir_mapa',
    'calcular_metricas_lotes',
    '_load_mapas_partitioned',
    # SIISP
    'adicionar_siisp_em_mapa',
    'validar_dados_siisp',
    'processar_texto_siisp',
    'calcular_discrepancias_siisp',
    'obter_resumo_siisp',
    # Auth
    'cadastrar_novo_usuario',
    'validar_login',
    'validar_cpf',
    'validar_email',
    'validar_telefone',
    'validar_matricula',
    'validar_username',
    'validar_senha',
    'validar_cadastro_no_usuario',
]
