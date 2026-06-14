import getpass
import supabase_client
from constants import (
    C_CYAN, C_GREEN, C_YELLOW, C_RED, C_MAGENTA, C_BLUE, C_BOLD, C_RESET, DB_FILE
)
from utils import (
    clear_screen, print_header, print_divider
)
from database import carregar_dados
from actions import (
    menu_ciclo_progresso, menu_materias, exibir_historico,
    configuracao_inicial, verificar_atualizacao
)
from reviews import menu_revisoes

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

    dados = carregar_dados()
    
    # Se for o primeiro acesso (sem horas configuradas e sem matérias)
    if dados["horas_semanais"] == 0.0 and not dados["materias"]:
        configuracao_inicial(dados)
        
    while True:
        clear_screen()
        print_header("MENU PRINCIPAL - CICLO DE ESTUDOS ESTRATÉGICO")
        
        horas = dados.get("horas_semanais", 0.0)
        num_materias = len(dados.get("materias", []))
        total_estudado = sum(dados.get("progresso_atual", {}).values())
        
        print(f"  {C_BOLD}Carga Semanal:{C_RESET} {C_GREEN}{horas}h{C_RESET}   |   {C_BOLD}Estudado:{C_RESET} {C_GREEN}{total_estudado:.1f}h{C_RESET}   |   {C_BOLD}Matérias:{C_RESET} {C_GREEN}{num_materias}{C_RESET}")
        print_divider()
        
        print(f"  [{C_CYAN}1{C_RESET}] 📅 Ciclo de Estudos & Progresso")
        print(f"  [{C_CYAN}2{C_RESET}] 📚 Gerenciar Matérias")
        print(f"  [{C_CYAN}3{C_RESET}] 🔄 Revisões Estratégicas (Repetição Espaçada)")
        print(f"  [{C_CYAN}4{C_RESET}] 📜 Históricos de Estudos (Ciclos e Sessões)")
        print(f"  [{C_CYAN}5{C_RESET}] 🚀 Verificar Atualizações")
        print(f"  [{C_CYAN}9{C_RESET}] 🚪 Deslogar / Alternar Conta")
        print(f"  [{C_CYAN}0{C_RESET}] 💾 Salvar e Sair")
        print_divider()
        
        opcao = input("Escolha uma opção: ").strip()
        
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
            print(f"\n{C_RED}Opção inválida! Escolha um número entre 0, 1-5 ou 9.{C_RESET}")
            input("\nPressione Enter para tentar novamente...")

if __name__ == "__main__":
    main()