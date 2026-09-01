import json
import os
import re
import time
import pandas as pd
from google import genai
from google.genai import types
from google.genai.errors import APIError
import streamlit as st

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="👑 Prof. Carlo REI - Simulados de Matemática",
    page_icon="👑",
    layout="centered",
    initial_sidebar_state="collapsed",
)

MODEL_NAME = "gemini-2.5-flash"

# -----------------------------------------------------------------------------
# INICIALIZAÇÃO DA API GEMINI
# -----------------------------------------------------------------------------
try:
    api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
except Exception:
    api_key = os.environ.get("GEMINI_API_KEY", "")

if not api_key:
    api_key = "AQ.Ab8RN6LjVTB0KTK4HsQb9F-oCzn2qeiur5Uga5YxZ6ietrw56w"

client = genai.Client(api_key=api_key)

# -----------------------------------------------------------------------------
# ESTILIZAÇÃO CSS GLOBAL (MODERNA E ELEGANTE)
# -----------------------------------------------------------------------------
bg_body = "#0B0F19"
text_color = "#F8FAFC"
card_bg = "#1E293B"
card_border = "#334155"

st.markdown(
    f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800;900&display=swap');

        * {{
            font-family: 'Plus Jakarta Sans', sans-serif;
        }}

        .stApp {{
            background-color: {bg_body} !important;
            color: {text_color} !important;
        }}

        .block-container {{
            max-width: 720px !important;
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
            margin: 0 auto !important;
        }}

        /* HERO BANNER - PROF CARLO REI */
        .hero-banner-rei {{
            background: linear-gradient(135deg, #1E1B4B 0%, #312E81 50%, #1D4ED8 100%);
            border-radius: 20px;
            padding: 30px 20px;
            text-align: center;
            color: white;
            box-shadow: 0 10px 30px rgba(37, 99, 235, 0.3);
            margin-bottom: 25px;
            border: 2px solid rgba(250, 204, 21, 0.4);
        }}

        .hero-titulo {{
            font-size: 2.2rem !important;
            font-weight: 900 !important;
            margin: 0 !important;
            text-transform: uppercase;
            background: linear-gradient(180deg, #FFFFFF 0%, #FACC15 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .hero-subtitulo {{
            font-size: 1.1rem !important;
            font-weight: 800 !important;
            color: #38BDF8 !important;
            margin-top: 6px !important;
            margin-bottom: 12px !important;
            text-transform: uppercase;
        }}

        .hero-bordao {{
            font-size: 0.9rem !important;
            font-weight: 600;
            color: rgba(255, 255, 255, 0.95);
            background: rgba(255, 255, 255, 0.08);
            padding: 8px 18px;
            border-radius: 25px;
            backdrop-filter: blur(6px);
            border: 1px solid rgba(255, 255, 255, 0.15);
            display: inline-block;
        }}

        /* BOTÕES PRINCIPAIS DE ESCOLHA DE NÍVEL (GRANDES QUADRADOS) */
        div.stButton > button {{
            font-size: 1.05rem;
            padding: 16px 20px;
            background-color: #2563EB;
            color: #FFFFFF !important;
            border-radius: 14px;
            border: none;
            font-weight: 800;
            text-align: center;
            justify-content: center;
            line-height: 1.4;
            white-space: normal;
            word-wrap: break-word;
            margin-bottom: 10px;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
            opacity: 1 !important;
            width: 100% !important;
            transition: all 0.2s ease;
        }}

        div.stButton > button:hover {{
            background-color: #1D4ED8 !important;
            box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5) !important;
            transform: translateY(-2px);
        }}

        div.stButton > button p, 
        div.stButton > button span {{
            color: #FFFFFF !important;
            opacity: 1 !important;
            font-weight: 800 !important;
        }}

        /* CARDS VISUAIS DA PRIMEIRA E SEGUNDA PÁGINA */
        .card-container-nivel {{
            background-color: {card_bg};
            border: 2px solid {card_border};
            border-radius: 16px;
            padding: 24px 20px;
            text-align: center;
            box-shadow: 0 6px 16px rgba(0,0,0,0.25);
            margin-bottom: 12px;
            cursor: pointer;
        }}

        .enunciado-card {{
            font-size: 1.05rem !important;
            font-weight: 700;
            line-height: 1.5;
            color: #F8FAFC;
            margin-bottom: 16px;
            padding: 18px;
            background-color: #1E293B;
            border: 2px solid #334155;
            border-left: 6px solid #38BDF8;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# GERENCIAMENTO DE ESTADO (SESSION STATE)
# -----------------------------------------------------------------------------
if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "home"  # 'home', 'selecao_quiz', 'executando_quiz', 'resultado'
if "etapa_selecionada" not in st.session_state:
    st.session_state.etapa_selecionada = None  # 'Basica' ou 'Superior'
if "nome_aluno" not in st.session_state:
    st.session_state.nome_aluno = ""
if "quiz_selecionado" not in st.session_state:
    st.session_state.quiz_selecionado = None
if "questoes_ativas" not in st.session_state:
    st.session_state.questoes_ativas = []
if "respostas_usuario" not in st.session_state:
    st.session_state.respostas_usuario = {}
if "indice_questao" not in st.session_state:
    st.session_state.indice_questao = 0
if "simulado_concluido" not in st.session_state:
    st.session_state.simulado_concluido = False

# -----------------------------------------------------------------------------
# FUNÇÃO PARA CRIAR OU LER O EXCEL DE QUESTÕES
# -----------------------------------------------------------------------------
EXCEL_FILE = "banco_questoes.xlsx"

def criar_excel_exemplo_se_nao_existir():
    if not os.path.exists(EXCEL_FILE):
        with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
            # Abas da Educação Básica (Iniciadas com B-)
            df_b1 = pd.DataFrame({
                "enunciado": ["Quanto é 15% de 200?", "Qual o valor de x na equação 2x + 10 = 20?"],
                "alt_a": ["20", "2"],
                "alt_b": ["30", "5"],
                "alt_c": ["40", "10"],
                "alt_d": ["50", "20"],
                "correta": ["b", "c"],
                "explicacao": ["15/100 * 200 = 30", "2x = 10 -> x = 5"]
            })
            df_b1.to_excel(writer, sheet_name="B-MATEMATICA_BASICA", index=False)

            df_b2 = pd.DataFrame({
                "enunciado": ["Qual figura geométrica possui 3 lados?", "Qual a raiz quadrada de 144?"],
                "alt_a": ["Quadrado", "10"],
                "alt_b": ["Triângulo", "12"],
                "alt_c": ["Círculo", "14"],
                "alt_d": ["Pentágono", "16"],
                "correta": ["b", "b"],
                "explicacao": ["O triângulo possui 3 lados.", "12 * 12 = 144"]
            })
            df_b2.to_excel(writer, sheet_name="B-TABUADA_E_GEOMETRIA", index=False)

            # Abas do Ensino Superior (Iniciadas com S-)
            df_s1 = pd.DataFrame({
                "enunciado": ["Segundo a LDB (Lei 9394/96), a educação básica obrigatória e gratuita vai de:", "Qual artigo da CF/88 trata diretamente da Educação?"],
                "alt_a": ["4 aos 17 anos", "Art. 5º"],
                "alt_b": ["6 aos 14 anos", "Art. 37"],
                "alt_c": ["0 aos 6 anos", "Art. 205 ao 214"],
                "alt_d": ["7 aos 18 anos", "Art. 100"],
                "correta": ["a", "c"],
                "explicacao": ["A EC 59/2009 tornou a educação básica obrigatória dos 4 aos 17 anos.", "Os arts. 205 a 214 da CF/88 tratam da ordem educacional."],
            })
            df_s1.to_excel(writer, sheet_name="S-LEGISLACAO_EDUCACIONAL", index=False)

criar_excel_exemplo_se_nao_existir()

def carregar_opcoes_por_etapa(etapa):
    try:
        xls = pd.ExcelFile(EXCEL_FILE)
        abas = xls.sheet_names
        opcoes = []
        prefixo = "B-" if etapa == "Basica" else "S-"
        for aba in abas:
            if aba.startswith(prefixo):
                nome_amigavel = aba[2:].replace("_", " ")
                opcoes.append({"aba_original": aba, "titulo": nome_amigavel})
        return opcoes
    except Exception as e:
        st.error(f"Erro ao ler abas do Excel: {e}")
        return []

def carregar_questoes_da_aba(nome_aba):
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=nome_aba)
        questoes = []
        for _, row in df.iterrows():
            q = {
                "enunciado": str(row["enunciado"]),
                "alternativas": {
                    "a": str(row["alt_a"]),
                    "b": str(row["alt_b"]),
                    "c": str(row["alt_c"]),
                    "d": str(row["alt_d"])
                },
                "correta": str(row["correta"]).strip().lower(),
                "explicacao": str(row["explicacao"])
            }
            questoes.append(q)
        return questoes
    except Exception as e:
        st.error(f"Erro ao carregar questões da aba {nome_aba}: {e}")
        return []

def resetar_navegacao():
    st.session_state.pagina_atual = "home"
    st.session_state.etapa_selecionada = None
    st.session_state.quiz_selecionado = None
    st.session_state.questoes_ativas = []
    st.session_state.respostas_usuario = {}
    st.session_state.indice_questao = 0
    st.session_state.simulado_concluido = False

# -----------------------------------------------------------------------------
# PÁGINA 1: ESCOLHA ENTRE EDUCAÇÃO BÁSICA E ENSINO SUPERIOR (DOIS QUADRADOS)
# -----------------------------------------------------------------------------
if st.session_state.pagina_atual == "home":
    st.markdown(
        """
        <div class="hero-banner-rei">
            <div style="font-size: 2.5rem; margin-bottom: 4px;">👑</div>
            <h1 class="hero-titulo">QUESTIONÁRIO DE MATEMÁTICA</h1>
            <div class="hero-subtitulo">Professor Carlo REI</div>
            <div style="font-size: 1.8rem; margin-top: 10px; letter-spacing: 6px;">📐 🧮 🏆</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "<h3 style='text-align: center; color: #38BDF8; font-weight: 800; margin-bottom: 20px; font-size: 1.1rem; text-transform: uppercase;'>ESCOLHA O NÍVEL DE ENSINO:</h3>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            <div class="card-container-nivel">
                <div style="font-size: 2.2rem; margin-bottom: 8px;">🏫</div>
                <div style="font-size: 1.2rem; font-weight: 900; color: #38BDF8; margin-bottom: 6px;">EDUCAÇÃO BÁSICA</div>
                <div style="font-size: 0.85rem; color: #94A3B8;">Fundamental, Médio e Raciocínio Lógico</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("👉 ACESSAR BÁSICA", key="btn_basica"):
            st.session_state.etapa_selecionada = "Basica"
            st.session_state.pagina_atual = "selecao_quiz"
            st.rerun()

    with col2:
        st.markdown(
            """
            <div class="card-container-nivel">
                <div style="font-size: 2.2rem; margin-bottom: 8px;">🎓</div>
                <div style="font-size: 1.2rem; font-weight: 900; color: #38BDF8; margin-bottom: 6px;">ENSINO SUPERIOR</div>
                <div style="font-size: 0.85rem; color: #94A3B8;">Concursos, Legislação e Provas Avançadas</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("👉 ACESSAR SUPERIOR", key="btn_superior"):
            st.session_state.etapa_selecionada = "Superior"
            st.session_state.pagina_atual = "selecao_quiz"
            st.rerun()

# -----------------------------------------------------------------------------
# PÁGINA 2: NOME DO ALUNO E ESCOLHA DO BLOCO DE PERGUNTAS (B- ou S-)
# -----------------------------------------------------------------------------
elif st.session_state.pagina_atual == "selecao_quiz":
    etapa = st.session_state.etapa_selecionada
    nome_etapa = "Educação Básica" if etapa == "Basica" else "Ensino Superior"
    prefixo_filtro = "B-" if etapa == "Basica" else "S-"

    if st.button("⬅️ Voltar para a Página Inicial"):
        resetar_navegacao()
        st.rerun()

    st.write("")

    # Card do Nome do Aluno
    st.markdown(
        """
        <div style="background-color: #1E293B; border: 2px solid #334155; border-radius: 14px; padding: 16px; margin-bottom: 16px;">
            <div style="font-weight: 800; color: #F8FAFC; margin-bottom: 8px; font-size: 0.95rem;">👤 Nome Completo do Aluno:</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    nome_input = st.text_input("Digite seu nome completo", value=st.session_state.nome_aluno, placeholder="Digite seu nome completo aqui...", label_visibility="collapsed")
    st.session_state.nome_aluno = nome_input

    st.write("")

    # Card de Escolha do Bloco de Exercícios
    st.markdown(
        f"""
        <div style="background-color: #1E293B; border: 2px solid #334155; border-radius: 14px; padding: 16px; margin-bottom: 16px;">
            <div style="font-weight: 800; color: #38BDF8; margin-bottom: 4px; font-size: 1rem;">📚 Escolha o Bloco de Exercícios ({nome_etapa}):</div>
            <div style="font-size: 0.85rem; color: #94A3B8;">Selecione abaixo o questionário correspondente às abas iniciadas com <code>{prefixo_filtro}</code></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    opcoes_quiz = carregar_opcoes_por_etapa(etapa)

    if not opcoes_quiz:
        st.warning(f"Nenhuma aba encontrada no arquivo `{EXCEL_FILE}` com o prefixo `{prefixo_filtro}`.")
    else:
        for opt in opcoes_quiz:
            col_ icone, col_botao = st.columns([1, 4])
            with col_icone:
                st.markdown("<div style='font-size: 2rem; text-align: center; padding-top: 10px;'>📖</div>", unsafe_allow_html=True)
            with col_botao:
                if st.button(f"🎯 {opt['titulo']} ({opt['aba_original']})", key=f"btn_quiz_{opt['aba_original']}"):
                    if not st.session_state.nome_aluno.strip():
                        st.warning("⚠️ Por favor, digite o seu nome completo antes de iniciar o questionário!")
                    else:
                        questoes = carregar_questoes_da_aba(opt['aba_original'])
                        if questoes:
                            st.session_state.quiz_selecionado = opt['titulo']
                            st.session_state.questoes_ativas = questoes
                            st.session_state.respostas_usuario = {}
                            st.session_state.indice_questao = 0
                            st.session_state.simulado_concluido = False
                            st.session_state.pagina_atual = "executando_quiz"
                            st.rerun()
                        else:
                            st.error("O questionário selecionado está vazio ou ocorreu um erro na leitura.")

# -----------------------------------------------------------------------------
# PÁGINA 3: EXECUÇÃO DO QUIZ E RESULTADOS
# -----------------------------------------------------------------------------
elif st.session_state.pagina_atual == "executando_quiz":
    questoes = st.session_state.questoes_ativas
    total_q = len(questoes)
    idx = st.session_state.indice_questao

    if st.button("⬅️ Escolher Outro Questionário"):
        st.session_state.pagina_atual = "selecao_quiz"
        st.rerun()

    st.write("")

    if not st.session_state.simulado_concluido:
        q_atual = questoes[idx]
        st.markdown(f"**Aluno(a):** `{st.session_state.nome_aluno}` | **Questão {idx + 1} de {total_q}**")
        st.markdown(f"**Questionário:** *{st.session_state.quiz_selecionado}*")
        
        # Barra de Progresso
        st.progress((idx + 1) / total_q)

        st.markdown(f'<div class="enunciado-card">{q_atual["enunciado"]}</div>', unsafe_allow_html=True)

        alternativas = q_atual["alternativas"]
        chaves_alt = list(alternativas.keys())
        
        resposta_atual = st.session_state.respostas_usuario.get(idx, None)
        indice_default = chaves_alt.index(resposta_atual) if resposta_atual in chaves_alt else 0

        escolha = st.radio(
            "Selecione a alternativa correta:",
            options=chaves_alt,
            format_func=lambda x: f"({x.upper()}) {alternativas[x]}",
            key=f"radio_q_{idx}",
            index=indice_default
        )

        col_ant, col_prox = st.columns(2)
        with col_ant:
            if idx > 0:
                if st.button("⬅️ Questão Anterior"):
                    st.session_state.respostas_usuario[idx] = escolha
                    st.session_state.indice_questao -= 1
                    st.rerun()

        with col_prox:
            if idx < total_q - 1:
                if st.button("Próxima Questão ➡️"):
                    st.session_state.respostas_usuario[idx] = escolha
                    st.session_state.indice_questao += 1
                    st.rerun()
            else:
                if st.button("🏁 Finalizar e Ver Resultado"):
                    st.session_state.respostas_usuario[idx] = escolha
                    st.session_state.simulado_concluido = True
                    st.rerun()
    else:
        # TELA DE RESULTADOS
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #1E1B4B 0%, #1D4ED8 100%); padding: 24px; border-radius: 16px; text-align: center; margin-bottom: 20px; border: 2px solid #38BDF8;">
                <h2 style="color: #FFFFFF; margin: 0; font-weight: 900;">👑 AVALIAÇÃO CONCLUÍDA! 👑</h2>
                <p style="color: #38BDF8; margin-top: 6px; font-weight: 700;">Aluno(a): {st.session_state.nome_aluno}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        acertos = 0
        for i, q in enumerate(questoes):
            resp_user = st.session_state.respostas_usuario.get(i)
            if resp_user == q["correta"]:
                acertos += 1

        percentual = (acertos / total_q) * 100

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric("📊 Acertos", f"{acertos} / {total_q}")
        with col_m2:
            st.metric("🎯 Aproveitamento", f"{percentual:.1f}%")

        st.write("---")
        st.markdown("<h4 style='color: #F8FAFC;'>📝 Gabarito e Explicações:</h4>", unsafe_allow_html=True)

        for i, q in enumerate(questoes):
            resp_user = st.session_state.respostas_usuario.get(i, "Não respondida")
            correta = q["correta"]
            acertou = (resp_user == correta)
            
            status_icone = "✅" if acertou else "❌"
            cor_borda = "#22C55E" if acertou else "#EF4444"

            st.markdown(
                f"""
                <div style="background-color: #1E293B; border: 2px solid {cor_borda}; border-radius: 12px; padding: 14px; margin-bottom: 12px;">
                    <div style="font-weight: 800; color: #F8FAFC; margin-bottom: 6px;">Questão {i+1}: {q['enunciado']}</div>
                    <div style="font-size: 0.9rem; color: #94A3B8; margin-bottom: 4px;">Sua resposta: <b>({str(resp_user).upper()})</b> | Resposta correta: <b>({str(correta).upper()})</b> {status_icone}</div>
                    <div style="font-size: 0.85rem; color: #38BDF8; background: rgba(56, 189, 248, 0.1); padding: 8px; border-radius: 8px; margin-top: 6px;"><b>Explicação:</b> {q['explicacao']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if st.button("🔄 Refazer / Escolher Outro Questionário"):
            resetar_navegacao()
            st.rerun()
