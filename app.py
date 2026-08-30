import json
import os
import re
import time
from google import genai
from google.genai import types
from google.genai.errors import APIError
import streamlit as st
import streamlit.components.v1 as components

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="👑 Rei dos Simulados",
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
# ESTILIZAÇÃO CSS GLOBAL (CORREÇÃO DE OPACIDADE E TEXTO AO CLICAR/FOCO)
# -----------------------------------------------------------------------------
bg_body = "#F0F4F8"
text_color = "#0F172A"
card_bg = "#FFFFFF"
card_border = "#CBD5E1"
hero_bg = "linear-gradient(135deg, #0F172A 0%, #1E3A8A 50%, #2563EB 100%)"
btn_bg = "#2563EB"

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
            padding-top: 1.5rem !important;
            padding-bottom: 1.5rem !important;
            margin: 0 auto !important;
        }}

        /* HERO BANNER LANDING PAGE */
        .hero-banner {{
            background: {hero_bg};
            border-radius: 16px;
            padding: 20px 24px;
            text-align: center;
            color: white;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
            margin-bottom: 20px;
            position: relative;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.15);
        }}

        .hero-coroa {{
            font-size: 2.2rem;
            margin-bottom: 4px;
            display: block;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
        }}

        .hero-titulo {{
            font-size: 1.9rem !important;
            font-weight: 900 !important;
            letter-spacing: -0.5px;
            margin: 0 !important;
            text-transform: uppercase;
            background: linear-gradient(180deg, #FFFFFF 0%, #E2E8F0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .hero-subtitulo {{
            font-size: 0.95rem !important;
            font-weight: 700 !important;
            color: #FACC15 !important;
            margin-top: 2px !important;
            margin-bottom: 10px !important;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }}

        .hero-bordao {{
            font-size: 0.85rem !important;
            font-weight: 500;
            color: rgba(255, 255, 255, 0.95);
            max-width: 480px;
            margin: 0 auto !important;
            line-height: 1.3;
            background: rgba(255, 255, 255, 0.1);
            padding: 6px 16px;
            border-radius: 20px;
            backdrop-filter: blur(5px);
            display: inline-block;
        }}

        /* CAMPOS DE SELEÇÃO E TEXTO */
        div[data-baseweb="select"], .stSelectbox > div > div {{
            background-color: #FFFFFF !important;
            border: 2px solid #CBD5E1 !important;
            border-radius: 10px !important;
            color: #0F172A !important;
            box-shadow: 0 2px 6px rgba(0,0,0,0.05) !important;
        }}

        div[data-baseweb="select"] * {{
            font-size: 0.95rem !important;
            font-weight: 700 !important;
            color: #0F172A !important;
        }}

        input[data-baseweb="input"], div[data-baseweb="input"], .stTextInput > div > div {{
            background-color: #FFFFFF !important;
            border: 2px solid #CBD5E1 !important;
            border-radius: 10px !important;
            color: #0F172A !important;
            font-size: 0.95rem !important;
            font-weight: 600 !important;
            box-shadow: 0 2px 6px rgba(0,0,0,0.05) !important;
        }}

        .rotulo-seletor {{
            font-size: 0.95rem !important;
            font-weight: 800 !important;
            color: {text_color} !important;
            margin-bottom: 6px !important;
            display: flex;
            align-items: center;
            gap: 6px;
            white-space: nowrap;
        }}

        /* BOTÕES GERAIS E CORREÇÃO DE OPACIDADE AO CLICAR/FOCO */
        div.stButton > button {{
            font-size: 0.95rem;
            padding: 12px 14px;
            background-color: {btn_bg};
            color: #FFFFFF !important;
            border-radius: 10px;
            border: none;
            font-weight: 700;
            text-align: center;
            justify-content: center;
            line-height: 1.4;
            white-space: normal;
            word-wrap: break-word;
            margin-bottom: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            opacity: 1 !important;
        }}

        div.stButton > button:hover, 
        div.stButton > button:focus, 
        div.stButton > button:active {{
            opacity: 1 !important;
            color: #FFFFFF !important;
            background-color: #1D4ED8 !important;
            border-color: transparent !important;
            outline: none !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
        }}

        div.stButton > button p, 
        div.stButton > button span {{
            color: #FFFFFF !important;
            opacity: 1 !important;
            font-weight: 700 !important;
        }}

        /* CARDS LANDING PAGE */
        div.stButton > button[key="btn_basica"], div.stButton > button[key="btn_superior"] {{
            background-color: {btn_bg} !important;
            color: #FFFFFF !important;
            border-radius: 0px 0px 14px 14px !important;
            margin-top: -2px !important;
            width: 100% !important;
            text-align: center !important;
            justify-content: center !important;
            font-weight: 800 !important;
            font-size: 0.95rem !important;
            padding: 12px 14px !important;
            opacity: 1 !important;
        }}

        .card-basica-topo, .card-superior-topo {{
            background-color: {card_bg};
            border: 2px solid {card_border};
            border-bottom: none;
            border-radius: 14px 14px 0px 0px;
            padding: 16px 14px 10px 14px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }}

        .enunciado-grande {{
            font-size: 1.05rem !important;
            font-weight: 700;
            line-height: 1.5;
            color: {text_color};
            margin-bottom: 16px;
            padding: 16px;
            background-color: {card_bg};
            border: 2px solid {card_border};
            border-left: 6px solid {btn_bg};
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }}

        .card-resultado {{
            background-color: {card_bg};
            border: 2px solid {card_border};
            border-radius: 14px;
            text-align: center;
        }}

        .metric-box {{
            background-color: rgba(0,0,0,0.03);
            padding: 12px;
            border-radius: 8px;
            border: 1px solid {card_border};
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# GERENCIAMENTO DE ESTADO (SESSION STATE)
# -----------------------------------------------------------------------------
if "etapa_ensino" not in st.session_state:
    st.session_state.etapa_ensino = None
if "funcao_selecionada" not in st.session_state:
    st.session_state.funcao_selecionada = None
if "questoes_online" not in st.session_state:
    st.session_state.questoes_online = []
if "respostas_usuario" not in st.session_state:
    st.session_state.respostas_usuario = {}
if "indice_questao" not in st.session_state:
    st.session_state.indice_questao = 0
if "qtd_total_questoes" not in st.session_state:
    st.session_state.qtd_total_questoes = 10
if "tempo_inicio" not in st.session_state:
    st.session_state.tempo_inicio = None
if "simulado_concluido" not in st.session_state:
    st.session_state.simulado_concluido = False


def formatar_tempo(segundos):
    minutos = int(segundos // 60)
    segundos_restantes = int(segundos % 60)
    return f"{minutos:02d}:{segundos_restantes:02d}"


def rolar_para_o_topo():
    components.html(
        """
        <script>
            window.parent.document.querySelector('.main').scrollTo({top: 0, behavior: 'smooth'});
        </script>
        """,
        height=0,
    )


def limpar_e_formatar_texto(texto):
    if not texto:
        return ""
    texto = re.sub(r"`([^`]+)`", r"\1", texto)
    texto = texto.replace("$", "")
    texto = re.sub(r"\\frac\{([^}]+)\}\{([^}]+)\}", r"\1/\2", texto)
    texto = re.sub(r"\\text\{([^}]+)\}", r"\1", texto)
    texto = texto.replace(r"\quad", " ")
    texto = texto.replace(r"\times", "×")
    texto = texto.replace(r"\div", "÷")
    texto = texto.replace("\\", "")
    return texto


def resetar_para_inicio():
    st.session_state.etapa_ensino = None
    st.session_state.funcao_selecionada = None
    st.session_state.questoes_online = []
    st.session_state.respostas_usuario = {}
    st.session_state.indice_questao = 0
    st.session_state.tempo_inicio = None
    st.session_state.simulado_concluido = False


def voltar_etapa():
    if st.session_state.simulado_concluido:
        st.session_state.simulado_concluido = False
    elif st.session_state.questoes_online:
        st.session_state.questoes_online = []
        st.session_state.respostas_usuario = {}
        st.session_state.indice_questao = 0
    elif st.session_state.funcao_selecionada:
        st.session_state.funcao_selecionada = None
    elif st.session_state.etapa_ensino:
        st.session_state.etapa_ensino = None


def gerar_lote_questoes(materia, topico, etapa, quantidade, nivel):
    descricoes_nivel = {
        1: "Nível 1 (Fácil / Conceitual): Questões diretas de fixação de conceitos básicos.",
        2: "Nível 2 (Tranquilo / Prático): Questões simples com cenários práticos do dia a dia.",
        3: "Nível 3 (Moderado / Acadêmico): Questões no padrão tradicional de exames e provas escolares/acadêmicas.",
        4: "Nível 4 (Desafiador / Análise): Questões complexas com casos práticos e pegadinhas.",
        5: "Nível 5 (Nível Concurso Público / Professor): Questões no estilo exato de bancas examinadoras de Concursos Públicos (Cebraspe, FGV, Vunesp, FCC). Altamente exigente.",
    }

    system_instruction = (
        "Você é um renomado examinador de provas e concursos públicos do Magistério. "
        "Sua regra absoluta é respeitar estritamente o tema solicitado e o nível de dificuldade exigido."
    )

    prompt_json = (
        f"Gere um array com exatamente {quantidade} questões inéditas para a disciplina {materia} ({etapa}).\n\n"
        f"🎯 TEMA EXCLUSIVO: \"{topico}\"\n"
        f"📊 DIFICULDADE EXIGIDA: {descricoes_nivel[nivel]}\n\n"
        "REGRAS DE FORMATAÇÃO:\n"
        "Retorne EXCLUSIVAMENTE um JSON com uma lista sob a chave \"questoes\", no formato:\n"
        "{\n"
        '  "questoes": [\n'
        "    {\n"
        '      "enunciado": "Texto do enunciado",\n'
        '      "alternativas": {"a": "Opção A", "b": "Opção B", "c": "Opção C", "d": "Opção D", "e": "Opção E"},\n'
        '      "correta": "a",\n'
        '      "explicacao": "Explicação objetiva em até 2 frases."\n'
        "    }\n"
        "  ]\n"
        "}"
    )

    max_tentativas = 3
    for tentativa in range(max_tentativas):
        try:
            res = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt_json,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.3,
                ),
            )
            dados = json.loads(res.text)
            return dados.get("questoes", [])
        except APIError as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                if tentativa < max_tentativas - 1:
                    time.sleep(11)
                    continue
                else:
                    st.error("⚠️ Limite de requisições atingido. Aguarde cerca de 10 segundos antes de clicar novamente.")
                    return []
            else:
                st.error(f"Erro ao comunicar com a API Gemini: {e}")
                return []
        except Exception as e:
            st.error(f"Erro no processamento da resposta: {e}")
            return []


# -----------------------------------------------------------------------------
# ESTRUTURA DE CONTEÚDOS
# -----------------------------------------------------------------------------
CONTEUDOS_EDUCACAO_BASICA = {
    "Matemática": {
        "Álgebra, Geometria e Estatística": [
            "Operações Fundamentais e Frações",
            "Equações de 1º e 2º Graus e Sistemas",
            "Porcentagem, Regra de Três e Juros",
            "Geometria Plana e Espacial",
            "Funções, Estatística e Probabilidade",
        ]
    },
    "Língua Portuguesa": {
        "Gramática e Interpretação": [
            "Compreensão e Interpretação de Textos",
            "Ortografia, Acentuação e Pontuação",
            "Classes de Palavras e Sintaxe",
            "Concordância, Regência e Crase",
        ]
    }
}

CONTEUDOS_ENSINO_SUPERIOR = {
    "Legislação Educacional": {
        "Leis Federais Fundamentais": [
            "LDB - Lei 9.394/1996 (Princípios, Fins e Organização)",
            "ECA - Estatuto da Criança e do Adolescente (Direito à Educação)",
            "Constituição Federal de 1988 (Artigos 205 ao 214)",
        ]
    }
}


# -----------------------------------------------------------------------------
# LANDING PAGE CENTRALIZADA (TELA PRINCIPAL)
# -----------------------------------------------------------------------------
if st.session_state.etapa_ensino is None:
    st.markdown(
        """
        <div class="hero-banner">
            <span class="hero-coroa">👑</span>
            <h1 class="hero-titulo">REI DOS SIMULADOS</h1>
            <div class="hero-subtitulo">⚡ TREINE COM PRECISÃO ⚡</div>
            <div class="hero-bordao">"Domine a banca, treine com precisão e conquiste a sua vaga!"</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"<h3 style='text-align: center; color: {text_color}; font-weight: 800; margin-bottom: 16px; font-size: 1.15rem; text-transform: uppercase;'>SELECIONE A SUA ETAPA DE ESTUDOS:</h3>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f"""
            <div class="card-basica-topo">
                <div style="font-size: 1.2rem; font-weight: 800; color: {btn_bg}; margin-bottom: 4px;">🏫 EDUCAÇÃO BÁSICA</div>
                <div style="font-size: 0.85rem; color: {text_color}; opacity: 0.85; margin-bottom: 8px;">Ensino Fundamental e Médio • ENEM • Provas Escolares</div>
                <div style="font-size: 1.4rem;">📐 📖 🎨 🧪 🌍</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("👈 ACESSAR EDUCAÇÃO BÁSICA 👉", key="btn_basica", use_container_width=True):
            st.session_state.etapa_ensino = "Educação Básica"
            st.rerun()

    with col2:
        st.markdown(
            f"""
            <div class="card-superior-topo">
                <div style="font-size: 1.2rem; font-weight: 800; color: {btn_bg}; margin-bottom: 4px;">🎓 ENSINO SUPERIOR</div>
                <div style="font-size: 0.85rem; color: {text_color}; opacity: 0.85; margin-bottom: 8px;">Concursos de Magistério & Nível Superior</div>
                <div style="font-size: 1.4rem;">📜 🧠 📖 🔢</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("👈 ACESSAR ENSINO SUPERIOR 👉", key="btn_superior", use_container_width=True):
            st.session_state.etapa_ensino = "Ensino Superior"
            st.rerun()

# -----------------------------------------------------------------------------
# PAINEL DE CONFIGURAÇÃO E EXECUÇÃO DE QUESTÕES
# -----------------------------------------------------------------------------
else:
    # Exemplo simples de fluxo caso o usuário já tenha escolhido a etapa
    st.write(f"Etapa selecionada: **{st.session_state.etapa_ensino}**")
    if st.button("🏠 Voltar ao Início"):
        resetar_para_inicio()
        st.rerun()
