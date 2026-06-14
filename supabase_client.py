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

def garantir_perfil_criado(user_id: str, email: str):
    """Garante que o perfil do usuário exista na tabela perfis_usuario, criando-o se necessário."""
    if not esta_configurado():
        return
    try:
        res = supabase.table("perfis_usuario").select("*").eq("user_id", user_id).execute()
        if not res.data:
            import random
            import string
            
            tentativas = 0
            while tentativas < 10:
                code_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
                codigo = f"ST-{code_suffix}"
                
                check_res = supabase.table("perfis_usuario").select("codigo_convite").eq("codigo_convite", codigo).execute()
                if not check_res.data:
                    supabase.table("perfis_usuario").insert({
                        "user_id": user_id,
                        "email": email,
                        "codigo_convite": codigo
                    }).execute()
                    break
                tentativas += 1
    except Exception:
        pass

def obter_perfil() -> dict:
    """Retorna o perfil do usuário logado na tabela perfis_usuario."""
    if not esta_configurado():
        return None
    user_id = obter_id_usuario()
    if not user_id:
        return None
    try:
        res = supabase.table("perfis_usuario").select("*").eq("user_id", user_id).execute()
        if res.data:
            return res.data[0]
    except Exception:
        pass
    return None

def vincular_parceiro(codigo_convite: str):
    """Vincula um parceiro de estudos utilizando o código de convite."""
    if not esta_configurado():
        raise Exception("Supabase não configurado.")
    
    current_user_id = obter_id_usuario()
    if not current_user_id:
        raise Exception("Usuário não autenticado.")
        
    # Busca o perfil alvo
    res = supabase.table("perfis_usuario").select("*").eq("codigo_convite", codigo_convite.strip().upper()).execute()
    if not res.data:
        raise Exception("Código de convite inválido ou não encontrado.")
        
    alvo = res.data[0]
    alvo_user_id = alvo["user_id"]
    
    if alvo_user_id == current_user_id:
        raise Exception("Você não pode vincular seu próprio código!")
        
    # Busca perfil atual
    res_atual = supabase.table("perfis_usuario").select("*").eq("user_id", current_user_id).execute()
    
    if res_atual.data:
        perfil_atual = res_atual.data[0]
        # Se o parceiro já me vinculou, já estamos vinculados mutuamente no banco. Retorna com sucesso kkk
        if perfil_atual.get("parceiro_id") == alvo_user_id:
            return
        if perfil_atual.get("parceiro_id"):
            raise Exception("Você já possui um parceiro de estudos. Desvincule-o primeiro.")
            
    if alvo.get("parceiro_id") and alvo.get("parceiro_id") != current_user_id:
        raise Exception("Este usuário já possui um parceiro de estudos.")
        
    # Vincula mutuamente
    try:
        supabase.table("perfis_usuario").update({"parceiro_id": alvo_user_id}).eq("user_id", current_user_id).execute()
        supabase.table("perfis_usuario").update({"parceiro_id": current_user_id}).eq("user_id", alvo_user_id).execute()
    except Exception as e:
        raise Exception(f"Erro ao salvar vínculo: {e}")

def desvincular_parceiro():
    """Remove o vínculo mútuo entre o usuário atual e seu parceiro."""
    if not esta_configurado():
        return
    current_user_id = obter_id_usuario()
    if not current_user_id:
        return
    try:
        perfil = obter_perfil()
        if perfil and perfil.get("parceiro_id"):
            parceiro_id = perfil["parceiro_id"]
            # Desvincula ambos
            supabase.table("perfis_usuario").update({"parceiro_id": None}).eq("user_id", current_user_id).execute()
            supabase.table("perfis_usuario").update({"parceiro_id": None}).eq("user_id", parceiro_id).execute()
    except Exception:
        pass

def obter_perfil_por_id(user_id: str) -> dict:
    """Busca um perfil específico pelo user_id."""
    if not esta_configurado() or not user_id:
        return None
    try:
        res = supabase.table("perfis_usuario").select("*").eq("user_id", user_id).execute()
        if res.data:
            return res.data[0]
    except Exception:
        pass
    return None

def baixar_dados_parceiro(parceiro_id: str) -> dict:
    """Busca dados de progresso do parceiro de estudos."""
    if not esta_configurado() or not parceiro_id:
        return None
    try:
        response = supabase.table("ciclos_usuario").select("dados").eq("user_id", parceiro_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0].get("dados")
    except Exception:
        pass
    return None



