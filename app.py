import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

st.set_page_config(page_title="Triagem Rigorosa v2.0", page_icon="⚖️")
conn = st.connection("gsheets", type=GSheetsConnection)
SENHA_ADMIN = "suasenha123"

if "passo" not in st.session_state:
    st.session_state.passo = 0
    st.session_state.respostas = []
    st.session_state.dados_pessoais = {"nome": "", "email": ""}

# --- FUNÇÃO DE ANÁLISE TÉCNICA (O RIGOR) ---
def realizar_analise_rigorosa(respostas):
    texto_total = " ".join(respostas).lower()
    palavras = re.findall(r'\w+', texto_total)
    total_palavras = len(palavras)
    vocabulario_unico = len(set(palavras))
    
    # 1. Pontuação de Esforço (Base: 0 a 50)
    # Exige pelo menos 150 palavras no total para pontuação máxima de esforço
    score_esforço = min(50, (total_palavras / 150) * 50)
    
    # 2. Pontuação de Complexidade (Base: 0 a 30)
    # Analisa se o candidato usa um vocabulário variado ou repete palavras
    ratio_complexidade = vocabulario_unico / total_palavras if total_palavras > 0 else 0
    score_complexidade = ratio_complexidade * 30
    
    # 3. Mapeamento Temático (Rigoroso)
    temas = {
        "Liderança Comunitária": ["projeto", "voluntario", "equipe", "comunidade", "liderar", "coletivo", "social", "impacto", "ajudar"],
        "Resiliência Acadêmica": ["superar", "dificuldade", "obstaculo", "estudar", "esforço", "trabalho", "persistencia", "luta", "familia"],
        "Inovação e Criatividade": ["criar", "ideia", "diferente", "tecnologia", "solução", "mudar", "novo", "pesquisa", "desenvolver"]
    }
    
    pontos_temas = {k: 0 for k in temas.keys()}
    for tema, palavras_chave in temas.items():
        for pc in palavras_chave:
            # Conta quantas vezes cada termo aparece
            pontos_temas[tema] += texto_total.count(pc)

    # Escolhe o tema com mais ocorrências
    categoria_vencedora = max(pontos_temas, key=pontos_temas.get)
    total_pontos_temas = pontos_temas[categoria_vencedora]
    
    # 4. Cálculo do Score Final (0 a 100)
    # Se não houver pontos de tema, a pontuação cai drasticamente
    score_final = score_esforço + score_complexidade + (min(20, total_pontos_temas * 2))
    
    # --- CRITÉRIOS DE CORTE ---
    if total_palavras < 40 or score_final < 45 or ratio_complexidade < 0.4:
        resultado = "REPROVADO"
        classificacao = "Perfil Inconsistente"
        resumo = "Respostas superficiais, repetitivas ou com falta de evidências de trajetória."
    elif score_final < 65:
        resultado = "EM ANÁLISE"
        classificacao = categoria_vencedora
        resumo = "O candidato possui potencial, mas as respostas carecem de detalhes técnicos ou exemplos práticos."
    else:
        resultado = "SELECIONADO"
        classificacao = categoria_vencedora
        resumo = f"Perfil sólido em {categoria_vencedora}. Demonstra vocabulário rico, clareza e alto engajamento."

    return classificacao, resultado, round(score_final, 2), resumo

# --- INTERFACE ---
st.sidebar.title("Sistema de Triagem")
aba = st.sidebar.radio("Navegação", ["Inscrição", "Área do Gestor"])

if aba == "Inscrição":
    st.title("🎓 Avaliação de Perfil Acadêmico")
    
    if st.session_state.passo == 0:
        nome = st.text_input("Nome Completo:")
        email = st.text_input("E-mail:")
        if st.button("Iniciar Avaliação Rigorosa"):
            if nome and "@" in email:
                st.session_state.dados_pessoais.update({"nome": nome, "email": email})
                st.session_state.passo = 1
                st.rerun()
    
    elif 1 <= st.session_state.passo <= 5:
        perguntas = [
            "Descreva detalhadamente sua trajetória e o que te motiva academicamente.",
            "Relate uma situação adversa específica e como você aplicou estratégia para superá-la.",
            "Descreva sua atuação em projetos coletivos e qual foi seu papel na resolução de problemas.",
            "Como você aplicará tecnicamente os conhecimentos desta bolsa em sua realidade local?",
            "Por que seu perfil se diferencia dos demais candidatos em termos de persistência e visão?"
        ]
        st.subheader(f"Questão {st.session_state.passo} de 5")
        resp = st.text_area("Sua resposta (mínimo de 3 linhas recomendado):", height=200)
        
        if st.button("Confirmar Resposta"):
            if len(resp.split()) < 5:
                st.error("Resposta muito curta. Por favor, aprofunde sua explicação.")
            else:
                st.session_state.respostas.append(resp)
                st.session_state.passo += 1
                st.rerun()

    else:
        st.info("Processando análise de mérito...")
        # Chamada da função rigorosa
        classe, result, nota, res = realizar_analise_rigorosa(st.session_state.respostas)
        
        # Salvamento
        nova_linha = pd.DataFrame([{
            "Nome": st.session_state.dados_pessoais["nome"],
            "Email": st.session_state.dados_pessoais["email"],
            "Pergunta1": st.session_state.respostas[0],
            "Pergunta2": st.session_state.respostas[1],
            "Pergunta3": st.session_state.respostas[2],
            "Pergunta4": st.session_state.respostas[3],
            "Pergunta5": st.session_state.respostas[4],
            "Classificacao": classe,
            "Resultado": result,
            "Pontuacao": nota,
            "Resumo": res
        }])
        
        try:
            existente = conn.read(worksheet="Página1", ttl=0)
            conn.update(worksheet="Página1", data=pd.concat([existente, nova_linha], ignore_index=True))
        except:
            conn.update(worksheet="Página1", data=nova_linha)

        st.success("Avaliação enviada. O comitê analisará seus dados.")
        if st.button("Finalizar"):
            st.session_state.passo = 0
            st.session_state.respostas = []
            st.rerun()

else:
    st.title("🔑 Painel de Auditoria")
    senha = st.text_input("Senha Admin:", type="password")
    if senha == SENHA_ADMIN:
        df = conn.read(worksheet="Página1", ttl=0)
        st.metric("Média de Pontuação dos Candidatos", round(df["Pontuacao"].astype(float).mean(), 2) if not df.empty else 0)
        st.dataframe(df.sort_values(by="Pontuacao", ascending=False))
