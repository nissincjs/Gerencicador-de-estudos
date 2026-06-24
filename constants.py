import sys
import os

# Habilita codificação UTF-8 no stdout para evitar erros de caractere no Windows CMD/PowerShell
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Habilita suporte a cores ANSI no console do Windows se necessário
if os.name == 'nt':
    os.system('')

# Constantes de cores ANSI para um CLI moderno e bonito
C_CYAN = "\033[96m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_RED = "\033[91m"
C_MAGENTA = "\033[95m"
C_BLUE = "\033[94m"
C_BOLD = "\033[1m"
C_RESET = "\033[0m"

DB_FILE = "ciclo_estudos.json"
