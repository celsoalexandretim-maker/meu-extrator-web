import streamlit as st
import pdfplumber
import pandas as pd
import re

def extrair_dados_do_pdf(arquivo_pdf):
    texto_completo = ""
    try:
        with pdfplumber.open(arquivo_pdf) as pdf:
            for pagina in pdf.pages:
                texto_da_pagina = pagina.extract_text(x_tolerance=1, y_tolerance=1)
                if texto_da_pagina:
                    texto_completo += texto_da_pagina + "\n"
    except Exception as e:
        st.error(f"Não foi possível ler o arquivo PDF. Pode ser um arquivo de imagem ou corrompido. Erro: {e}")
        return None

    if not texto_completo:
        st.warning("Nenhum texto extraível foi encontrado no PDF. Pode ser um documento scaneado (imagem).")
        return None

    codigo = (re.search(r"Contrato de Licença de Uso\s*([A-Z]{6})", texto_completo, re.IGNORECASE).group(1) 
              if re.search(r"Contrato de Licença de Uso\s*([A-Z]{6})", texto_completo, re.IGNORECASE) else "Não encontrado")

    razao_social = (re.search(r"Razão Social:\s*([^\n]+)", texto_completo).group(1).strip()
                    if re.search(r"Razão Social:\s*([^\n]+)", texto_completo) else "Não encontrada")

    cnpj = (re.search(r"(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})", texto_completo).group(0)
            if re.search(r"(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})", texto_completo) else "Não encontrado")

    forma_pagamento_raw = (re.search(r"Forma de Pagamento:\s*([^\n]+)", texto_completo).group(1).strip()
                           if re.search(r"Forma de Pagamento:\s*([^\n]+)", texto_completo) else "")
    
    parcelas_raw = (re.search(r"Parcelas:\s*(\d+)", texto_completo).group(1).strip()
                    if re.search(r"Parcelas:\s*(\d+)", texto_completo) else "")
    
    pagamento_final = f"{forma_pagamento_raw} {parcelas_raw}x" if forma_pagamento_raw and parcelas_raw else forma_pagamento_raw

    itens_bloco = re.search(r"Itens adquiridos(.*?)Condição de Pagamento", texto_completo, re.DOTALL)
    produto = "Não encontrado"
    quantidade = "Não encontrado"
    if itens_bloco:
        bloco = itens_bloco.group(1)
        match_produto = re.search(r"\d+\s+UN\s+.*?ZW.*?\s+([^\n]+)", bloco)
        if match_produto:
            produto = match_produto.group(1).strip()
        match_qtde = re.search(r"(\d+)\s+UN", bloco)
        if match_qtde:
            quantidade = match_qtde.group(1).strip()

    valor_total = (re.search(r"Valor Total\s*(R\$\s*[\d\.,]+)", texto_completo).group(1)
                   if re.search(r"Valor Total\s*(R\$\s*[\d\.,]+)", texto_completo) else "Não encontrado")

    data = (re.search(r"(\d{1,2} de [A-Za-z]+ de \d{4})", texto_completo).group(1)
            if re.search(r"(\d{1,2} de [A-Za-z]+ de \d{4})", texto_completo) else "Não encontrado")
    
    vendedor = (re.search(r"Vendedor:\s*([^\n]+)", texto_completo).group(1).strip()
                if re.search(r"Vendedor:\s*([^\n]+)", texto_completo) else "Não encontrado")

    dados = {
        "CONTRATO": [codigo],
        "CNPJ": [cnpj],
        "Razão Social": [razao_social],
        "Forma de pagamento": [pagamento_final],
        "Produto": [produto],
        "Qtd Novos": [quantidade],
        "Valor Novos": [valor_total],
        "Data
