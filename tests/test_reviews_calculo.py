"""Testes do algoritmo SM2 (revisões) e funções de arredondamento/status."""
from datetime import datetime, timedelta

import pytest

from calculo import (
    arredondar_dias,
    calcular_proxima_revisao,
    calcular_status_e_dias,
)


def test_arredondar_dias_positivos():
    assert arredondar_dias(2.5) == 3
    assert arredondar_dias(2.4) == 2
    assert arredondar_dias(0.5) == 1
    assert arredondar_dias(0.49) == 0


def test_arredondar_dias_negativos():
    assert arredondar_dias(-2.5) == -3
    assert arredondar_dias(-2.4) == -2


def test_calcular_status_e_dias_passado():
    ontem = (datetime.now().date() - timedelta(days=1)).strftime("%d/%m/%Y")
    descricao, delta = calcular_status_e_dias(ontem)
    assert delta == -1
    assert "Atrasado" in descricao


def test_calcular_status_e_dias_hoje():
    hoje = datetime.now().strftime("%d/%m/%Y")
    descricao, delta = calcular_status_e_dias(hoje)
    assert delta == 0
    assert "Hoje" in descricao


def test_calcular_status_e_dias_futuro():
    amanha = (datetime.now().date() + timedelta(days=1)).strftime("%d/%m/%Y")
    descricao, delta = calcular_status_e_dias(amanha)
    assert delta == 1
    assert "Em 1 dias" in descricao


def test_calcular_status_e_dias_invalido():
    descricao, delta = calcular_status_e_dias("data-invalida")
    assert descricao == "N/A"
    assert delta == 0


def test_sem_nota_mantem_progressao_padrao():
    # Sem acertos informados: intervalo = anterior * ease_factor (arredondado)
    data_base = "01/01/2026"
    data_proxima, novo_intervalo, anterior, ef_novo, info = calcular_proxima_revisao(
        data_base_str=data_base,
        acertos_pct=None,
        intervalo_dias_atual=10,
        revisoes_feitas=5,
        ease_factor=2.5,
    )
    assert novo_intervalo == 25  # 10 * 2.5
    assert ef_novo == 2.5
    assert data_proxima == (datetime(2026, 1, 1) + timedelta(days=25)).strftime("%d/%m/%Y")


def test_lapso_reinicia_intervalo():
    # Desempenho < 50% -> lapso, intervalo volta para 1 dia
    data_proxima, novo_intervalo, _, ef_novo, info = calcular_proxima_revisao(
        data_base_str="01/01/2026",
        acertos_pct=40.0,
        intervalo_dias_atual=30,
        revisoes_feitas=5,
        ease_factor=2.5,
        historico_acertos=[40.0, 45.0],
    )
    assert novo_intervalo == 1
    assert data_proxima == "02/01/2026"


def test_primeira_revisao_intervalo_inicial():
    data_proxima, novo_intervalo, anterior, _, _ = calcular_proxima_revisao(
        data_base_str="01/01/2026",
        acertos_pct=90.0,
        intervalo_dias_atual=None,
        revisoes_feitas=0,
        ease_factor=2.5,
    )
    assert anterior == 3  # padrão inicial
    assert novo_intervalo >= 1


def test_ease_factor_clamp_inferior():
    # Muitos acertos muito baixos -> ease factor não desce abaixo de 1.3
    _, _, _, ef_novo, _ = calcular_proxima_revisao(
        data_base_str="01/01/2026",
        acertos_pct=0.0,
        intervalo_dias_atual=3,
        revisoes_feitas=1,
        ease_factor=1.3,
        historico_acertos=[0.0],
    )
    assert ef_novo >= 1.3


def test_ease_factor_clamp_superior():
    _, _, _, ef_novo, _ = calcular_proxima_revisao(
        data_base_str="01/01/2026",
        acertos_pct=100.0,
        intervalo_dias_atual=3,
        revisoes_feitas=1,
        ease_factor=4.9,
        historico_acertos=[100.0, 100.0],
    )
    assert ef_novo <= 5.0


def test_bonus_consistencia_melhora():
    # Tendência de melhora contínua aplica +10%
    _, intervalo_melhorando, _, _, _ = calcular_proxima_revisao(
        data_base_str="01/01/2026",
        acertos_pct=90.0,
        intervalo_dias_atual=10,
        revisoes_feitas=3,
        ease_factor=2.5,
        historico_acertos=[60.0, 75.0, 85.0],
    )
    _, intervalo_estavel, _, _, _ = calcular_proxima_revisao(
        data_base_str="01/01/2026",
        acertos_pct=90.0,
        intervalo_dias_atual=10,
        revisoes_feitas=3,
        ease_factor=2.5,
        historico_acertos=[85.0, 85.0, 85.0],
    )
    assert intervalo_melhorando > intervalo_estavel


def test_bonus_alta_performance():
    # 3 revisões >= 90% aplicam +15%
    _, intervalo_alto, _, _, _ = calcular_proxima_revisao(
        data_base_str="01/01/2026",
        acertos_pct=95.0,
        intervalo_dias_atual=10,
        revisoes_feitas=3,
        ease_factor=2.5,
        historico_acertos=[92.0, 94.0, 90.0],
    )
    _, intervalo_normal, _, _, _ = calcular_proxima_revisao(
        data_base_str="01/01/2026",
        acertos_pct=95.0,
        intervalo_dias_atual=10,
        revisoes_feitas=3,
        ease_factor=2.5,
        historico_acertos=[70.0, 80.0, 90.0],
    )
    assert intervalo_alto > intervalo_normal


def test_penalidade_declinio():
    # Queda contínua aplica -15% (intervalo menor que o caso neutro)
    _, intervalo_queda, _, _, _ = calcular_proxima_revisao(
        data_base_str="01/01/2026",
        acertos_pct=80.0,
        intervalo_dias_atual=10,
        revisoes_feitas=3,
        ease_factor=2.5,
        historico_acertos=[95.0, 88.0, 82.0],
    )
    _, intervalo_estavel, _, _, _ = calcular_proxima_revisao(
        data_base_str="01/01/2026",
        acertos_pct=80.0,
        intervalo_dias_atual=10,
        revisoes_feitas=3,
        ease_factor=2.5,
        historico_acertos=[80.0, 80.0, 80.0],
    )
    assert intervalo_queda < intervalo_estavel
