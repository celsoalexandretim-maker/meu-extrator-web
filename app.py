import streamlit as st
import pdfplumber
import pandas as pd
import re

def extrair_dados_do_pdf(arquivo_pdf):
    texto_completo = ""
    try:
        with pdfplumber.open(arquivo_pdf) as pdf:
            for pagina in pdf.pages:
                texto_da_pagina = pagina.extract_text()
                if texto_da_pagina:
                    texto_completo += texto_da_pagina + "\n"
    except Exception as e:
        st.error(f"Não foi possível ler o arquivo PDF. Pode ser um arquivo de imagem ou corrompido. Erro: {e}")
        return None

    if not texto_completo:
        st.warning("Nenhum texto extraível foi encontrado no PDF. Pode ser um documento scaneado (imagem).")
        return None

    # Adapte os padrões de regex abaixo para o seu contrato específico
    cnpj_pattern = re.search(r"(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})", texto_completo)
    cnpj = cnpj_pattern.group(0) if cnpj_pattern else "Não encontrado"

    razao_social_pattern = re.search(r"Razão Social:\s*(.*)", texto_completo)
    razao_social = razao_social_pattern.group(1).strip() if razao_social_pattern else "Não encontrada"

    valor_pattern = re.search(r"Valor Total R\$\s*([\d\.,]+)", texto_completo)
    valor = valor_pattern.group(1).strip() if valor_pattern else "Não encontrado"

    vendedor_pattern = re.search(r"Vendedor:\s*(.*)", texto_completo)
    vendedor = vendedor_pattern.group(1).strip() if vendedor_pattern else "Não encontrado"

    dados = {
        "CNPJ": [cnpj],
        "Razão Social": [razao_social],
        "Valor": [valor],
        "Vendedor": [vendedor],
    }
    return pd.DataFrame.from_dict(dados)

st.set_page_config(page_title="Extrator de Dados de PDF", layout="centered")
st.title("🚀 Ferramenta de Extração de Dados de PDF")

uploaded_file = st.file_uploader("1. Faça o upload do seu arquivo PDF de contrato", type="pdf")

if uploaded_file is not None:
    with st.spinner('Analisando o PDF...'):
        df_dados = extrair_dados_do_pdf(uploaded_file)

        if df_dados is not None:
            st.success("2. Dados extraídos com sucesso!")
            st.dataframe(df_dados)

            texto_para_copiar = df_dados.to_csv(sep='\t', index=False, header=False)

            st.subheader("3. Copie abaixo e cole na sua planilha")
            st.text_area(
                "Texto formatado para cópia (Ctrl+A para selecionar tudo):", 
                texto_para_copiar, 
                height=100
            )
