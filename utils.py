import os
import re
import shutil
from constants import (
    C_CYAN, C_GREEN, C_YELLOW, C_RED, C_MAGENTA, C_BLUE, C_BOLD, C_RESET
)

def obter_largura_ui(largura_max=115):
    """Retorna a largura ideal da UI dinâmica com base no terminal atual (min 80)."""
    try:
        cols = shutil.get_terminal_size((80, 20)).columns
        limite_superior = largura_max if largura_max is not None else cols - 4
        return max(80, min(limite_superior, cols - 4))
    except Exception:
        return 80

_largura_atual = 80
_largura_manual = False
_ultimo_ajuste_zoom = 0

def atualizar_largura_dinamica():
    global _largura_atual
    if not _largura_manual:
        try:
            cols = shutil.get_terminal_size((80, 20)).columns
            # Limit the default width of menus/headers to 115 to occupy a larger area
            _largura_atual = max(80, min(115, cols - 4))
        except Exception:
            _largura_atual = 80

def obter_margem_esquerda(largura_conteudo=None):
    """Retorna a margem esquerda (espaços em branco) para centralizar um conteúdo no terminal."""
    if largura_conteudo is None:
        atualizar_largura_dinamica()
        largura_conteudo = _largura_atual
    try:
        cols = shutil.get_terminal_size((80, 20)).columns
        if cols > largura_conteudo:
            return " " * ((cols - largura_conteudo) // 2)
    except Exception:
        pass
    return ""

def set_largura_atual(largura):
    global _largura_atual, _largura_manual
    _largura_atual = largura
    _largura_manual = True

def reset_largura_atual():
    global _largura_atual, _largura_manual
    _largura_atual = 80
    _largura_manual = False

def print_override(*args, **kwargs):
    atualizar_largura_dinamica()
    margin = obter_margem_esquerda(_largura_atual)
    import builtins
    if args:
        val = str(args[0])
        if "\n" in val:
            lines = val.split("\n")
            val = "\n".join((margin + line if line.strip() or idx == 0 else line) for idx, line in enumerate(lines))
            new_args = (val,) + args[1:]
        else:
            new_args = (margin + val,) + args[1:]
        builtins.print(*new_args, **kwargs)
    else:
        builtins.print(margin, **kwargs)

def _formatar_prompt(prompt, margin):
    if not prompt:
        return margin
    val = str(prompt)
    if "\n" in val:
        lines = val.split("\n")
        return "\n".join((margin + line if line.strip() or idx == 0 else line) for idx, line in enumerate(lines))
    else:
        return margin + val

def input_override(prompt=""):
    atualizar_largura_dinamica()
    margin = obter_margem_esquerda(_largura_atual)
    import builtins
    return builtins.input(_formatar_prompt(prompt, margin))

def print_l(texto, largura_ref=None):
    """Imprime uma linha de texto adicionando a margem esquerda para centralização."""
    atualizar_largura_dinamica()
    if largura_ref is None:
        largura_ref = _largura_atual
    margin = obter_margem_esquerda(largura_ref)
    print(margin + texto)

def input_l(prompt, largura_ref=None):
    """Lê do input padrão com a margem esquerda apropriada para alinhamento."""
    atualizar_largura_dinamica()
    if largura_ref is None:
        largura_ref = _largura_atual
    margin = obter_margem_esquerda(largura_ref)
    return input(margin + prompt)

def clear_screen():
    """Limpa a tela do terminal e ajusta o zoom automaticamente se necessário."""
    auto_ajustar_zoom()
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title, width=None):
    """Exibe um cabeçalho estilizado com bordas duplas (largura fixa ou dinâmica, centralizado)."""
    atualizar_largura_dinamica()
    if width is None:
        width = _largura_atual
    width = max(80, width)
    margin = obter_margem_esquerda(width)
    import builtins
    builtins.print(margin + C_CYAN + "╔" + "═" * (width - 2) + "╗")
    builtins.print(margin + f"║{title.center(width - 2)}║")
    builtins.print(margin + "╚" + "═" * (width - 2) + "╝" + C_RESET)

def print_divider(width=None):
    """Exibe uma linha divisória sólida em ciano (largura dinâmica ou fixa, centralizada)."""
    atualizar_largura_dinamica()
    if width is None:
        width = _largura_atual
    width = max(80, width)
    margin = obter_margem_esquerda(width)
    import builtins
    builtins.print(margin + C_CYAN + "─" * width + C_RESET)

