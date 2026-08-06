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

def baixar_dados_membro(membro_id: str) -> dict:
    """Busca dados de progresso de um membro do grupo de estudos."""
    if not esta_configurado() or not membro_id:
        return None
    try:
        response = supabase.table("ciclos_usuario").select("dados").eq("user_id", membro_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0].get("dados")
    except Exception:
        pass
    return None

def obter_grupo_do_usuario() -> dict:
    """Retorna o grupo do usuário atual (info + ids dos membros) ou None."""
    if not esta_configurado():
        return None
    current_user_id = obter_id_usuario()
    if not current_user_id:
        return None
    try:
        res = supabase.table("membros_grupo").select("grupo_id").eq("user_id", current_user_id).execute()
        if not res.data:
            return None
        grupo_id = res.data[0]["grupo_id"]

        grupo_res = supabase.table("grupos").select("*").eq("id", grupo_id).execute()
        if not grupo_res.data:
            return None
        grupo = grupo_res.data[0]

        membros_res = supabase.table("membros_grupo").select("user_id").eq("grupo_id", grupo_id).execute()
        membros_ids = [m["user_id"] for m in membros_res.data] if membros_res.data else []

        if grupo["criador_id"] not in membros_ids:
            membros_ids.append(grupo["criador_id"])

        return {
            "grupo": grupo,
            "membros_ids": membros_ids
        }
    except Exception:
        return None

def listar_membros_grupo() -> list:
    """Retorna a lista de perfis dos membros do grupo do usuário atual."""
    info = obter_grupo_do_usuario()
    if not info:
        return []
    membros = []
    for uid in info["membros_ids"]:
        perfil = obter_perfil_por_id(uid)
        if perfil:
            membros.append(perfil)
    return membros

def criar_grupo() -> str:
    """Cria um novo grupo de estudos e torna o usuário atual o admin (criador).
    Retorna o código de convite gerado (GR-XXXXXX)."""
    if not esta_configurado():
        raise Exception("Supabase não configurado.")
    current_user_id = obter_id_usuario()
    if not current_user_id:
        raise Exception("Usuário não autenticado.")

    if obter_grupo_do_usuario():
        raise Exception("Você já está em um grupo de estudos.")

    import random
    import string

    codigo = None
    for _ in range(10):
        code_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        codigo = f"GR-{code_suffix}"
        check = supabase.table("grupos").select("codigo_convite").eq("codigo_convite", codigo).execute()
        if not check.data:
            break
    else:
        raise Exception("Não foi possível gerar um código único. Tente novamente.")

    try:
        res = supabase.table("grupos").insert({
            "codigo_convite": codigo,
            "criador_id": current_user_id
        }).execute()
        grupo_id = res.data[0]["id"]
        supabase.table("membros_grupo").insert({
            "grupo_id": grupo_id,
            "user_id": current_user_id
        }).execute()
    except Exception as e:
        raise Exception(f"Erro ao criar grupo: {e}")

    return codigo

def entrar_grupo(codigo_convite: str):
    """Faz o usuário atual entrar em um grupo existente pelo código de convite."""
    if not esta_configurado():
        raise Exception("Supabase não configurado.")
    current_user_id = obter_id_usuario()
    if not current_user_id:
        raise Exception("Usuário não autenticado.")

    if obter_grupo_do_usuario():
        raise Exception("Você já está em um grupo de estudos. Saia dele primeiro.")

    codigo = codigo_convite.strip().upper()
    res = supabase.table("grupos").select("*").eq("codigo_convite", codigo).execute()
    if not res.data:
        raise Exception("Código de convite inválido ou não encontrado.")

    grupo = res.data[0]
    grupo_id = grupo["id"]

    if grupo["criador_id"] == current_user_id:
        raise Exception("Você já é o criador deste grupo.")

    try:
        supabase.table("membros_grupo").insert({
            "grupo_id": grupo_id,
            "user_id": current_user_id
        }).execute()
    except Exception:
        raise Exception("Não foi possível entrar no grupo. Você pode já estar em outro grupo.")

def sair_grupo():
    """Remove o usuário atual do grupo. Se for o admin, transfere a liderança
    para outro membro ou dissolve o grupo quando for o último membro."""
    if not esta_configurado():
        return
    current_user_id = obter_id_usuario()
    if not current_user_id:
        return
    try:
        info = obter_grupo_do_usuario()
        if not info:
            return
        grupo = info["grupo"]
        grupo_id = grupo["id"]

        if grupo["criador_id"] == current_user_id:
            outros = [uid for uid in info["membros_ids"] if uid != current_user_id]
            if outros:
                novo_admin = outros[0]
                supabase.table("grupos").update({"criador_id": novo_admin}).eq("id", grupo_id).execute()
            else:
                dissolver_grupo()
                return

        supabase.table("membros_grupo").delete().eq("user_id", current_user_id).execute()
    except Exception:
        pass

def remover_membro(user_id: str):
    """Admin remove um membro específico do grupo."""
    if not esta_configurado():
        raise Exception("Supabase não configurado.")
    current_user_id = obter_id_usuario()
    if not current_user_id:
        raise Exception("Usuário não autenticado.")

    info = obter_grupo_do_usuario()
    if not info:
        raise Exception("Você não está em um grupo de estudos.")
    grupo = info["grupo"]

    if grupo["criador_id"] != current_user_id:
        raise Exception("Somente o administrador do grupo pode remover membros.")

    if user_id == current_user_id:
        raise Exception("Você não pode remover a si mesmo. Use a opção 'Sair do Grupo'.")

    try:
        supabase.table("membros_grupo").delete().eq("user_id", user_id).execute()
    except Exception as e:
        raise Exception(f"Erro ao remover membro: {e}")

def dissolver_grupo():
    """Admin dissolve o grupo inteiro, removendo todos os membros."""
    if not esta_configurado():
        return
    current_user_id = obter_id_usuario()
    if not current_user_id:
        return
    try:
        info = obter_grupo_do_usuario()
        if not info:
            return
        grupo = info["grupo"]
        if grupo["criador_id"] != current_user_id:
            raise Exception("Somente o administrador do grupo pode dissolvê-lo.")
        supabase.table("grupos").delete().eq("id", grupo["id"]).execute()
    except Exception:
        pass



