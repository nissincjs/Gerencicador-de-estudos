import os
import json
from datetime import datetime, timezone
from constants import DB_FILE, C_RED, C_RESET, C_YELLOW, C_GREEN, C_BOLD

def obter_fator(m):
    """Calcula o fator de prioridade da matéria."""
    qp = m.get("questoes_prova", 10.0)
    pq = m.get("peso_questao", 1.0)
    dif = m.get("dificuldade", 1.0)
    return qp * pq * dif

def carregar_dados():
    """Carrega os dados salvos do ciclo de estudos e realiza migrações de dados se necessário."""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                dados = json.load(f)
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
                    migrou = True
                if "revisoes" not in dados:
                    dados["revisoes"] = []
                if "limite_revisoes_diarias" not in dados:
                    dados["limite_revisoes_diarias"] = 10
                    migrou = True
                if "justificativas" not in dados:
                    dados["justificativas"] = []
                    migrou = True
                
                # Migração de dados do formato antigo para o formato estratégico (sem aulas)
                migrou = False
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
        except Exception as e:
            print(f"{C_RED}Erro ao ler o arquivo {DB_FILE}: {e}{C_RESET}")
            input("Pressione Enter para iniciar com um ciclo vazio...")
            
    return {
        "horas_semanais": 0.0,
        "limite_revisoes_diarias": 10,
        "data_inicio_ciclo": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "materias": [],
        "progresso_atual": {},
        "historico_ciclos": [],
        "historico_sessoes": [],
        "revisoes": [],
        "justificativas": []
    }

def salvar_local(dados):
    """Salva apenas localmente no arquivo JSON."""
    if "materias" in dados:
        dados["materias"].sort(key=obter_fator, reverse=True)
    # Define timestamp de atualização em UTC
    dados["updated_at"] = datetime.now(timezone.utc).isoformat()
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

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

