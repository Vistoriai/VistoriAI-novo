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
        return pd.DataFrame(columns=["token", "servico", "status", "nome", "telefone", "email"])
    return pd.read_csv(TOKEN_FILE)

def salvar_tokens(df):
    df.to_csv(TOKEN_FILE, index=False)

def gerar_token_aleatorio(tamanho=8):
    letras = string.ascii_uppercase + string.digits
    return ''.join(random.choices(letras, k=tamanho))

def salvar_historico(dados):
    if not os.path.exists(HISTORICO_FILE):
        historico_df = pd.DataFrame(columns=dados.keys())
    else:
        historico_df = pd.read_csv(HISTORICO_FILE)
    novo_historico = pd.DataFrame([dados])
    historico_df = pd.concat([historico_df, novo_historico], ignore_index=True)
    historico_df.to_csv(HISTORICO_FILE, index=False)

def gerar_token_automatico(servico, nome, telefone, email):
    token = gerar_token_aleatorio()
    df = carregar_tokens()
    novo_registro = pd.DataFrame([{
        "token": token,
        "servico": servico,
        "status": "ativo",
        "nome": nome,
        "telefone": telefone,
        "email": email
    }])
    df = pd.concat([df, novo_registro], ignore_index=True)
    salvar_tokens(df)

    # Também salva no histórico
    salvar_historico({
        "token": token,
        "servico": servico,
        "nome": nome,
        "telefone": telefone,
        "email": email,
        "pdf_gerado": ""
    })

    link = f"https://seusite.streamlit.app/?token={token}"
    return link

# Exemplo de uso (será chamado após pagamento confirmado)
# novo_link = gerar_token_automatico('motor', 'João Silva', '+5511999999999', 'joao@email.com')
# print(novo_link)
