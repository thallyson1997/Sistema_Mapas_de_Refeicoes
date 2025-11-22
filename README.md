# SGMRP - Sistema de Gerenciamento de Mapas de Refeições Penitenciário

## Sobre o Projeto

O SGMRP é um sistema web desenvolvido em Python/Flask para gerenciar e monitorar o fornecimento de refeições em unidades prisionais do Estado. O objetivo é substituir o uso de planilhas Excel fragmentadas por uma solução centralizada, automatizada e segura, facilitando a gestão administrativa e o controle de conformidade dos lotes contratuais.

## Funcionalidades Disponíveis

### 🔐 Autenticação e Controle de Acesso
- Sistema completo de login/logout com validação de credenciais
- Cadastro de novos usuários com validação em tempo real (CPF, email, telefone, matrícula)
- Sistema de aprovação administrativa para novos usuários
- Controle de sessão seguro com Flask sessions
- Proteção de rotas com verificação de autenticação

### 📊 Gestão de Lotes Contratuais
- **Listagem de Lotes**: Visualização de todos os lotes com cards estilizados
- **Criação de Lotes**: Modal para adicionar novos lotes com validação completa
  - Dados da empresa contratada
  - Número do contrato
  - Data de início e fim do contrato
  - Valor contratual
  - Unidades vinculadas ao lote
  - Preços por tipo de refeição (café, almoço, lanche, jantar) e categoria (interno/funcionário)
- **Edição de Lotes**: Atualização de informações contratuais
- **Métricas Automatizadas**:
  - Refeições/Mês (média mensal)
  - Custo/Mês (média mensal de gastos)
  - Desvio/Mês (média mensal de desvios)
  - % Executado (percentual do valor contratual consumido)
  - Última atividade registrada

### 📈 Dashboard Interativo
- Visão geral consolidada de todos os lotes contratuais
- Indicadores de conformidade e performance
- Gráficos e métricas em tempo real
- Navegação rápida entre lotes e unidades
- Breadcrumbs estilizados para navegação intuitiva

### 🏢 Detalhes do Lote (Página Dedicada)
- Informações completas do contrato
- Sistema de abas para organização de dados:
  - **Dados de Refeições**: Tabela com todos os registros diários
  - **Comparação SIISP**: Análise de conformidade com dados oficiais
- **Sub-abas de Resumo**:
  - Resumo Geral (métricas consolidadas)
  - Resumo por Unidade (detalhamento por estabelecimento)
  - Resumo Mensal (evolução temporal)
- Filtros avançados:
  - Período (data início e fim)
  - Unidades específicas (multi-select)
  - Aplicação dinâmica sem reload da página

### 📥 Importação de Dados
- **Três métodos de entrada**:
  1. **Adicionar Dados (Texto Tabulado)**:
     - Cola dados copiados do Excel/PDFs
     - Suporta separadores TAB e espaços
     - Validação automática de formato
     - Seleção de mês/ano e unidade
  
  2. **Entrada Manual**:
     - Tabela interativa estilo Excel
     - Navegação por teclado (setas, Tab, Enter)
     - Suporte para Ctrl+V (colar dados tabulares)
     - Geração automática de dias do mês
     - Validação de dados em tempo real
  
  3. **Adicionar Números SIISP**:
     - Importação de dados oficiais do sistema SIISP
     - Comparação automática com registros internos
     - Cálculo de conformidade e desvios

### 🗑️ Exclusão de Dados
- Exclusão seletiva por unidade, mês e ano
- Modal de confirmação para evitar exclusões acidentais
- Atualização automática das métricas após exclusão

### 📑 Exportação para Excel
- Geração dinâmica de planilhas Excel
- Aplicação de filtros na exportação:
  - Por lote específico
  - Por unidades selecionadas
  - Por período (data início/fim)
- Formato padronizado com:
  - Cabeçalho com informações do lote
  - Dados organizados por unidade
  - Cálculos automáticos de totais
  - Fórmulas pré-configuradas
- Download direto pelo navegador

