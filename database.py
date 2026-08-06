import os
import json
from datetime import datetime, timezone
from constants import DB_FILE, C_RED, C_RESET, C_YELLOW, C_GREEN, C_BOLD
from utils import print_override as print, input_override as input

MAX_BACKUPS = 3
BACKUP_SUFIXO = ".backup"
TMP_SUFIXO = ".tmp"

def _caminho_backup(indice):
    """Retorna o caminho de um backup rotativo (1 = mais recente)."""
    return f"{DB_FILE}{BACKUP_SUFIXO}{indice}"

def _escrever_json_atomicamente(dados, pre_commit=None):
    """Grava os dados num arquivo temporário e move de forma atômica.
    Se algo falhar, o arquivo atual permanece intacto.
    pre_commit: callback opcional executado entre a escrita do .tmp e a troca final."""
    tmp = f"{DB_FILE}{TMP_SUFIXO}"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        if pre_commit:
            pre_commit()
        os.replace(tmp, DB_FILE)
    except Exception:
        try:
            os.remove(tmp)
        except Exception:
            pass
        raise

def _rotacionar_backups():
    """Desloca os backups antes de gravar um novo estado:
    backup2→backup3, backup1→backup2, atual→backup1."""
    for i in range(MAX_BACKUPS, 1, -1):
        origem = _caminho_backup(i - 1)
        destino = _caminho_backup(i)
        if os.path.exists(origem):
            os.replace(origem, destino)
    if os.path.exists(DB_FILE):
        os.replace(DB_FILE, _caminho_backup(1))

def _carregar_json(caminho):
    """Carrega e valida o JSON de um arquivo. Retorna None se inválido."""
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
        if isinstance(dados, dict):
            return dados
    except Exception:
        pass
    return None

def obter_fator(m):
    """Calcula o fator de prioridade da matéria."""
    qp = m.get("questoes_prova", 10.0)
    pq = m.get("peso_questao", 1.0)
    dif = m.get("dificuldade", 1.0)
    return qp * pq * dif

def novo_ciclo() -> dict:
    """Retorna um ciclo de estudos vazio (novo usuário / sem dados)."""
    return {
        "horas_semanais": 0.0,
        "limite_revisoes_diarias": 10,
        "data_inicio_ciclo": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "materias": [],
        "progresso_atual": {},
        "historico_ciclos": [],
        "historico_sessoes": [],
        "revisoes": [],
        "justificativas": [],
        "atualizacao_automatica": True
    }

