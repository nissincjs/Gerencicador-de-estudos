import os
import sys

# Garante que os testes importem os módulos da raiz do projeto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Bloqueia qualquer chamada real ao Supabase durante os testes
import supabase_client
supabase_client.supabase = None
supabase_client.esta_configurado = lambda: False
supabase_client.obter_id_usuario = lambda: None
