import streamlit as st

# Configuração da Página
st.set_page_config(page_title="Plataforma de Triagem IA", page_icon="🎓")

st.title("🤖 Assistente de Triagem Acadêmica")
st.write("Responda às perguntas abaixo para avaliarmos seu perfil.")

# Inicialização do estado da conversa
if "passo" not in st.session_state:
    st.session_state.passo = 0
    st.session_state.respostas = []

perguntas = [
    "Qual é o seu maior objetivo profissional hoje?",
    "Conte sobre um desafio que você superou recentemente.",
    "Como você lida com críticas ou feedbacks negativos?",
    "Por que você deveria ser escolhido para esta oportunidade?",
    "Se você ganhasse a vaga hoje, qual seria sua primeira ação?"
]

if st.session_state.passo < len(perguntas):
    pergunta_atual = perguntas[st.session_state.passo]
    resposta = st.text_input(f"Pergunta {st.session_state.passo + 1}: {pergunta_atual}")
    
    if st.button("Enviar Resposta"):
        if resposta:
            st.session_state.respostas.append(resposta)
            st.session_state.passo += 1
            st.rerun()
        else:
            st.warning("Por favor, digite uma resposta.")

else:
    st.success("Triagem Concluída! Analisando perfil...")
    
    # Aqui o código simula a análise da IA (ou você pode conectar à API do ChatGPT)
    # Para este exemplo, faremos uma análise lógica simples:
    todas_respostas = " ".join(st.session_state.respostas)
    
    st.subheader("📋 Resultado da Avaliação")
    
    # Lógica de Seleção (Simulada)
    if len(todas_respostas) > 100: # Exemplo de critério: profundidade das respostas
        status = "✅ [SELECIONADO]"
        cor = "green"
    else:
        status = "❌ [NÃO SELECIONADO]"
        cor = "red"
        
    st.markdown(f"### Status: :{cor}[{status}]")
    
    st.write("**Resumo Técnico:**")
    st.info(f"O candidato demonstrou {'profundidade e clareza' if status == '✅ [SELECIONADO]' else 'pouco engajamento'} em suas respostas. A análise baseou-se na consistência dos argumentos e prontidão para o desafio.")

    if st.button("Reiniciar Triagem"):
        st.session_state.passo = 0
        st.session_state.respostas = []
        st.rerun()
