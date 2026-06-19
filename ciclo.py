import getpass
import supabase_client
from constants import (
    C_CYAN, C_GREEN, C_YELLOW, C_RED, C_MAGENTA, C_BLUE, C_BOLD, C_RESET, DB_FILE
)
from utils import (
    clear_screen, print_header, print_divider, formatar_horas_minutos
)
from database import carregar_dados, salvar_local, sincronizar_pendencias
from actions import (
    menu_ciclo_progresso, menu_materias, exibir_historico,
    configuracao_inicial, verificar_atualizacao
)
from reviews import menu_revisoes
import os
import partner_menu

def limpar_meta_dados(dados: dict) -> dict:
    """Retorna uma cópia limpa dos dados sem campos de controle/timestamp."""
    if not dados:
        return {}
    copia = dados.copy()
    copia.pop("sync_pending", None)
    copia.pop("updated_at", None)
    return copia

def e_vazio(dados: dict) -> bool:
    """Verifica se o ciclo de estudos está vazio/zerado (sem horas e sem matérias)."""
    if not dados:
        return True
    materias = dados.get("materias", [])
    horas = dados.get("horas_semanais", 0.0)
    return len(materias) == 0 and horas == 0.0

def main():
    # Verifica se o Supabase está devidamente configurado
    if not supabase_client.esta_configurado():
        clear_screen()
        print_header("CONFIGURAÇÃO DO SUPABASE REQUERIDA")
        print(f"\n  {C_YELLOW}Atenção:{C_RESET} O arquivo {C_BOLD}.env{C_RESET} não foi configurado ou contém chaves inválidas.")
        print("  Para utilizar o sistema, siga as instruções abaixo:")
        print(f"  1. Copie o arquivo {C_BOLD}.env.example{C_RESET} para {C_BOLD}.env{C_RESET}")
        print(f"  2. Preencha as chaves {C_BOLD}SUPABASE_URL{C_RESET} e {C_BOLD}SUPABASE_KEY{C_RESET} com os dados do seu projeto.")
        print_divider()
        input("\nPressione Enter para sair e configurar...")
        return

    usuario = supabase_client.recuperar_sessao_salva()
    if usuario:
        clear_screen()
        print_header("SESSÃO RESTAURADA")
        print(f"\n{C_GREEN}Bem-vindo(a) de volta, {usuario.email}!{C_RESET}")
        input("\nPressione Enter para continuar para o painel...")

    while not usuario:
        clear_screen()
        print_header("AUTENTICAÇÃO - CICLO DE ESTUDOS")
        print(f"  [{C_CYAN}1{C_RESET}] 🔑 Entrar (Login)")
        print(f"  [{C_CYAN}2{C_RESET}] 📝 Criar Nova Conta (Cadastro)")
        print(f"  [{C_CYAN}0{C_RESET}] ❌ Sair")
        print_divider()
        
        opcao = input("Escolha uma opção: ").strip()
        
        if opcao == "1":
            clear_screen()
            print_header("LOGIN - CICLO DE ESTUDOS")
            email = input("  E-mail: ").strip()
            senha = getpass.getpass("  Senha: ")
            
            print(f"\n{C_YELLOW}Autenticando...{C_RESET}")
            try:
                usuario = supabase_client.fazer_login(email, senha)
                print(f"\n{C_GREEN}Login realizado com sucesso! Bem-vindo(a), {usuario.email}!{C_RESET}")
                input("\nPressione Enter para continuar...")
            except Exception as e:
                print(f"\n{C_RED}Erro ao entrar: {e}{C_RESET}")
                input("\nPressione Enter para tentar novamente...")
                
        elif opcao == "2":
            clear_screen()
            print_header("CADASTRO - CICLO DE ESTUDOS")
            email = input("  E-mail: ").strip()
            senha = getpass.getpass("  Senha: ")
            confirmar_senha = getpass.getpass("  Confirme a Senha: ")
            
            if senha != confirmar_senha:
                print(f"\n{C_RED}Erro: As senhas não coincidem.{C_RESET}")
                input("\nPressione Enter para tentar novamente...")
                continue
                
            print(f"\n{C_YELLOW}Criando sua conta...{C_RESET}")
            try:
                usuario = supabase_client.fazer_cadastro(email, senha)
                print(f"\n{C_GREEN}Conta criada com sucesso!{C_RESET}")
                print(f"{C_YELLOW}Nota: Se você não desativou a confirmação por e-mail nas configurações do Supabase, você precisará confirmar seu e-mail antes de fazer login.{C_RESET}")
                input("\nPressione Enter para continuar...")
            except Exception as e:
                print(f"\n{C_RED}Erro ao cadastrar: {e}{C_RESET}")
                input("\nPressione Enter para tentar novamente...")
                
        elif opcao == "0":
            clear_screen()
            print_header("ATÉ LOGO!")
            print("Saindo do sistema de ciclo de estudos...\n")
            return
        else:
            print(f"\n{C_RED}Opção inválida!{C_RESET}")
            input("\nPressione Enter para tentar novamente...")

    # Garante que o perfil do usuário esteja criado no banco
    if usuario:
        supabase_client.garantir_perfil_criado(usuario.id, usuario.email)

    # Fluxo de Sincronização Local + Nuvem
    dados_nuvem = supabase_client.baixar_dados_nuvem()
    local_exists = os.path.exists(DB_FILE)
    dados = None

    if dados_nuvem:
        if not local_exists:
            clear_screen()
            print_header("RESTAURAÇÃO DE DADOS DA NUVEM")
            print(f"\n{C_GREEN}Dados salvos encontrados no Supabase! Recriando ciclo local...{C_RESET}")
            dados = dados_nuvem
            dados["sync_pending"] = False
            salvar_local(dados)
            input("\nPressione Enter para continuar...")
        else:
            dados_locais = carregar_dados()
            
            # 1. Se os dados locais estiverem vazios/zerados e a nuvem não,
            #    prioriza a nuvem automaticamente por segurança.
            if e_vazio(dados_locais) and not e_vazio(dados_nuvem):
                dados = dados_nuvem
                dados["sync_pending"] = False
                salvar_local(dados)
                clear_screen()
                print_header("RESTAURAÇÃO AUTOMÁTICA")
                print(f"\n{C_GREEN}Dados locais vazios detectados. Restaurando ciclo da nuvem...{C_RESET}")
                input("\nPressione Enter para continuar...")
                
            # 2. Se a nuvem estiver vazia e o local não, mantém o local.
            elif not e_vazio(dados_locais) and e_vazio(dados_nuvem):
                dados = dados_locais
                dados["sync_pending"] = True
                salvar_local(dados)
                
            # 3. Compara o conteúdo estrutural (ignorando campos de controle/timestamps)
            elif limpar_meta_dados(dados_locais) == limpar_meta_dados(dados_nuvem):
                dados = dados_locais
                dados["sync_pending"] = False
                salvar_local(dados)
                
            # 4. Compara timestamps de atualização
            else:
                updated_local = dados_locais.get("updated_at")
                updated_nuvem = dados_nuvem.get("updated_at")
                
                resolvido = False
                if updated_local and updated_nuvem:
                    try:
                        from datetime import datetime
                        dt_local = datetime.fromisoformat(updated_local)
                        dt_nuvem = datetime.fromisoformat(updated_nuvem)
                        
                        if dt_local > dt_nuvem:
                            # Local é mais recente, mantém local e agenda sync
                            dados = dados_locais
                            dados["sync_pending"] = True
                            salvar_local(dados)
                            resolvido = True
                        elif dt_nuvem > dt_local:
                            # Nuvem é mais recente, baixa da nuvem
                            dados = dados_nuvem
                            dados["sync_pending"] = False
                            salvar_local(dados)
                            resolvido = True
                    except Exception:
                        pass
                
                if not resolvido:
                    # Caso de fallback: exibe tela de conflito manual
                    clear_screen()
                    print_header("CONFLITO DE DADOS")
                    print(f"  {C_YELLOW}Foram encontrados dados locais neste computador e dados na nuvem.{C_RESET}")
                    print(f"  [{C_CYAN}1{C_RESET}] 💻 Manter DADOS LOCAIS (sobrescreverá a nuvem com os dados locais)")
                    print(f"  [{C_CYAN}2{C_RESET}] ☁️ Baixar DADOS DA NUVEM (sobrescreverá os dados locais deste computador)")
                    print_divider()
                    
                    escolha = ""
                    while escolha not in ["1", "2"]:
                        escolha = input("Escolha uma opção: ").strip()
                        if escolha == "1":
                            dados = dados_locais
                            dados["sync_pending"] = True
                            salvar_local(dados)
                            print(f"\n{C_GREEN}Mantendo dados locais. Eles serão sincronizados na nuvem em breve.{C_RESET}")
                            input("\nPressione Enter para continuar...")
                        elif escolha == "2":
                            dados = dados_nuvem
                            dados["sync_pending"] = False
                            salvar_local(dados)
                            print(f"\n{C_GREEN}Dados da nuvem aplicados localmente com sucesso!{C_RESET}")
                            input("\nPressione Enter para continuar...")
                        else:
                            print(f"\n{C_RED}Opção inválida!{C_RESET}")
    else:
        dados = carregar_dados()

    # Tenta sincronizar pendências imediatamente ao abrir
    sincronizar_pendencias(dados)
    
    # Se for o primeiro acesso (sem horas configuradas e sem matérias)
    if dados["horas_semanais"] == 0.0 and not dados["materias"]:
        configuracao_inicial(dados)
        
    while True:
        try:
            clear_screen()
            print_header("MENU PRINCIPAL - CICLO DE ESTUDOS ESTRATÉGICO")
            
            horas = dados.get("horas_semanais", 0.0)
            num_materias = len(dados.get("materias", []))
            total_estudado = sum(dados.get("progresso_atual", {}).values())
            
            carga_formatada = formatar_horas_minutos(horas)
            estudado_formatado = formatar_horas_minutos(total_estudado)
            print(f"  {C_BOLD}Carga Semanal:{C_RESET} {C_GREEN}{carga_formatada}{C_RESET}   |   {C_BOLD}Estudado:{C_RESET} {C_GREEN}{estudado_formatado}{C_RESET}   |   {C_BOLD}Matérias:{C_RESET} {C_GREEN}{num_materias}{C_RESET}")
            print_divider()
            
            print(f"  [{C_CYAN}1{C_RESET}] 📅 Ciclo de Estudos & Progresso")
            print(f"  [{C_CYAN}2{C_RESET}] 📚 Gerenciar Matérias")
            print(f"  [{C_CYAN}3{C_RESET}] 🔄 Revisões Estratégicas (Repetição Espaçada)")
            print(f"  [{C_CYAN}4{C_RESET}] 📜 Históricos de Estudos (Ciclos e Sessões)")
            print(f"  [{C_CYAN}5{C_RESET}] 🚀 Verificar Atualizações")
            print(f"  [{C_CYAN}6{C_RESET}] 🤝 Parceiro de Estudos")
            print(f"  [{C_CYAN}9{C_RESET}] 🚪 Deslogar / Alternar Conta")
            print(f"  [{C_CYAN}0{C_RESET}] 💾 Salvar e Sair")
            print_divider()
            
            opcao = input("Escolha uma opção: ").strip()
            
            try:
                if opcao == "1":
                    menu_ciclo_progresso(dados)
                elif opcao == "2":
                    menu_materias(dados)
                elif opcao == "3":
                    menu_revisoes(dados)
                elif opcao == "4":
                    exibir_historico(dados)
                elif opcao == "5":
                    verificar_atualizacao(dados)
                elif opcao == "6":
                    partner_menu.menu_parceria(dados)
                elif opcao == "9":
                    clear_screen()
                    print_header("DESCONECTANDO")
                    supabase_client.limpar_sessao()
                    print(f"\n{C_GREEN}Você foi deslogado com sucesso!{C_RESET}")
                    input("\nPressione Enter para sair...")
                    break
                elif opcao == "0":
                    clear_screen()
                    print_header("ATÉ LOGO!")
                    print(f"\n{C_GREEN}Seu ciclo de estudos foi salvo com sucesso em '{DB_FILE}'!{C_RESET}")
                    print("Mantenha o foco e bons estudos! 📚🚀\n")
                    break
                else:
                    print(f"\n{C_RED}Opção inválida! Escolha um número entre 0, 1-6 ou 9.{C_RESET}")
                    input("\nPressione Enter para tentar novamente...")
            except KeyboardInterrupt:
                pass
        except KeyboardInterrupt:
            clear_screen()
            print_header("ATÉ LOGO!")
            print(f"\n{C_GREEN}Seu ciclo de estudos foi salvo com sucesso em '{DB_FILE}'!{C_RESET}")
            print("Mantenha o foco e bons estudos! 📚🚀\n")
            break

if __name__ == "__main__":
    main()