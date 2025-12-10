from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    data_criacao = db.Column(db.String(32), nullable=False)
    cpf = db.Column(db.String(16), nullable=False)
    email = db.Column(db.String(128), nullable=False)
    telefone = db.Column(db.String(32), nullable=False)
    matricula = db.Column(db.String(32), nullable=False)
    usuario = db.Column(db.String(64), nullable=False)
    nome = db.Column(db.String(128), nullable=False)
    cargo = db.Column(db.String(64), nullable=True)
    unidade = db.Column(db.String(64), nullable=True)
    motivo = db.Column(db.Text, nullable=True)
    concordo = db.Column(db.Boolean, default=False)
    ativo = db.Column(db.Boolean, default=False)
    senha = db.Column(db.String(256), nullable=False)

    def __repr__(self):
        return f'<Usuario {self.id} {self.usuario}>'


# Modelo para Lote

class Lote(db.Model):
    __tablename__ = 'lotes'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(128), nullable=False)
    empresa = db.Column(db.String(128), nullable=True)
    numero_contrato = db.Column(db.String(32), nullable=True)
    numero = db.Column(db.String(32), nullable=True)
    data_inicio = db.Column(db.String(32), nullable=True)
    data_fim = db.Column(db.String(32), nullable=True)
    valor_contratual = db.Column(db.Float, nullable=True)
    unidades = db.Column(db.Text, nullable=True)  # Salvar como JSON/texto
    precos = db.Column(db.Text, nullable=True)    # Salvar como JSON/texto
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.String(32), nullable=True)
    data_criacao = db.Column(db.String(32), nullable=True)
    data_contrato = db.Column(db.String(32), nullable=True)
    status = db.Column(db.String(32), nullable=True)
    descricao = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Lote {self.id} {self.nome}>'


# Modelo para Unidade

class Unidade(db.Model):
    __tablename__ = 'unidades'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(128), nullable=False)
    lote_id = db.Column(db.Integer, nullable=True)
    criado_em = db.Column(db.String(32), nullable=True)
    ativo = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Unidade {self.id} {self.nome}>'


# Modelo para Mapa
class Mapa(db.Model):
    __tablename__ = 'mapas'
    id = db.Column(db.Integer, primary_key=True)
    lote_id = db.Column(db.Integer, nullable=False)
    mes = db.Column(db.Integer, nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    unidade = db.Column(db.String(128), nullable=False)
    linhas = db.Column(db.Integer, nullable=True)
    colunas_count = db.Column(db.Integer, nullable=True)
    dados_siisp = db.Column(db.Text, nullable=True)  # JSON/texto
    cafe_interno = db.Column(db.Text, nullable=True)  # JSON/texto
    cafe_funcionario = db.Column(db.Text, nullable=True)  # JSON/texto
    almoco_interno = db.Column(db.Text, nullable=True)  # JSON/texto
    almoco_funcionario = db.Column(db.Text, nullable=True)  # JSON/texto
    lanche_interno = db.Column(db.Text, nullable=True)  # JSON/texto
    lanche_funcionario = db.Column(db.Text, nullable=True)  # JSON/texto
    jantar_interno = db.Column(db.Text, nullable=True)  # JSON/texto
    jantar_funcionario = db.Column(db.Text, nullable=True)  # JSON/texto
    datas = db.Column(db.Text, nullable=True)  # JSON/texto
    criado_em = db.Column(db.String(32), nullable=True)
    atualizado_em = db.Column(db.String(32), nullable=True)
    cafe_interno_siisp = db.Column(db.Text, nullable=True)  # JSON/texto
    cafe_funcionario_siisp = db.Column(db.Text, nullable=True)  # JSON/texto
    almoco_interno_siisp = db.Column(db.Text, nullable=True)  # JSON/texto
    almoco_funcionario_siisp = db.Column(db.Text, nullable=True)  # JSON/texto
    lanche_interno_siisp = db.Column(db.Text, nullable=True)  # JSON/texto
    lanche_funcionario_siisp = db.Column(db.Text, nullable=True)  # JSON/texto
    jantar_interno_siisp = db.Column(db.Text, nullable=True)  # JSON/texto
    jantar_funcionario_siisp = db.Column(db.Text, nullable=True)  # JSON/texto

    def __repr__(self):
        return f'<Mapa {self.id} {self.unidade} {self.mes}/{self.ano}>'
