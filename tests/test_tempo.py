"""Testes de parsing e formatação de tempo."""
import pytest

from calculo import formatar_horas_minutos, parse_data_hora_input, parse_tempo_input


@pytest.mark.parametrize("entrada,esperado", [
    ("1.5", 1.5),
    ("0", 0.0),
    ("1:30", 1.5),
    ("1:30:12", 1.0 + 30 / 60.0 + 12 / 3600.0),
    ("90m", 1.5),
    ("1h30m", 1.5),
    ("1h30m12s", 1.0 + 30 / 60.0 + 12 / 3600.0),
    ("45s", 45 / 3600.0),
    (" 2 ", 2.0),
    ("2H", 2.0),
])
def test_parse_tempo_input_validos(entrada, esperado):
    assert parse_tempo_input(entrada) == pytest.approx(esperado)


@pytest.mark.parametrize("entrada", [
    "",
    "abc",
    "2:75",       # minutos >= 60
    "1:30:90",    # segundos >= 60
    "1:30:12:45", # formato inválido
])
def test_parse_tempo_input_invalidos(entrada):
    with pytest.raises(ValueError):
        parse_tempo_input(entrada)


@pytest.mark.parametrize("horas,esperado", [
    (0, "0s"),
    (1.0, "1h"),
    (1.5, "1h 30m"),
    (0.5, "30m"),
    (0.25, "15m"),
    (2.0 + 10.0 / 60.0 + 5.0 / 3600.0, "2h 10m 5s"),
])
def test_formatar_horas_minutos(horas, esperado):
    assert formatar_horas_minutos(horas) == esperado


def test_parse_data_hora_input_apenas_dia():
    ref = "15/08/2026 10:30:00"
    assert parse_data_hora_input("20", ref) == "20/08/2026 10:30:00"


def test_parse_data_hora_input_dia_mes():
    ref = "15/08/2026 10:30:00"
    assert parse_data_hora_input("5/7", ref) == "05/07/2026 10:30:00"


def test_parse_data_hora_input_dia_mes_ano():
    ref = "15/08/2026 10:30:00"
    assert parse_data_hora_input("5/7/25", ref) == "05/07/2025 10:30:00"
    assert parse_data_hora_input("5/7/2024", ref) == "05/07/2024 10:30:00"


def test_parse_data_hora_input_apenas_hora():
    ref = "15/08/2026 10:30:00"
    assert parse_data_hora_input("14:45", ref) == "15/08/2026 14:45:00"


def test_parse_data_hora_input_data_e_hora():
    ref = "15/08/2026 10:30:00"
    assert parse_data_hora_input("20 14:45", ref) == "20/08/2026 14:45:00"


def test_parse_data_hora_input_vazio_retorna_default():
    ref = "15/08/2026 10:30:00"
    assert parse_data_hora_input("", ref) == ref


def test_parse_data_hora_input_invalido():
    ref = "15/08/2026 10:30:00"
    with pytest.raises(ValueError):
        parse_data_hora_input("99/99/99", ref)
