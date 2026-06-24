import os
import re
import shutil
from constants import (
    C_CYAN, C_GREEN, C_YELLOW, C_RED, C_MAGENTA, C_BLUE, C_BOLD, C_RESET
)

def obter_largura_ui():
    """Retorna a largura ideal da UI dinâmica com base no terminal atual (min 80, max 100)."""
    try:
        cols = shutil.get_terminal_size((80, 20)).columns
        return max(80, min(100, cols))
    except Exception:
        return 80

def clear_screen():
    """Limpa a tela do terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    """Exibe um cabeçalho estilizado com bordas duplas (largura dinâmica)."""
    width = obter_largura_ui()
    print(C_CYAN + "╔" + "═" * (width - 2) + "╗")
    print(f"║{title.center(width - 2)}║")
    print("╚" + "═" * (width - 2) + "╝" + C_RESET)

def print_divider():
    """Exibe uma linha divisória sólida em ciano (largura dinâmica)."""
    print(C_CYAN + "─" * obter_largura_ui() + C_RESET)

def mostrar_guia_dificuldade():
    """Exibe uma legenda explicativa sobre os níveis de dificuldade com base em acertos."""
    inner_width = obter_largura_ui() - 2
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
    """Interpreta formatos de tempo flexíveis como '1.5', '1:30', '1:30:12', '90m', '1h30m12s', etc."""
    entrada = entrada.strip().lower()
    if not entrada:
        raise ValueError("Entrada vazia")
        
    # 1. Formato com dois pontos (ex: 1:30:12 ou 1:30)
    if ":" in entrada:
        partes = entrada.split(":")
        if len(partes) == 3:
            h = float(partes[0])
            m = float(partes[1])
            s = float(partes[2])
            if h < 0 or m < 0 or m >= 60 or s < 0 or s >= 60:
                raise ValueError("Valores de horas/minutos/segundos inválidos.")
            return h + m / 60.0 + s / 3600.0
        elif len(partes) == 2:
            h = float(partes[0])
            m = float(partes[1])
            if h < 0 or m < 0 or m >= 60:
                raise ValueError("Minutos devem estar entre 0 e 59.")
            return h + m / 60.0
            
    # 2. Formato com sufixos (h, m, s)
    if any(char in entrada for char in ['h', 'm', 's']):
        horas = 0.0
        minutos = 0.0
        segundos = 0.0
        
        match_h = re.search(r'(\d+(?:\.\d+)?)\s*(?:h|hs|hora|horas)', entrada)
        if match_h:
            horas = float(match_h.group(1))
            
        match_m = re.search(r'(\d+(?:\.\d+)?)\s*(?:m|min|minuto|minutos)', entrada)
        if match_m:
            minutos = float(match_m.group(1))
            
        match_s = re.search(r'(\d+(?:\.\d+)?)\s*(?:s|seg|segundo|segundos)', entrada)
        if match_s:
            segundos = float(match_s.group(1))
            
        # Validar se conseguimos extrair alguma coisa válida
        if not match_h and not match_m and not match_s:
            raise ValueError("Não foi possível extrair tempo válido do formato com sufixos.")
            
        return horas + minutos / 60.0 + segundos / 3600.0
        
    # 3. Decimal simples (ex: 1.5)
    return float(entrada)

def formatar_horas_minutos(horas_decimais):
    """Converte horas decimais em formato legível como 'Xh YYm ZZs', 'YYm ZZs' ou 'ZZs'."""
    if horas_decimais <= 0:
        return "0s"
        
    total_segundos = round(horas_decimais * 3600)
    if total_segundos <= 0:
        return "0s"
        
    horas = total_segundos // 3600
    minutos = (total_segundos % 3600) // 60
    segundos = total_segundos % 60
    
    partes = []
    if horas > 0:
        partes.append(f"{horas}h")
    if minutos > 0:
        partes.append(f"{minutos}m")
    if segundos > 0:
        partes.append(f"{segundos}s")
        
    if not partes:
        return "0s"
        
    return " ".join(partes)