### 🔍 Filtros e Ordenação
- **Filtros Avançados na Listagem de Lotes**:
  - Busca por nome/empresa
  - Status (ativo/inativo)
  - Empresa contratada
  - % Executado (alto >80%, médio 50-80%, baixo <50%)
- **Ordenação**:
  - Por nome (alfabética)
  - Por % executado (decrescente)
  - Por refeições/mês (decrescente)
  - Por atualização recente
- Contador de resultados visíveis em tempo real

### 🎨 Interface do Usuário
- Design moderno e responsivo
- Breadcrumbs estilizados em todas as páginas
- Cards com visual profissional e badges de status
- Notificações toast para feedback de ações
- Animações suaves (fade-in, slide)
- Sistema de modais para ações importantes
- Formulários com validação visual em tempo real
- Mensagens de erro/sucesso contextualizadas

### 🔌 APIs RESTful
- `POST /api/novo-lote`: Criar novo lote
- `PUT /api/editar-lote/<id>`: Editar lote existente
- `POST /api/adicionar-dados`: Importar dados tabulados
- `POST /api/entrada-manual`: Salvar dados digitados manualmente
- `POST /api/adicionar-siisp`: Adicionar dados do sistema SIISP
- `DELETE /api/excluir-dados`: Excluir registros específicos
- `POST /api/validar-campo`: Validação individual de campos
- `GET /exportar-tabela`: Exportar dados filtrados em Excel

### 🛡️ Segurança e Validação
- Validação de CPF com algoritmo verificador
- Validação de email com regex
- Validação de telefone (formato brasileiro)
- Validação de matrícula funcional
- Validação de username (disponibilidade)
- Validação de senha com requisitos mínimos
- Proteção contra SQL injection (uso de JSON)
- Sanitização de inputs do usuário
- Controle de acesso baseado em sessão

## Restrições e Observações

- **Os arquivos de dados reais (.json) NÃO estão disponíveis no repositório** por questões de segurança e privacidade. Apenas arquivos de exemplo ou estrutura vazia podem ser fornecidos para desenvolvimento.
- O sistema depende dos arquivos JSON em `dados/` para funcionar plenamente (usuarios.json, lotes.json, unidades.json, mapas.json). Para testes, crie arquivos de exemplo ou solicite ao administrador.
- O arquivo modelo.xlsx deve estar presente em `dados/` para exportação de planilhas.

## Estrutura do Projeto

```
Sistema_Gerenciamento_Mapas_de_Refei-es_Penitenci-rio/
├── main.py                # Aplicação Flask principal
├── requirements.txt       # Dependências Python
├── dados/                 # Base de dados JSON (NÃO disponível no repositório)
│   ├── modelo.xlsx        # Modelo de planilha Excel para exportação
│   ├── usuarios.json      # Controle de usuários
│   ├── lotes.json         # Dados dos lotes
│   ├── unidades.json      # Dados das unidades
│   └── mapas.json         # Dados de refeições
├── templates/             # Templates HTML (Jinja2)
├── static/                # Arquivos estáticos (CSS)
└── README.md              # Documentação do projeto
```

## Instalação e Execução

### Pré-requisitos
- Python 3.11 ou superior
- pip (gerenciador de pacotes)

### Passos para Instalar

1. Clone o repositório:
	```bash
	git clone https://github.com/thallyson1997/Sistema_Gerenciamento_Mapas_de_Refei-es_Penitenci-rio.git
	cd Sistema_Gerenciamento_Mapas_de_Refei-es_Penitenci-rio
	```
2. Instale as dependências:
	```bash
	pip install -r requirements.txt
	```
3. Certifique-se de que o arquivo `modelo.xlsx` está presente em `dados/`.
4. Crie arquivos JSON de exemplo em `dados/` se necessário para testes locais.
5. Execute a aplicação:
	```bash
	python main.py
	```
