"""Testes de consistência de estudos: streak, estudos por dia e metas semanais."""
from datetime import datetime, timedelta

import pytest

from calculo import (
    calcular_estudos_por_dia,
    calcular_streak,
    obter_estudos_hoje,
    obter_metas_semana,
)


def _sessao(dias_atras, horas, materia="Mat", tipo="registro"):
    dt = (datetime.now() - timedelta(days=dias_atras)).strftime("%d/%m/%Y %H:%M:%S")
    return {"data": dt, "materia": materia, "horas": horas, "tipo": tipo}


def _dados(sessoes, materias=None, horas_semanais=10.0, progresso=None):
    return {
        "historico_sessoes": sessoes,
        "historico_ciclos": [],
        "materias": materias or [],
        "horas_semanais": horas_semanais,
        "progresso_atual": progresso or {},
    }


def test_streak_sem_sessoes():
    assert calcular_streak(_dados([])) == 0


def test_streak_zero_se_nao_estudou_recentemente():
    # Só estudou há 5 dias -> streak 0
    dados = _dados([_sessao(5, 1.0)])
    assert calcular_streak(dados) == 0


def test_streak_consecutivo():
    # Hoje, ontem e anteontem -> streak 3
    dados = _dados([_sessao(0, 1.0), _sessao(1, 1.0), _sessao(2, 1.0)])
    assert calcular_streak(dados) == 3


def test_streak_quebra_nao_quebra_contagem():
    # Hoje e ontem estudou, há 3 dias não, há 4 dias sim -> streak 2
    dados = _dados([_sessao(0, 1.0), _sessao(1, 1.0), _sessao(4, 1.0)])
    assert calcular_streak(dados) == 2


def test_estudos_por_dia_acumula_registros():
    dados = _dados([
        _sessao(0, 1.0),
        _sessao(0, 0.5),
        _sessao(1, 2.0),
    ])
    por_dia = calcular_estudos_por_dia(dados)
    hoje = datetime.now().strftime("%d/%m/%Y")
    ontem = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
    assert por_dia[hoje]["Mat"] == pytest.approx(1.5)
    assert por_dia[ontem]["Mat"] == 2.0


def test_estudos_por_dia_ajuste_substitui():
    # Ajuste substitui o acumulado: 3h registradas, ajustado para 1h -> total do dia 1h
    dados = _dados([
        _sessao(0, 3.0),
        _sessao(0, 1.0, tipo="ajuste"),
    ])
    por_dia = calcular_estudos_por_dia(dados)
    hoje = datetime.now().strftime("%d/%m/%Y")
    assert por_dia[hoje]["Mat"] == pytest.approx(1.0)


def test_estudos_por_dia_reseta_no_reinicio_de_ciclo():
    # Uma sessão anterior a um fim de ciclo não entra no delta posterior
    dados = {
        "historico_sessoes": [
            {"data": "01/01/2020 10:00:00", "materia": "Mat", "horas": 5.0, "tipo": "registro"},
            _sessao(0, 1.0),
        ],
        "historico_ciclos": [
            {"data_fim": "01/01/2020 11:00:00"},
        ],
    }
    por_dia = calcular_estudos_por_dia(dados)
    hoje = datetime.now().strftime("%d/%m/%Y")
    assert por_dia[hoje]["Mat"] == 1.0


def test_obter_estudos_hoje():
    dados = _dados([_sessao(0, 2.0), _sessao(1, 1.0)])
    info = obter_estudos_hoje(dados)
    assert info["estudou"] is True
    assert info["total_horas"] == pytest.approx(2.0)
    assert "Mat" in info["materias"]


def test_obter_estudos_hoje_nao_estudou():
    dados = _dados([_sessao(1, 1.0)])
    info = obter_estudos_hoje(dados)
    assert info["estudou"] is False


def test_obter_metas_semana():
    materias = [
        {"nome": "Mat1", "questoes_prova": 10, "peso_questao": 1, "dificuldade": 1},
        {"nome": "Mat2", "questoes_prova": 10, "peso_questao": 1, "dificuldade": 1},
    ]
    dados = _dados([], materias=materias, horas_semanais=10.0, progresso={"Mat1": 6.0, "Mat2": 1.0})
    metas = obter_metas_semana(dados)
    # meta de cada matéria = 5h; Mat1 atingiu (6 >= 5), Mat2 não (1 < 5)
    assert metas == {"cumpridas": 1, "total": 2}


def test_obter_metas_semana_sem_materias():
    assert obter_metas_semana(_dados([])) == {"cumpridas": 0, "total": 0}
