import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Triagem Oficial", page_icon="🎓")

# Conectar ao Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Senha do Admin
SENHA_ADMIN = "suasenha123"

# Inicializar estados
if "passo" not in st.session_state:
    st.session_state.passo = 0
    st.session_state.respostas = []

st.sidebar.title("Navegação")
aba = st.sidebar.radio("Ir para:", ["Formulário de Inscrição", "Painel Administrativo"])

# --- ABA DO CANDIDATO ---
if aba == "Formulário de Inscrição":
    st.title("🚀 Inscrição - Programa de Bolsas")
    
    perguntas = [
        "Qual seu objetivo com essa bolsa?",
        "Qual seu maior desafio superado?",
        "Como ajudará sua comunidade?",
        "Qual sua maior conquista?",
        "Por que você deve ser o escolhido?"
    ]

    if st.session_state.passo < 5:
        st.subheader(f"Pergunta {st.session_state.passo + 1}")
        resp = st.text_area(perguntas[st.session_state.passo])
        
        if st.button("Enviar"):
            if resp:
                st.session_state.respostas.append(resp)
                st.session_state.passo += 1
                st.rerun()
    else:
        st.success("🎉 Inscrição enviada com sucesso! Aguarde nosso contato.")
        
        # Lógica Simples de Classificação
        texto = " ".join(st.session_state.respostas).lower()
        classe = "Inovação"
        if "comunidade" in texto or "ajudar" in texto: classe = "Liderança Comunitária"
        if "difícil" in texto or "superar" in texto: classe = "Resiliência Acadêmica"

        # Salvar no Google Sheets
        nova_linha = pd.DataFrame([{
            "Pergunta1": st.session_state.respostas[0],
            "Pergunta2": st.session_state.respostas[1],
            "Pergunta3": st.session_state.respostas[2],
            "Pergunta4": st.session_state.respostas[3],
            "Pergunta5": st.session_state.respostas[4],
            "Classificacao": classe,
            "Resumo": f"Perfil identificado como {classe}."
        }])
        
        # Ler dados atuais e adicionar novo
        try:
            existente = conn.read(worksheet="Página1", ttl=0)
            atualizado = pd.concat([existente, nova_linha], ignore_index=True)
            conn.update(worksheet="Página1", data=atualizado)
        except:
            conn.update(worksheet="Página1", data=nova_linha)

        if st.button("Nova Inscrição"):
            st.session_state.passo = 0
            st.session_state.respostas = []
            st.rerun()

# --- ABA DO ADMIN ---
else:
    st.title("🔒 Painel do Gestor")
    senha = st.text_input("Senha", type="password")
    
    if senha == SENHA_ADMIN:
        data = conn.read(worksheet="Página1", ttl =0)
        st.dataframe(data)
        st.download_button("Baixar Planilha (CSV)", data.to_csv().encode('utf-8'), "candidatos.csv")