6. Acesse o sistema em [http://localhost:5000](http://localhost:5000)

### Credenciais Padrão

- **Administrador**: `admin@seap.gov.br` / `admin123`
- **Usuário alternativo**: `admin` / `admin123`
- Novos usuários podem se cadastrar via `/cadastro` (necessita aprovação administrativa)

**⚠️ Importante**: Em produção, altere as credenciais padrão e utilize senhas fortes!

## Principais Rotas e APIs

### 🌐 Rotas da Aplicação

- `/` - Página inicial
- `/login` - Login de usuário
- `/cadastro` - Cadastro de usuário
- `/logout` - Logout e limpeza de sessão
- `/dashboard` - Painel principal com métricas consolidadas
- `/lotes` - Listagem de todos os lotes contratuais
- `/lote/<id>` - Detalhes completos de um lote específico
- `/admin/usuarios` - Gestão de usuários (somente admin)
- `/admin/usuarios/<id>/aprovar` - Aprovar cadastro de usuário
- `/admin/usuarios/<id>/revogar` - Revogar acesso de usuário
- `/exportar-tabela` - Exportação de dados em Excel (com filtros via query params)

### 🔌 Endpoints da API

- `POST /api/novo-lote` - Criar novo lote contratual
- `PUT /api/editar-lote/<id>` - Editar lote existente
- `POST /api/adicionar-dados` - Importar dados de refeições (formato tabulado)
- `POST /api/entrada-manual` - Salvar dados digitados manualmente
- `POST /api/adicionar-siisp` - Adicionar/atualizar dados do sistema SIISP
- `DELETE /api/excluir-dados` - Excluir registros de mapas específicos
- `POST /api/validar-campo` - Validar campos individuais em tempo real
- `GET /api/lotes` - Listar todos os lotes (JSON)

### 📋 Parâmetros da Exportação Excel

```http
GET /exportar-tabela?lote_id=<id>&unidades=<u1,u2>&data_inicio=<YYYY-MM-DD>&data_fim=<YYYY-MM-DD>
```

- `lote_id` (obrigatório): ID do lote a ser exportado
- `unidades` (opcional): Lista de unidades separadas por vírgula
- `data_inicio` (opcional): Data inicial do filtro
- `data_fim` (opcional): Data final do filtro

## Exportação de Dados para Excel

O sistema possui um módulo avançado de exportação de dados para planilhas Excel com as seguintes características:

### 📊 Recursos de Exportação

- **Geração Dinâmica**: Planilhas criadas em tempo real com base nos filtros aplicados
- **Modelo Padronizado**: Utiliza template pré-configurado (`modelo.xlsx`)
- **Filtros Flexíveis**:
  - Exportação completa do lote (sem filtros)
  - Filtragem por unidades específicas
  - Filtragem por período (data início e fim)
- **Estrutura do Arquivo Gerado**:
  - Cabeçalho com informações do lote e contrato
  - Dados organizados por unidade prisional
  - Tabelas com totais de refeições por tipo
  - Cálculos automáticos de custos (fórmulas Excel)
  - Totalizadores por unidade e geral
  - Formatação profissional e legível

### 🎯 Como Usar

1. Acesse a página de detalhes do lote
2. Aplique os filtros desejados (período, unidades)
3. Clique no botão "Exportar Dados"
4. O arquivo Excel será gerado e baixado automaticamente
5. Nome do arquivo: `lote_<id>_completo.xlsx`

### 📝 Conteúdo Exportado

- Data de cada registro
- Café da Manhã (Internos e Funcionários)
- Almoço (Internos e Funcionários)
- Lanche (Internos e Funcionários)
- Jantar (Internos e Funcionários)
- Totais por tipo de refeição
- Valores contratuais por refeição
- Cálculo automático do custo total

## Segurança e Privacidade

- Dados reais de produção NÃO são versionados no Git (protegidos por `.gitignore`)
- Recomenda-se usar arquivos de exemplo para desenvolvimento
- Nunca compartilhe dados sensíveis em ambientes públicos

## Licença

Este projeto está licenciado sob a GNU General Public License v3.0. Consulte o arquivo LICENSE para detalhes.

## Contato

**Desenvolvedor**: Thallyson Gabriel Martins Correia Fontenele  
**Email**: <thallysong10@hotmail.com>  
**Órgão**: SEAP/SFA
