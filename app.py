import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

# 1. Configurações Iniciais
st.set_page_config(page_title="Sistema de Triagem v5.0", page_icon="🎓", layout="wide")

# Conexão segura
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Erro de conexão com a planilha. Verifique os Secrets.")

# Senha de Acesso
SENHA_ADMIN = "12345"

# Inicialização de variáveis de controle
if "passo" not in st.session_state:
    st.session_state.passo = 0
    st.session_state.respostas = []
    st.session_state.dados_pessoais = {"nome": "", "email": ""}
    st.session_state.enviado = False

# --- MOTOR DE ANÁLISE BALANCEADA ---
def analisar_perfil(respostas):
    texto = " ".join(respostas).lower()
    palavras = re.findall(r'\w+', texto)
    qtd_palavras = len(palavras)
    vocab_unico = len(set(palavras))
    
    # Pontuação de Esforço (0 a 40) - 80 palavras = Nota Máxima
    score_esforco = min(40, (qtd_palavras / 80) * 40)
    
    # Diversidade de Vocabulário (0 a 20)
    complexidade = (vocab_unico / qtd_palavras) * 20 if qtd_palavras > 0 else 0
    
    # Temas Positivos (Bônus de Selecionado)
    positivos = ["projeto", "ajudar", "comunidade", "social", "equipe", "estudar", "aprender", "superar", "impacto", "futuro", "região", "medicina", "saúde", "dedicação", "esforço"]
    score_positivos = sum(1 for p in positivos if p in texto) * 4
    
    # Sinais de Alerta (Rigor de Reprovação)
    red_flags = ["odeio", "rico", "dinheiro", "dane", "sozinho", "individual", "preguiça", "ambicioso", "riqueza"]
    score_negativo = sum(1 for r in red_flags if r in texto) * 35 # Penalidade pesada
    
    # Nota Final
    nota = (score_esforco + complexidade + min(40, score_positivos)) - score_negativo
    nota = max(0, nota)
    
    # Verificação de Perfil
    if nota >= 60:
        res, status = "SELECIONADO", "EXCELENTE: Candidato articulado, esforçado e com valores alinhados."
    elif nota >= 35:
        res, status = "EM ANÁLISE", "POTENCIAL: Respostas coerentes, mas poderiam ser mais detalhadas."
    else:
        res, status = "REPROVADO", "DESALINHAMENTO: Respostas superficiais ou valores contrários ao programa."
        
    return res, round(nota, 2), status

# --- INTERFACE LATERAL ---
st.sidebar.title("Navegação Principal")
aba = st.sidebar.radio("Escolha uma opção:", ["Inscrição de Candidato", "Área do Gestor"])

# --- ABA 1: INSCRIÇÃO ---
if aba == "Inscrição de Candidato":
    st.title("🚀 Inscrição - Programa de Bolsas")
    
    if st.session_state.passo == 0:
        st.subheader("Dados do Candidato")
        nome = st.text_input("Nome Completo:")
        email = st.text_input("E-mail:")
        if st.button("Iniciar Triagem"):
            if nome and "@" in email:
                st.session_state.dados_pessoais = {"nome": nome, "email": email}
                st.session_state.passo = 1
                st.session_state.enviado = False
                st.rerun()
            else:
                st.warning("Por favor, preencha nome e e-mail corretamente.")

    elif 1 <= st.session_state.passo <= 5:
        perguntas = [
            "O que te motiva academicamente e qual sua trajetória até aqui?",
            "Relate um desafio de vida e como você o superou.",
            "Como você descreve sua capacidade de trabalhar em grupos?",
            "Como você pretende aplicar o que aprender em sua região?",
            "Por que devemos confiar em sua persistência para esta vaga?"
        ]
        st.subheader(f"Questão {st.session_state.passo} de 5")
        st.info(perguntas[st.session_state.passo - 1])
        res_usuario = st.text_area("Sua resposta:", height=150, key=f"q{st.session_state.passo}")
        
        if st.button("Próxima"):
            st.session_state.respostas.append(res_usuario if res_usuario else "Não respondeu")
            st.session_state.passo += 1
            st.rerun()

    else:
        if not st.session_state.enviado:
            with st.spinner("Enviando dados..."):
                resultado, nota_final, resumo = analisar_perfil(st.session_state.respostas)
                nova_linha = pd.DataFrame([{
                    "Nome": st.session_state.dados_pessoais["nome"],
                    "Email": st.session_state.dados_pessoais["email"],
                    "Pergunta1": st.session_state.respostas[0],
                    "Pergunta2": st.session_state.respostas[1],
                    "Pergunta3": st.session_state.respostas[2],
                    "Pergunta4": st.session_state.respostas[3],
                    "Pergunta5": st.session_state.respostas[4],
                    "Classificacao": "Identificado",
                    "Resultado": resultado,
                    "Pontuacao": nota_final,
                    "Resumo": resumo
                }])
                try:
                    existente = conn.read(worksheet="Página1", ttl=0)
                    conn.update(worksheet="Página1", data=pd.concat([existente, nova_linha], ignore_index=True))
                    st.session_state.enviado = True
                except:
                    conn.update(worksheet="Página1", data=nova_linha)
        
        st.success("✅ Inscrição finalizada com sucesso!")
        if st.button("Sair e Reiniciar"):
            st.session_state.passo = 0
            st.session_state.respostas = []
            st.rerun()

# --- ABA 2: ÁREA DO GESTOR (TOTALMENTE REESCRITA) ---
else:
    st.title("🔑 Painel Administrativo")
    st.write("Acesso restrito para avaliadores.")
    
    # Campo de senha sempre visível nesta aba
    entrada_senha = st.text_input("Digite a senha de acesso:", type="password")
    
    if entrada_senha == SENHA_ADMIN:
        st.success("Acesso autorizado!")
        try:
            with st.spinner("Carregando base de dados..."):
                df = conn.read(worksheet="Página1", ttl=0)
                if not df.empty:
                    # Formatação da tabela
                    df["Pontuacao"] = pd.to_numeric(df["Pontuacao"], errors='coerce').fillna(0)
                    st.write(f"### Total de Candidatos: {len(df)}")
                    st.dataframe(df.sort_values(by="Pontuacao", ascending=False), use_container_width=True)
                else:
                    st.info("Nenhuma inscrição encontrada na planilha.")
        except Exception as err:
            st.error(f"Erro ao ler planilha: {err}")
    elif entrada_senha != "":
        st.error("Senha incorreta. Tente novamente.")
