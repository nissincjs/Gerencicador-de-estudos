"""Testes do módulo database: fator, migrações, backups e recuperação."""
import json

import pytest

import database


@pytest.fixture
def db_file(tmp_path, monkeypatch):
    """Redireciona o DB_FILE para um arquivo temporário isolado."""
    caminho = tmp_path / "ciclo.json"
    monkeypatch.setattr(database, "DB_FILE", str(caminho))
    return str(caminho)


def test_obter_fator():
    m = {"questoes_prova": 10, "peso_questao": 1, "dificuldade": 2}
    assert database.obter_fator(m) == 20


def test_obter_fator_defaults():
    assert database.obter_fator({}) == 10.0


def test_processar_migracoes_preenche_campos_ausentes():
    dados = {}
    resultado = database._processar_migracoes(dados)
    assert resultado["horas_semanais"] == 0.0
    assert resultado["materias"] == []
    assert resultado["revisoes"] == []
    assert resultado["limite_revisoes_diarias"] == 10
    assert resultado["justificativas"] == []
    assert resultado["atualizacao_automatica"] is True


def test_processar_migracoes_converte_formato_antigo():
    dados = {
        "materias": [
            {
                "nome": "Mat",
                "aulas": [{"tema": "x"}],
                "peso": 2.0,
            }
        ],
        "revisoes": [],
    }
    resultado = database._processar_migracoes(dados)
    materia = resultado["materias"][0]
    assert "aulas" not in materia
    assert materia["peso_questao"] == 2.0
    assert "peso" not in materia
    assert materia["questoes_prova"] == 10.0


def test_processar_migracoes_revisoes_antigas():
    dados = {"revisoes": [{"acertos_pct": 80.0, "intervalo_dias": 5, "data_ultimo_estudo": "01/01/2026"}]}
    resultado = database._processar_migracoes(dados)
    r = resultado["revisoes"][0]
    assert r["ease_factor"] == 2.5
    assert r["historico_acertos"] == [80.0]
    assert r["historico_intervalos"] == [5]
    assert r["historico_datas"] == ["01/01/2026"]
    assert r["historico_ease_factors"] == [2.5]


def test_salvar_local_cria_backups_rotativos(db_file):
    for i in range(1, 5):
        dados = database.novo_ciclo()
        dados["horas_semanais"] = float(i)
        database.salvar_local(dados, "user@x.com")

    principal = json.load(open(db_file))
    assert principal["horas_semanais"] == 4.0
    assert principal.get("owner_email") == "user@x.com"

    assert json.load(open(database._caminho_backup(1)))["horas_semanais"] == 3.0
    assert json.load(open(database._caminho_backup(2)))["horas_semanais"] == 2.0
    assert json.load(open(database._caminho_backup(3)))["horas_semanais"] == 1.0


def test_salvar_local_nao_deixa_tmp(db_file):
    dados = database.novo_ciclo()
    database.salvar_local(dados)
    assert not __import__("os").path.exists(f"{db_file}.tmp")


def test_carregar_dados_recupera_de_backup(db_file, monkeypatch):
    for i in range(1, 5):
        dados = database.novo_ciclo()
        dados["horas_semanais"] = float(i)
        database.salvar_local(dados, "user@x.com")

    # Corrompe o arquivo principal
    with open(db_file, "w") as f:
        f.write("{corrompido!!!")
    monkeypatch.setattr(database, "input", lambda prompt="": "")

    recuperados = database.carregar_dados("user@x.com")
    assert recuperados["horas_semanais"] == 3.0  # estado anterior ao corrompido


def test_carregar_dados_backup_de_outra_conta(db_file, monkeypatch):
    for i in range(1, 5):
        dados = database.novo_ciclo()
        dados["horas_semanais"] = float(i)
        database.salvar_local(dados, "outra@x.com")

    with open(db_file, "w") as f:
        f.write("{corrompido!!!")
    monkeypatch.setattr(database, "input", lambda prompt="": "")

    resultado = database.carregar_dados("user@x.com")
    assert resultado["horas_semanais"] == 0.0  # backup pertence a outra conta


def test_carregar_dados_tudo_corrompido(db_file, monkeypatch):
    for suf in ["", ".backup1", ".backup2", ".backup3"]:
        with open(db_file + suf, "w") as f:
            f.write("x")
    monkeypatch.setattr(database, "input", lambda prompt="": "")
    resultado = database.carregar_dados()
    assert resultado["horas_semanais"] == 0.0
