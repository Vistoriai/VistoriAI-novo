import streamlit as st
import pandas as pd
import openai
from fpdf import FPDF
import os
import random
import string

# Configuração do cliente OpenAI
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Constantes
TOKEN_FILE = "tokens.csv"
HISTORICO_FILE = "historico.csv"

servicos = {
    'motor': ('Análise Motor', 1),
    'suspensao': ('Análise Suspensão', 5),
    'rodas_pneus': ('Análise Rodas e Pneus', 8),
    'interior': ('Análise Interior', 11),
    'completo': ('Pacote Completo', 25)
}

# Funções auxiliares
def carregar_tokens():
    if not os.path.exists(TOKEN_FILE):
        return pd.DataFrame(columns=["token", "servico", "status"])
    return pd.read_csv(TOKEN_FILE)

def salvar_tokens(df):
    df.to_csv(TOKEN_FILE, index=False)

def gerar_token_aleatorio(tamanho=8):
    letras = string.ascii_uppercase + string.digits
    return ''.join(random.choices(letras, k=tamanho))

def atualizar_token(token):
    df = carregar_tokens()
    df.loc[df["token"].str.strip() == token.strip(), "status"] = "usado"
    salvar_tokens(df)

def salvar_historico(dados):
    if not os.path.exists(HISTORICO_FILE):
        historico_df = pd.DataFrame(columns=dados.keys())
    else:
        historico_df = pd.read_csv(HISTORICO_FILE)
    novo_historico = pd.DataFrame([dados])
    historico_df = pd.concat([historico_df, novo_historico], ignore_index=True)
    historico_df.to_csv(HISTORICO_FILE, index=False)

# Interface principal
st.set_page_config(page_title="VistoriAI", page_icon="🔍")

st.title("🔍 Bem-vindo ao VistoriAI!")
st.write("Seu aplicativo de análise veicular por Inteligência Artificial.")

abas = st.tabs(["Início", "Cliente", "Administrador"])

# ================== ABA INÍCIO ==================
with abas[0]:
    st.header("Sobre o VistoriAI")
    st.markdown("""
    - Gere relatórios profissionais de vistoria de forma automática.
    - Análise baseada em Inteligência Artificial.
    - Simples, rápido e eficaz!
    """)

# ================== ABA CLIENTE ==================
with abas[1]:
    st.header("🔑 Acesso do Cliente")

    df = carregar_tokens()

    token_digitado = st.text_input("Digite seu token para iniciar:")

    if token_digitado:
        tokens_validos = df["token"].astype(str).str.strip().tolist()

        if token_digitado.strip() not in tokens_validos:
            st.error(f"⚠️ Token inválido: {token_digitado}")
            st.stop()

        linha = df[df["token"].astype(str).str.strip() == token_digitado.strip()]
        status = linha["status"].values[0]
        servico = linha["servico"].values[0]

        if status != "ativo":
            st.error("⚠️ Este token já foi usado ou está expirado.")
            st.stop()

        nome_servico, qtd_fotos = servicos.get(servico, ("Desconhecido", 0))

        st.success(f"💼 Serviço validado: {nome_servico}")
        st.info(f"Por favor, envie exatamente {qtd_fotos} foto(s) para análise.")

        nome = st.text_input("Nome completo")
        telefone = st.text_input("Telefone")
        email = st.text_input("E-mail")
        marca = st.text_input("Marca")
        modelo = st.text_input("Modelo")
        ano = st.text_input("Ano")
        motorizacao = st.text_input("Motorizacao")
        cambio = st.selectbox("Tipo de câmbio", ["Manual", "Automático"])

        midias = st.file_uploader(
            f"Envie {qtd_fotos} foto(s):",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True
        )

        if st.button("Enviar para análise"):
            if len(midias) != qtd_fotos:
                st.error(f"⚠️ Envie exatamente {qtd_fotos} fotos!")
                st.stop()

            with st.spinner("🦹‍♂️ Analisando..."):
                nomes_midias = [m.name for m in midias]
                prompt = f"""
                Você é especialista automotivo. Analise:
                Marca: {marca}, Modelo: {modelo}, Ano: {ano}, Motorizacao: {motorizacao}, Câmbio: {cambio}.
                Fotos: {nomes_midias}

                Gere:
                - Problemas detectados;
                - Defeitos comuns;
                - Soluções recomendadas;
                - Estimativa de custo.
                """

                resposta = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}]
                )

                relatorio = resposta.choices[0].message.content

                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 10, relatorio)
                nome_pdf = f"Relatorio_{modelo}_{ano}.pdf"
                pdf.output(nome_pdf)

                atualizar_token(token_digitado)
                salvar_historico({
                    "token": token_digitado,
                    "servico": nome_servico,
                    "nome": nome,
                    "telefone": telefone,
                    "email": email,
                    "marca": marca,
                    "modelo": modelo,
                    "ano": ano,
                    "pdf_gerado": nome_pdf
                })

                st.success("✅ Análise concluída!")
                with open(nome_pdf, "rb") as file:
                    st.download_button("📅 Baixar Relatório PDF", file, file_name=nome_pdf)

# ================== ABA ADMINISTRADOR ==================
with abas[2]:
    st.header("🔑 Acesso Administrativo")

    senha = st.text_input("Senha de administrador:", type="password")

    if senha == "vistoria2024":
        st.success("✅ Acesso liberado.")

        st.subheader("Gerar novo token")
        servico_escolhido = st.selectbox("Escolha o serviço", list(servicos.keys()))

        if st.button("Gerar token"):
            novo_token = gerar_token_aleatorio()
            df = carregar_tokens()
            novo_registro = pd.DataFrame([{
                "token": novo_token,
                "servico": servico_escolhido,
                "status": "ativo"
            }])
            df = pd.concat([df, novo_registro], ignore_index=True)
            salvar_tokens(df)
            st.success(f"✅ Token gerado: {novo_token}")

        st.subheader("Tokens cadastrados")
        df = carregar_tokens()
        st.dataframe(df)

        st.subheader("Histórico de Análises")
        if os.path.exists(HISTORICO_FILE):
            historico = pd.read_csv(HISTORICO_FILE)
            st.dataframe(historico)
        else:
            st.info("Nenhum histórico registrado.")
    else:
        st.stop()
