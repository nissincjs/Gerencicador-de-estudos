import os
import re
from constants import *

def clear_screen():
    """Limpa a tela do terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    """Exibe um cabeçalho estilizado com bordas duplas (largura de UI_WIDTH colunas)."""
    print(C_CYAN + "╔" + "═" * (UI_WIDTH - 2) + "╗")
    print(f"║{title.center(UI_WIDTH - 2)}║")
    print("╚" + "═" * (UI_WIDTH - 2) + "╝" + C_RESET)

def print_divider():
    """Exibe uma linha divisória sólida em ciano (largura de UI_WIDTH colunas)."""
    print(C_CYAN + "─" * UI_WIDTH + C_RESET)

def mostrar_guia_dificuldade():
    """Exibe uma legenda explicativa sobre os níveis de dificuldade com base em acertos."""
    inner_width = UI_WIDTH - 2
    print(C_YELLOW + "┌" + "─" * inner_width + "┐")
    print("│" + " GUIA DE ESTIMATIVA DE DIFICULDADE (Baseado em acertos):".ljust(inner_width) + "│")
    print("│" + "   1 - Ótimo domínio (>85% de acertos em questões)".ljust(inner_width) + "│")
    print("│" + "   2 - Bom domínio (75% - 85% de acertos)".ljust(inner_width) + "│")
    print("│" + "   3 - Domínio médio (60% - 75% de acertos)".ljust(inner_width) + "│")
    print("│" + "   4 - Baixo rendimento (45% - 60% de acertos)".ljust(inner_width) + "│")
    print("│" + "   5 - Sem base ou assunto novo (<45% de acertos)".ljust(inner_width) + "│")
    print("└" + "─" * inner_width + "┘" + C_RESET)

def obter_input_float(prompt, min_val=None, max_val=None, default=None):
    """Lê e valida uma entrada decimal."""
    while True:
        try:
            entrada = input(prompt).strip()
            if not entrada and default is not None:
                return default
            val = float(entrada)
            if min_val is not None and val < min_val:
                print(f"{C_RED}Erro: O valor deve ser no mínimo {min_val}.{C_RESET}")
                continue
            if max_val is not None and val > max_val:
                print(f"{C_RED}Erro: O valor não deve ultrapassar {max_val}.{C_RESET}")
                continue
            return val
        except ValueError:
            print(f"{C_RED}Erro: Por favor, insira um número válido.{C_RESET}")

def obter_input_str(prompt, obrigatorio=True, default=None):
    """Lê e valida uma entrada de texto."""
    while True:
        entrada = input(prompt).strip()
        if not entrada:
            if default is not None:
                return default
            if not obrigatorio:
                return ""
            print(f"{C_RED}Erro: Este campo não pode ficar vazio.{C_RESET}")
            continue
        return entrada

def parse_tempo_input(entrada):
    """Interpreta formatos de tempo flexíveis como '1.5', '1:30', '90m' ou '90min'."""
    entrada = entrada.strip().lower()
    if not entrada:
        raise ValueError("Entrada vazia")
        
    # 1. Formato H:MM (ex: 1:30, 0:45)
    if ":" in entrada:
        partes = entrada.split(":")
        if len(partes) == 2:
            h = float(partes[0])
            m = float(partes[1])
            if m < 0 or m >= 60 or h < 0:
                raise ValueError("Minutos devem estar entre 0 e 59.")
            return h + m / 60.0
            
    # 2. Formato com h e m (ex: 1h30m, 1h 30min, 45m)
    if 'h' in entrada or 'm' in entrada:
        horas = 0.0
        minutos = 0.0
        
        match_h = re.search(r'(\d+(?:\.\d+)?)\s*h', entrada)
        if match_h:
            horas = float(match_h.group(1))
            
        match_m = re.search(r'(\d+(?:\.\d+)?)\s*m', entrada)
        if match_m:
            minutos = float(match_m.group(1))
            
        if 'h' not in entrada and 'm' in entrada:
            # Caso o usuário digite apenas minutos (ex: 45m ou 45min)
            match_so_m = re.match(r'^(\d+(?:\.\d+)?)\s*(?:m|min)', entrada)
            if match_so_m:
                return float(match_so_m.group(1)) / 60.0
                
        return horas + minutos / 60.0
        
    # 3. Decimal simples (ex: 1.5)
    return float(entrada)

def formatar_horas_minutos(horas_decimais):
    """Converte horas decimais em formato legível como 'Xh YYmin'."""
    if horas_decimais <= 0:
        return "0h 00min"
    horas = int(horas_decimais)
    minutos = round((horas_decimais - horas) * 60)
    if minutos == 60:
        horas += 1
        minutos = 0
    return f"{horas}h {minutos:02d}min"
