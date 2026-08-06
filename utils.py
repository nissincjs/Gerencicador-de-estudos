import os
import shutil
from constants import (
    C_CYAN, C_GREEN, C_YELLOW, C_RED, C_MAGENTA, C_BLUE, C_BOLD, C_RESET
)
from calculo import parse_tempo_input, formatar_horas_minutos, parse_data_hora_input

def obter_largura_ui(largura_max=115):
    """Retorna a largura ideal da UI dinâmica com base no terminal atual."""
    try:
        cols = shutil.get_terminal_size((80, 20)).columns
        limite_superior = largura_max if largura_max is not None else cols - 4
        return max(20, min(limite_superior, cols - 4))
    except Exception:
        return 70

_largura_atual = 70
_largura_manual = False
_ultimo_ajuste_zoom = 0
_margem_atual = ""
_tamanho_terminal_ultimo_ajuste = None

def atualizar_largura_dinamica():
    global _largura_atual, _margem_atual
    if not _largura_manual:
        try:
            cols = shutil.get_terminal_size((80, 20)).columns
            # Limita a largura padrão dos menus/cabeçalhos a 115, mas também
            # se adapta a terminais estreitos (ex.: Termux no celular em retrato),
            # em vez de forçar 70 colunas e estourar a tela.
            _largura_atual = max(20, min(115, cols - 4))
            
            # Recalculate margins
            if cols > _largura_atual:
                _margem_atual = " " * ((cols - _largura_atual) // 2)
            else:
                _margem_atual = ""
        except Exception:
            _largura_atual = 70
            _margem_atual = ""
    else:
        try:
            cols = shutil.get_terminal_size((80, 20)).columns
            if cols > _largura_atual:
                _margem_atual = " " * ((cols - _largura_atual) // 2)
            else:
                _margem_atual = ""
        except Exception:
            _margem_atual = ""

def obter_margem_esquerda(largura_conteudo=None):
    """Retorna a margem esquerda (espaços em branco) para centralizar um conteúdo no terminal."""
    if largura_conteudo is None:
        atualizar_largura_dinamica()
        return _margem_atual
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
    atualizar_largura_dinamica()

def reset_largura_atual():
    global _largura_atual, _largura_manual
    _largura_atual = 70
    _largura_manual = False
    atualizar_largura_dinamica()

def print_override(*args, **kwargs):
    # Use cached margin to avoid flicker and dynamic layout changes mid-draw
    margin = _margem_atual
    import builtins
    if args:
        val = str(args[0])
        is_r = val.startswith("\r")
        if is_r:
            val = val[1:]
            
        if "\n" in val:
            lines = val.split("\n")
            val = "\n".join((margin + line if line.strip() or idx == 0 else line) for idx, line in enumerate(lines))
        else:
            val = margin + val
            
        if is_r:
            val = "\r" + val
            
        new_args = (val,) + args[1:]
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
    margin = _margem_atual
    import builtins
    return builtins.input(_formatar_prompt(prompt, margin))

def print_l(texto, largura_ref=None):
    """Imprime uma linha de texto adicionando a margem esquerda para centralização."""
    if largura_ref is None:
        margin = _margem_atual
    else:
        margin = obter_margem_esquerda(largura_ref)
    print(margin + texto)

def input_l(prompt, largura_ref=None):
    """Lê do input padrão com a margem esquerda apropriada para alinhamento."""
    if largura_ref is None:
        margin = _margem_atual
    else:
        margin = obter_margem_esquerda(largura_ref)
    return input(margin + prompt)

def clear_screen():
    """Limpa a tela do terminal e ajusta o zoom automaticamente se necessário."""
    auto_ajustar_zoom()
    atualizar_largura_dinamica() # Refresh terminal layout dimensions at start of frame
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title, width=None):
    """Exibe um cabeçalho estilizado com bordas duplas (largura fixa ou dinâmica, centralizado)."""
    if width is None:
        width = _largura_atual
        margin = _margem_atual
    else:
        width = max(70, width)
        margin = obter_margem_esquerda(width)
    import builtins
    # Em terminais estreitos, encurta o título para não passar das bordas
    largura_interna = max(2, width - 2)
    if len(title) > largura_interna:
        title = title[:max(1, largura_interna - 1)] + "…"
    builtins.print(margin + C_CYAN + "╔" + "═" * (width - 2) + "╗")
    builtins.print(margin + C_CYAN + f"║{title.center(width - 2)}║")
    builtins.print(margin + C_CYAN + "╚" + "═" * (width - 2) + "╝" + C_RESET)

def print_divider(width=None):
    """Exibe uma linha divisória sólida em ciano (largura dinâmica ou fixa, centralizada)."""
    if width is None:
        width = _largura_atual
        margin = _margem_atual
    else:
        width = max(70, width)
        margin = obter_margem_esquerda(width)
    import builtins
    builtins.print(margin + C_CYAN + "─" * width + C_RESET)

def mostrar_guia_dificuldade(largura_ref=None):
    """Exibe uma legenda explicativa sobre os níveis de dificuldade com base em acertos (centralizada)."""
    if largura_ref is None:
        largura_ref = _largura_atual
        margin = _margem_atual
    else:
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
    if largura_ref is None:
        margin = _margem_atual
    else:
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
    if largura_ref is None:
        margin = _margem_atual
    else:
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

def ajustar_zoom_console(passos=1):
    """Ajusta o nível de zoom do terminal enviando atalhos de teclado (Ctrl + + / Ctrl + Shift + +)."""
    if os.name == 'nt':
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
    elif os.name == 'posix':
        import subprocess
        import time
        if shutil.which('xdotool'):
            try:
                for _ in range(passos):
                    # No Linux (Cinnamon, GNOME, MATE, XFCE), o atalho padrão de zoom-in é Ctrl + Shift + +
                    subprocess.run(["xdotool", "key", "ctrl+shift+plus"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    time.sleep(0.05)
            except Exception:
                pass

def ajustar_zoom_console_out(passos=1):
    """Diminui o nível de zoom do terminal enviando atalhos de teclado (Ctrl + -)."""
    if os.name == 'nt':
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
    elif os.name == 'posix':
        import subprocess
        import time
        if shutil.which('xdotool'):
            try:
                for _ in range(passos):
                    # No Linux, o atalho padrão de zoom-out é Ctrl + -
                    subprocess.run(["xdotool", "key", "ctrl+minus"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    time.sleep(0.05)
            except Exception:
                pass

def auto_ajustar_zoom():
    """Detecta se o terminal está muito largo ou muito estreito e ajusta o zoom automaticamente."""
    # Executa apenas se for Windows OU se for Linux com xdotool disponível
    if os.name != 'nt' and not (os.name == 'posix' and shutil.which('xdotool')):
        return
        
    global _tamanho_terminal_ultimo_ajuste, _ultimo_ajuste_zoom
    import time
    
    try:
        size = shutil.get_terminal_size((80, 20))
        cols, rows = size.columns, size.lines
    except Exception:
        return

    # Se o tamanho atual for igual ao último após o ajuste, não há necessidade de reajustar
    if _tamanho_terminal_ultimo_ajuste == (cols, rows):
        return

    agora = time.time()
    # Evita reajustes de zoom se tiver ocorrido um ajuste há menos de 1.0 segundo (evita loops rápidos na inicialização/redimensionamento manual)
    if agora - _ultimo_ajuste_zoom < 1.0:
        return
        
    # Feedback loop para manter a largura do terminal ideal entre 75 e 110 colunas
    max_tentativas = 8
    tentativa = 0
    tamanho_anterior = (cols, rows)
    
    while tentativa < max_tentativas:
        if 75 <= cols <= 110:
            break
            
        # Ajusta dependendo da distância do tamanho ideal
        if cols > 160:
            ajustar_zoom_console(2)
        elif cols > 110:
            ajustar_zoom_console(1)
        elif cols < 75:
            ajustar_zoom_console_out(1)
            
        # Espera um curto período para a janela do console atualizar a fonte e o grid de caracteres
        time.sleep(0.08)
        
        try:
            size = shutil.get_terminal_size((80, 20))
            cols, rows = size.columns, size.lines
        except Exception:
            break
            
        # Se o tamanho de caracteres não mudou após o comando de zoom, significa que
        # atingimos o limite de zoom da janela ou o console não responde a atalhos.
        if (cols, rows) == tamanho_anterior:
            break
            
        tamanho_anterior = (cols, rows)
        tentativa += 1

    # Registra o estado atual estável do terminal
    _tamanho_terminal_ultimo_ajuste = (cols, rows)
    _ultimo_ajuste_zoom = time.time()

