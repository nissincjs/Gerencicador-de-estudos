import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = None

if SUPABASE_URL and SUPABASE_KEY and not (SUPABASE_URL.startswith("https://sua-url-do-supabase") or SUPABASE_KEY.startswith("sua-anon-key")):
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        pass

import json

SESSION_FILE = ".session.json"

def esta_configurado() -> bool:
    """Verifica se o Supabase está configurado corretamente no .env."""
    return supabase is not None

def salvar_sessao(session):
    """Salva os tokens da sessão atual em um arquivo JSON local."""
    if not session:
        return
    try:
        dados_sessao = {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token
        }
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(dados_sessao, f)
    except Exception:
        pass

def limpar_sessao():
    """Remove o arquivo de sessão local e desloga o usuário."""
    if os.path.exists(SESSION_FILE):
        try:
            os.remove(SESSION_FILE)
        except Exception:
            pass
    if esta_configurado():
        try:
            supabase.auth.sign_out()
        except Exception:
            pass

def recuperar_sessao_salva():
    """Tenta restaurar a sessão do usuário a partir dos tokens salvos localmente."""
    if not esta_configurado():
        return None
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                dados_sessao = json.load(f)
            access_token = dados_sessao.get("access_token")
            refresh_token = dados_sessao.get("refresh_token")
            if access_token and refresh_token:
                response = supabase.auth.set_session(access_token=access_token, refresh_token=refresh_token)
                return response.user
        except Exception:
            limpar_sessao()
    return None

def fazer_login(email, password):
    """Realiza o login com email e senha no Supabase."""
    if not esta_configurado():
        raise Exception("Supabase não está configurado. Verifique o arquivo .env.")
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if response.session:
            salvar_sessao(response.session)
        return response.user
    except Exception as e:
        # Extrai mensagem legível de erro, caso exista
        msg = str(e)
        if "Invalid login credentials" in msg:
            raise Exception("E-mail ou senha incorretos.")
        elif "Email not confirmed" in msg:
            raise Exception("E-mail ainda não foi confirmado. Verifique sua caixa de entrada.")
        raise Exception(msg)

def fazer_cadastro(email, password):
    """Realiza o cadastro de um novo usuário no Supabase."""
    if not esta_configurado():
        raise Exception("Supabase não está configurado. Verifique o arquivo .env.")
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        if response.session:
            salvar_sessao(response.session)
        return response.user
    except Exception as e:
        raise Exception(str(e))

def obter_id_usuario() -> str:
    """Retorna o ID do usuário atualmente autenticado ou None."""
    if not esta_configurado():
        return None
    try:
        res = supabase.auth.get_user()
        if res and res.user:
            return res.user.id
    except Exception:
        pass
    return None

def enviar_dados_nuvem(dados: dict) -> bool:
    """Envia os dados do ciclo de estudos para a tabela ciclos_usuario no Supabase."""
    if not esta_configurado():
        return False
    user_id = obter_id_usuario()
    if not user_id:
        return False
    try:
        dados_upload = dados.copy()
        if "sync_pending" in dados_upload:
            del dados_upload["sync_pending"]
        
        from datetime import datetime, timezone
        supabase.table("ciclos_usuario").upsert({
            "user_id": user_id,
            "dados": dados_upload,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }).execute()
        return True
    except Exception:
        return False

def baixar_dados_nuvem() -> dict:
    """Busca os dados salvos na nuvem para o usuário logado."""
    if not esta_configurado():
        return None
    user_id = obter_id_usuario()
    if not user_id:
        return None
    try:
        response = supabase.table("ciclos_usuario").select("dados").eq("user_id", user_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0].get("dados")
    except Exception:
        pass
    return None


