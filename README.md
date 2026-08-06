# 📚 Ciclo de Estudos Estratégico

> **Um gerenciador de estudos moderno via terminal (CLI) projetado para otimizar sua preparação para concursos e exames com priorização algorítmica e repetição espaçada inteligente.**

---

<div align="center">

![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Git Powered](https://img.shields.io/badge/Git-Auto--Update-orange?style=for-the-badge&logo=git&logoColor=white)
![Algorithms Used](https://img.shields.io/badge/Algoritmos-SM2%20%2F%20Anki%20%2F%20Prioridade-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Desenvolvimento%20Ativo-brightgreen?style=for-the-badge)

</div>

---

## 🗺️ Índice
- [🎨 Identidade Visual](#-identidade-visual)
- [✨ Principais Funcionalidades](#-principais-funcionalidades)
- [📐 O Algoritmo de Priorização](#-o-algoritmo-de-priorizacao)
- [🔄 Repetição Espaçada Inteligente (Baseada no SM2)](#-repeticao-espacada-inteligente-baseada-no-sm2)
- [📂 Estrutura do Projeto](#-estrutura-do-projeto)
- [🚀 Como Começar](#-como-comecar)
- [⚙️ Como Utilizar](#-como-utilizar)

---

## 🎨 Identidade Visual

O projeto utiliza um design de terminal premium com cores ANSI vibrantes e formatação tabular precisa, desenhado para ser legível, dinâmico e esteticamente agradável:

| Cor | Descrição / Uso |
| :--- | :--- |
| 🔵 **Ciano** | Estruturas de tabelas, cabeçalhos de menus e realces. |
| 🟢 **Verde** | Valores positivos, conclusões de metas, tempo estudado e status de sucesso. |
| 🟡 **Amarelo** | Avisos importantes, observações e lembretes de revisões. |
| 🔴 **Vermelho** | Erros de validação, status atrasados e alertas críticos. |
| ⚪ **Negrito** | Rótulos e informações principais do console. |

---

## ✨ Principais Funcionalidades

### 📅 1. Ciclo de Estudos e Carga Horária Dinâmica
O sistema calcula automaticamente a distribuição de horas que você deve dedicar a cada matéria com base no peso e na relevância delas no seu edital. Conforme você registra o progresso, o ciclo recalcula o tempo restante dinamicamente.

### 🔄 2. Repetição Espaçada Inteligente (Spaced Repetition)
Esqueça planilhas manuais. O sistema calcula a data e o intervalo ideal da sua próxima revisão utilizando o algoritmo **SM2** (estilo Anki), adaptado para suavizar variações de desempenho e com bônus para consistência e penalidades para declínio de acertos.

### 📝 3. Histórico Detalhado de Sessões
Cada sessão de estudo registrada gera um log contendo:
* Data e hora exatas do registro.
* Tempo exato dedicado.
* Uma anotação/observação opcional (ex: *"Resolução de questões de crase no QConcursos"*).
* Filtros de pesquisa por matéria diretamente na tela.

### 🚀 4. Auto-updater via GitHub
Opção nativa no menu principal para verificar atualizações no repositório GitHub. Caso haja uma nova versão, o script realiza um `git pull` de forma automatizada e segura e reinicia a aplicação para aplicar as mudanças.

### 👥 5. Múltiplos Perfis no Mesmo Dispositivo
Use vários logins no mesmo script sem precisar digitar e-mail e senha toda vez:
* **Perfis salvos**: cada conta logada é salva no dispositivo e fica disponível no seletor de perfis.
* **Seletor na inicialização**: quando há perfis salvos, uma tela permite escolher o perfil (ou adicionar um novo) antes de entrar.
* **Troca rápida**: pelo menu principal (`[7] Trocar de Perfil`), troque de conta em segundos — os dados do perfil atual são sincronizados na nuvem automaticamente.
* **Remover perfil**: remova contas do dispositivo quando quiser (os dados na nuvem continuam intactos).

### 👥 6. Grupo de Estudos (Responsabilidade Mútua)
Forme grupos de estudo com 2 ou mais pessoas (sem limite de membros) para manter a constância em equipe:
* **Criação e convite**: o criador do grupo (admin) gera um código único (`GR-XXXXXX`) e os demais entram com esse código.
* **Dashboard do grupo**: resumo de todos os membros com status de estudo do dia, sequência de consistência (streak) e metas semanais cumpridas.
* **Acompanhamento individual**: consulte o calendário de consistência, os logs detalhados por data e as justificativas de qualquer membro.
* **Justificativas de ausência**: registre, edite ou exclua justificativas para dias sem estudo, visíveis para todo o grupo.
* **Administração**: o criador pode remover membros e dissolver o grupo. Se o admin sair, a liderança é transferida automaticamente.

---

## 📐 O Algoritmo de Priorização

A carga horária semanal é distribuída proporcionalmente ao **Fator de Prioridade** de cada matéria, calculado por:

$$\text{Fator} = (\text{Questões na Prova} \times \text{Peso da Questão}) \times \text{Dificuldade}$$

* **Questões na Prova**: Quantidade de questões cobradas no último edital.
* **Peso da Questão**: Peso atribuído pela banca.
* **Dificuldade**: Uma escala de 1 a 5 definida por você (baseada no seu domínio no assunto).

Desta forma, matérias com maior relevância na prova e que você possui maior dificuldade receberão uma alocação de tempo maior, otimizando o custo-benefício dos seus estudos.

---

## 🔄 Repetição Espaçada Inteligente (Baseada no SM2)

O espaçamento de revisões utiliza o algoritmo **SuperMemo-2 (SM2)** adaptado para uma experiência de alto desempenho em concursos:

* **Média Histórica Suavizada**: A porcentagem de acertos atual é combinada com o seu histórico recente para evitar alterações drásticas devido a um único dia ruim.
* **Ajuste Contínuo de Facilidade (Ease Factor)**: O fator varia de `1.3` a `5.0` de forma contínua, medindo a velocidade com que você domina o assunto.
* **Bônus de Consistência**: Melhora contínua de desempenho nas últimas 3 revisões aplica um bônus de **+10%** no espaçamento.
* **Bônus de Alta Performance**: Manter acertos acima de 90% em 3 revisões consecutivas expande o espaçamento em **+15%**.
* **Penalidade de Declínio**: Queda de rendimento nas últimas 3 revisões reduz o intervalo em **-15%**.
* **Tratamento de Lapsos**: Se o rendimento cair abaixo de 50% de acertos, o assunto é classificado como lapso e o intervalo é reiniciado para 1 dia para fixação rápida.

---

## 📂 Estrutura do Projeto

```text
├── ciclo.py             # Arquivo principal / Entry-point e Loop do Menu
├── actions.py           # Submenus, Lógica de Telas, Registros e Logs
├── reviews.py           # Gerenciador de Revisões Espaçadas e SM2
├── partner_menu.py      # Grupo de Estudos (menus, dashboard, justificativas)
├── calculo.py           # Lógica pura de cálculo (SM2, streak, tempo, métricas)
├── supabase_client.py   # Integração Supabase (auth, sync e grupos)
├── database.py          # Leitura/Escrita do JSON e migração automática de dados
├── logger.py            # Configuração de log (ciclo.log)
├── utils.py             # Helpers de UI (tela, inputs, cores)
├── constants.py         # Cores ANSI e variáveis de configuração de tela
├── setup_banco.sql      # Script SQL completo (tabelas + políticas + migração) para o Supabase
├── requirements.txt     # Dependências de execução
├── requirements-dev.txt # Dependências de desenvolvimento (pytest)
├── tests/               # Testes automatizados
├── version.txt          # Arquivo contendo a versão atual instalada
└── ciclo_estudos.json   # Banco de dados local (gerado automaticamente)
```

---

## 🚀 Como Começar

### Pré-requisitos
* Python 3.8 ou superior instalado.
* Git instalado (necessário para a função de auto-update).

### Instalação e Execução

1. Clone o repositório para sua máquina local:
   ```bash
   git clone https://github.com/nissincjs/Gerencicador-de-estudos.git
   ```
2. Navegue até o diretório do projeto:
   ```bash
   cd Gerencicador-de-estudos
   ```
3. **Configure o Supabase** (usado para autenticação, sincronização na nuvem e grupos de estudo):
   1. Crie um projeto gratuito em [supabase.com](https://supabase.com).
   2. No **SQL Editor** do projeto, execute o script `setup_banco.sql` (cria todas as tabelas e políticas).
   3. Copie o arquivo `.env.example` para `.env` e preencha a **URL** e a **chave anon** do projeto (em *Project Settings → API*).
4. Execute o script inicializador adequado para o seu sistema (ele criará o ambiente virtual `venv` e instalará todas as dependências automaticamente):

   * **No Windows:**
     * Dê um duplo-clique no arquivo `iniciar.bat` ou execute no terminal:
       ```cmd
       iniciar.bat
       ```
   * **No Linux (Mint, Ubuntu, Debian, etc.):**
     * Execute no terminal:
       ```bash
       ./iniciar.sh
       ```


---

## ⚙️ Como Utilizar

Ao iniciar pela primeira vez, o assistente guiará você na configuração da sua **carga horária semanal** e no cadastro da **sua primeira matéria** para inicializar o ciclo.

No menu principal, você terá acesso rápido às seções organizadas:
* Digite **`1`** para acessar **Ciclo & Progresso** (visualizar tabela, registrar estudos).
* Digite **`2`** para **Gerenciar Matérias** (criar, editar ou remover matérias).
* Digite **`3`** para **Revisões Estratégicas** (gerenciar revisões, registrar acertos de questões).
* Digite **`4`** para acessar seus **Históricos** (ver logs detalhados das suas sessões).
* Digite **`5`** para buscar **Atualizações** do script.
* Digite **`6`** para acessar o **Grupo de Estudos** (criar/entrar em grupo, acompanhar membros e gerenciar justificativas).
* Digite **`7`** para **Trocar de Perfil** (alternar entre contas salvas neste dispositivo sem digitar senha de novo).
* Digite **`9`** para **Deslogar e Sair** (mantém os perfis salvos para o próximo acesso).
* Digite **`0`** para **Salvar e Sair** da aplicação.

> **ℹ️ Configuração do banco**: execute o script `setup_banco.sql` no SQL Editor do Supabase. Ele cria **todas** as tabelas (`perfis_usuario`, `ciclos_usuario`, `grupos` e `membros_grupo`) e as políticas de acesso. Funciona em banco novo e, em banco antigo, converte automaticamente vínculos de parceiro em grupos e remove o legado. É idempotente (pode rodar quantas vezes quiser).

---

## 🧪 Testes

Os testes automatizados cobrem o núcleo de lógica (SM2, streak, tempo, banco de dados local) e não dependem de rede nem do Supabase.

```bash
# Instalar as dependências de desenvolvimento
venv/bin/pip install -r requirements-dev.txt

# Rodar os testes
venv/bin/python -m pytest tests/ -v
```

Os erros de execução do app são registrados no arquivo `ciclo.log` (gerado automaticamente, ignorado pelo Git) para facilitar o diagnóstico sem poluir o terminal.

---
<div align="center">
Desenvolvido com foco em alta performance e aprovação! 📚🚀
</div>