def _processar_migracoes(dados):
    """Aplica validações e migrações de dados de versões antigas. Retorna o dict pronto."""
    if "horas_semanais" not in dados:
        dados["horas_semanais"] = 0.0
    if "materias" not in dados:
        dados["materias"] = []
    if "data_inicio_ciclo" not in dados:
        dados["data_inicio_ciclo"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    if "progresso_atual" not in dados:
        dados["progresso_atual"] = {}
    if "historico_ciclos" not in dados:
        dados["historico_ciclos"] = []
    if "historico_sessoes" not in dados:
        dados["historico_sessoes"] = []
    if "revisoes" not in dados:
        dados["revisoes"] = []
    if "limite_revisoes_diarias" not in dados:
        dados["limite_revisoes_diarias"] = 10
    if "justificativas" not in dados:
        dados["justificativas"] = []
    if "atualizacao_automatica" not in dados:
        dados["atualizacao_automatica"] = True

    migrou = False
    # Migração de dados do formato antigo para o formato estratégico (sem aulas)
    for m in dados["materias"]:
        if "aulas" in m:
            del m["aulas"]
            migrou = True
        if "questoes_prova" not in m:
            m["questoes_prova"] = 10.0
            migrou = True
        if "peso_questao" not in m:
            m["peso_questao"] = m.get("peso", 1.0)
            migrou = True
        if "peso" in m:
            del m["peso"]
            migrou = True

    for r in dados.get("revisoes", []):
        if "ease_factor" not in r:
            r["ease_factor"] = 2.5
            migrou = True
        if "historico_acertos" not in r:
            r["historico_acertos"] = [r["acertos_pct"]] if r.get("acertos_pct") is not None else []
            migrou = True
        if "historico_intervalos" not in r:
            r["historico_intervalos"] = [r["intervalo_dias"]] if r.get("intervalo_dias") is not None else []
            migrou = True
        if "historico_datas" not in r:
            r["historico_datas"] = [r["data_ultimo_estudo"]] if r.get("data_ultimo_estudo") is not None else []
            migrou = True
        if "historico_ease_factors" not in r:
            r["historico_ease_factors"] = [r.get("ease_factor", 2.5)]
            migrou = True

    if migrou:
        salvar_dados(dados)

    if "materias" in dados:
        dados["materias"].sort(key=obter_fator, reverse=True)
    return dados

def carregar_dados(usuario_email=None):
    """Carrega os dados salvos do ciclo de estudos e realiza migrações de dados se necessário.
    Se um usuario_email for informado e o arquivo local pertencer a outra conta,
    devolve um ciclo vazio (os dados locais são de outro usuário).
    Se o arquivo principal estiver corrompido, tenta recuperar do backup mais recente."""
    if os.path.exists(DB_FILE):
        dados = _carregar_json(DB_FILE)
        if dados is not None:
            owner = dados.get("owner_email")
            if usuario_email and owner and owner != usuario_email:
                return novo_ciclo()
            return _processar_migracoes(dados)
        else:
            # Arquivo principal corrompido ou ilegível: tenta recuperar do backup
            print(f"{C_RED}Erro ao ler o arquivo {DB_FILE}: o arquivo parece estar corrompido.{C_RESET}")
            for i in range(1, MAX_BACKUPS + 1):
                backup = _caminho_backup(i)
                if os.path.exists(backup):
                    dados_recuperados = _carregar_json(backup)
                    if dados_recuperados is not None:
                        print(f"{C_YELLOW}✔ Dados recuperados do backup {i}.{C_RESET}")
                        owner = dados_recuperados.get("owner_email")
                        if usuario_email and owner and owner != usuario_email:
                            print(f"{C_YELLOW}O backup pertence a outra conta; iniciando ciclo vazio.{C_RESET}")
                            input("Pressione Enter para continuar...")
                            return novo_ciclo()
                        input("Pressione Enter para continuar...")
                        return _processar_migracoes(dados_recuperados)
            print(f"{C_RED}Não foi possível recuperar de nenhum backup. Iniciando ciclo vazio.{C_RESET}")
            input("Pressione Enter para continuar...")
    return novo_ciclo()

def salvar_local(dados, email=None):
    """Salva apenas localmente no arquivo JSON (com backup rotativo e escrita atômica)."""
    if "materias" in dados:
        dados["materias"].sort(key=obter_fator, reverse=True)
    if email:
        dados["owner_email"] = email
    # Define timestamp de atualização em UTC
    dados["updated_at"] = datetime.now(timezone.utc).isoformat()
    # Grava o novo estado em .tmp e, só então, desloca os backups e troca o arquivo
    _escrever_json_atomicamente(dados, pre_commit=_rotacionar_backups)

def salvar_dados(dados):
    """Salva os dados localmente e tenta sincronizar com o Supabase."""
    import supabase_client

    # Define flag de pendência
    dados["sync_pending"] = True

    try:
        salvar_local(dados)
    except Exception as e:
        print(f"{C_RED}Erro ao salvar os dados em {DB_FILE}: {e}{C_RESET}")
        input("Pressione Enter para continuar...")
        return

    # Tenta enviar para a nuvem
    if supabase_client.esta_configurado() and supabase_client.obter_id_usuario():
        print(f"\n{C_YELLOW}Sincronizando com o Supabase...{C_RESET}", end="", flush=True)
        if supabase_client.enviar_dados_nuvem(dados):
            dados["sync_pending"] = False
            try:
                salvar_local(dados)
            except Exception:
                pass
            print(f"\r{C_GREEN}✓ Sincronizado com o Supabase com sucesso!{C_RESET}      ")
        else:
            print(f"\r{C_RED}✗ Falha na sincronização. Salvo localmente (pendente).{C_RESET}      ")

def sincronizar_pendencias(dados):
    """Tenta sincronizar quaisquer dados locais pendentes com a nuvem."""
    import supabase_client
    if dados.get("sync_pending", False):
        if supabase_client.esta_configurado() and supabase_client.obter_id_usuario():
            print(f"{C_YELLOW}Sincronizando alterações pendentes com o Supabase...{C_RESET}", end="", flush=True)
            if supabase_client.enviar_dados_nuvem(dados):
                dados["sync_pending"] = False
                try:
                    salvar_local(dados)
                except Exception:
                    pass
                print(f"\r{C_GREEN}✓ Alterações pendentes sincronizadas com sucesso!{C_RESET}      ")
            else:
                print(f"\r{C_RED}✗ Não foi possível sincronizar com o Supabase. Continuará offline.{C_RESET}      ")

def recalcular_progresso_atual(dados):
    """Recalcula o progresso_atual das matérias com base no histórico de sessões do ciclo atual."""
    progresso = {}
    for m in dados.get("materias", []):
        progresso[m["nome"]] = 0.0
        
    sessoes = dados.get("historico_sessoes", [])
    data_inicio_str = dados.get("data_inicio_ciclo")
    
    dt_inicio = None
    if data_inicio_str:
        try:
            dt_inicio = datetime.strptime(data_inicio_str, "%d/%m/%Y %H:%M:%S")
        except Exception:
            pass
            
    # Processa as sessões em ordem cronológica
    for s in sessoes:
        materia = s.get("materia")
        horas = s.get("horas", 0.0)
        tipo = s.get("tipo", "registro")
        data_str = s.get("data", "")
        
        if tipo in ["registro", "ajuste"] and materia in progresso:
            pertence_ao_ciclo = True
            if dt_inicio and data_str:
                try:
                    dt_sessao = datetime.strptime(data_str, "%d/%m/%Y %H:%M:%S")
                    if dt_sessao < dt_inicio:
                        pertence_ao_ciclo = False
                except Exception:
                    pass
            
            if pertence_ao_ciclo:
                if tipo == "registro":
                    progresso[materia] += horas
                elif tipo == "ajuste":
                    progresso[materia] = horas
                    
    dados["progresso_atual"] = progresso

