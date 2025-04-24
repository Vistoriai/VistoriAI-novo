import streamlit as st
import pandas as pd
import openai
from fpdf import FPDF
import os
import random
import string

import os
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TOKEN_FILE = "tokens.csv"
HISTORICO_FILE = "historico.csv"

servicos = {
    'motor': ('Análise Motor', 1),
    'suspensao': ('Análise Suspensão', 5),
    'rodas_pneus': ('Análise Rodas e Pneus', 8),
    'interior': ('Análise Interior', 11),
    'completo': ('Pacote Completo', 25)
}

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

# ================== ÁREA DO ADMINISTRADOR ==================
if "admin" in st.query_params:
    senha = st.text_input("Digite a senha de administrador:", type="password")
    if senha == "vistoria2024":
        st.success("✅ Acesso autorizado")

        st.subheader("🔑 Gerar novo token")
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
            st.code(f"http://localhost:8501/?token={novo_token}")

        st.markdown("---")
        st.subheader("📋 Tokens existentes")
        df = carregar_tokens()
        st.dataframe(df)

        st.subheader("📂 Histórico de análises")
        if os.path.exists(HISTORICO_FILE):
            historico = pd.read_csv(HISTORICO_FILE)
            st.dataframe(historico)
        else:
            st.info("Nenhuma análise registrada ainda.")
    else:
        st.stop()

# ================== ÁREA DO CLIENTE ==================
else:
    # ✅ Correção da leitura do token
    token = st.query_params.get("token")
    if isinstance(token, list):
        token = token[0]
    elif token is None:
        token = ""

    df = carregar_tokens()
    st.write("📋 Tokens carregados:")
    st.dataframe(df)

    tokens_validos = df["token"].astype(str).str.strip().tolist()

    if token.strip() not in tokens_validos:
        st.error(f"⚠️ Token inválido: {token}")
        st.stop()

    linha = df[df["token"].astype(str).str.strip() == token.strip()]
    status = linha["status"].values[0]
    servico = linha["servico"].values[0]

    if status != "ativo":
        st.error("⚠️ Este link já foi usado.")
        st.stop()

    nome_servico, qtd_fotos = servicos.get(servico, ("Desconhecido", 0))

    st.title(f"🔍 VistoriAI – {nome_servico}")
    st.info(f"Serviço contratado: {nome_servico} – Envie exatamente {qtd_fotos} foto(s).")

    nome = st.text_input("Seu nome completo")
    telefone = st.text_input("Telefone")
    email = st.text_input("E-mail")
    marca = st.text_input("Marca")
    modelo = st.text_input("Modelo")
    ano = st.text_input("Ano")
    motorizacao = st.text_input("Motorização")
    cambio = st.selectbox("Tipo de câmbio", ["Manual", "Automático"])

    midias = st.file_uploader(
        f"Envie exatamente {qtd_fotos} foto(s):",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )

    if st.button("Enviar para análise"):
        if len(midias) != qtd_fotos:
            st.error(f"⚠️ Você enviou {len(midias)} fotos. O serviço exige {qtd_fotos}.")
            st.stop()

        with st.spinner("🧠 Analisando com IA..."):
            nomes_midias = [m.name for m in midias]

            prompt = f"""
            Você é especialista automotivo. Analise este veículo:
            Serviço: {nome_servico}
            Marca: {marca}
            Modelo: {modelo}
            Ano: {ano}
            Motorização: {motorizacao}
            Câmbio: {cambio}
            Fotos: {nomes_midias}

            Gere um relatório com:
            1. Problemas visuais detectáveis;
            2. Defeitos comuns nesse modelo;
            3. Soluções práticas;
            4. Estimativa de custo médio no Brasil.
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

            atualizar_token(token)

            salvar_historico({
                "token": token,
                "servico": nome_servico,
                "nome": nome,
                "telefone": telefone,
                "email": email,
                "marca": marca,
                "modelo": modelo,
                "ano": ano,
                "pdf_gerado": nome_pdf
            })

            st.success("✅ Análise concluída! Baixe seu relatório abaixo.")
            with open(nome_pdf, "rb") as file:
                st.download_button("📥 Baixar PDF", file, file_name=nome_pdf)