def mostrar_guia_dificuldade(largura_ref=None):
    """Exibe uma legenda explicativa sobre os níveis de dificuldade com base em acertos (centralizada)."""
    atualizar_largura_dinamica()
    if largura_ref is None:
        largura_ref = _largura_atual
    margin = obter_margem_esquerda(largura_ref)
    inner_width = largura_ref - 2
    import builtins
    builtins.print(margin + C_YELLOW + "┌" + "─" * inner_width + "┐")
    builtins.print(margin + "│" + " GUIA DE ESTIMATIVA DE DIFICULDADE (Baseado em acertos):".ljust(inner_width) + "│")
    builtins.print(margin + "│" + "   1 - Ótimo domínio (>85% de acertos em questões)".ljust(inner_width) + "│")
    builtins.print(margin + "│" + "   2 - Bom domínio (75% - 85% de acertos)".ljust(inner_width) + "│")
    builtins.print(margin + "│" + "   3 - Domínio médio (60% - 75% de acertos)".ljust(inner_width) + "│")
    builtins.print(margin + "│" + "   4 - Baixo rendimento (45% - 60% de acertos)".ljust(inner_width) + "│")
    builtins.print(margin + "│" + "   5 - Sem base ou assunto novo (<45% de acertos)".ljust(inner_width) + "│")
    builtins.print(margin + "└" + "─" * inner_width + "┘" + C_RESET)

def obter_input_float(prompt, min_val=None, max_val=None, default=None, largura_ref=None):
    """Lê e valida uma entrada decimal (alinhada à margem esquerda)."""
    atualizar_largura_dinamica()
    if largura_ref is None:
        largura_ref = _largura_atual
    margin = obter_margem_esquerda(largura_ref)
    import builtins
    while True:
        try:
            entrada = builtins.input(_formatar_prompt(prompt, margin)).strip()
            if not entrada and default is not None:
                return default
            val = float(entrada)
            if min_val is not None and val < min_val:
                builtins.print(margin + f"{C_RED}Erro: O valor deve ser no mínimo {min_val}.{C_RESET}")
                continue
            if max_val is not None and val > max_val:
                builtins.print(margin + f"{C_RED}Erro: O valor não deve ultrapassar {max_val}.{C_RESET}")
                continue
            return val
        except ValueError:
            builtins.print(margin + f"{C_RED}Erro: Por favor, insira um número válido.{C_RESET}")

def obter_input_str(prompt, obrigatorio=True, default=None, largura_ref=None):
    """Lê e valida uma entrada de texto (alinhada à margem esquerda)."""
    atualizar_largura_dinamica()
    if largura_ref is None:
        largura_ref = _largura_atual
    margin = obter_margem_esquerda(largura_ref)
    import builtins
    while True:
        entrada = builtins.input(_formatar_prompt(prompt, margin)).strip()
        if not entrada:
            if default is not None:
                return default
            if not obrigatorio:
                return ""
            builtins.print(margin + f"{C_RED}Erro: Este campo não pode ficar vazio.{C_RESET}")
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

def ajustar_zoom_console(passos=1):
    """Ajusta o nível de zoom do terminal enviando atalhos de teclado (Ctrl + +) no Windows."""
    if os.name != 'nt':
        return
    try:
        import ctypes
        import time
        user32 = ctypes.windll.user32
        
        VK_CONTROL = 0x11
        VK_OEM_PLUS = 0xBB
        KEYEVENTF_KEYUP = 0x0002
        
        for _ in range(passos):
            user32.keybd_event(VK_CONTROL, 0, 0, 0)
            user32.keybd_event(VK_OEM_PLUS, 0, 0, 0)
            user32.keybd_event(VK_OEM_PLUS, 0, KEYEVENTF_KEYUP, 0)
            user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
            time.sleep(0.05)
    except Exception:
        pass

def ajustar_zoom_console_out(passos=1):
    """Diminui o nível de zoom do terminal enviando atalhos de teclado (Ctrl + -) no Windows."""
    if os.name != 'nt':
        return
    try:
        import ctypes
        import time
        user32 = ctypes.windll.user32
        
        VK_CONTROL = 0x11
        VK_OEM_MINUS = 0xBD
        KEYEVENTF_KEYUP = 0x0002
        
        for _ in range(passos):
            user32.keybd_event(VK_CONTROL, 0, 0, 0)
            user32.keybd_event(VK_OEM_MINUS, 0, 0, 0)
            user32.keybd_event(VK_OEM_MINUS, 0, KEYEVENTF_KEYUP, 0)
            user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
            time.sleep(0.05)
    except Exception:
        pass

def auto_ajustar_zoom():
    """Detecta se o terminal está muito largo ou muito estreito e ajusta o zoom automaticamente."""
    if os.name != 'nt':
        return
    global _ultimo_ajuste_zoom
    import time
    agora = time.time()
    
    # Evita reajustes de zoom muito frequentes (intervalo mínimo de 1.2 segundos)
    if agora - _ultimo_ajuste_zoom < 1.2:
        return
        
    try:
        cols = shutil.get_terminal_size((80, 20)).columns
        
        # Feedback loop para manter a largura do terminal ideal entre 75 e 110 colunas
        if cols > 160:
            ajustar_zoom_console(3)
            _ultimo_ajuste_zoom = agora
            time.sleep(0.15)
        elif cols > 135:
            ajustar_zoom_console(2)
            _ultimo_ajuste_zoom = agora
            time.sleep(0.15)
        elif cols > 110:
            ajustar_zoom_console(1)
            _ultimo_ajuste_zoom = agora
            time.sleep(0.15)
        elif cols < 75:
            ajustar_zoom_console_out(1)
            _ultimo_ajuste_zoom = agora
            time.sleep(0.15)
    except Exception:
        pass
