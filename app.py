import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime

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

    # --- REGRAS DE EXTRAÇÃO PERSONALIZADAS E CORRIGIDAS ---

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

    # Extrai a data e converte para o formato DD/MM/AAAA
    data_formatada = "Não encontrada"
    match_data = re.search(r"\d{1,2} de [A-Za-z]+ de \d{4}", texto_completo)
    if match_data:
        data_texto = match_data.group(0)
        meses = {
            'janeiro': '01', 'fevereiro': '02', 'março': '03', 'abril': '04', 
            'maio': '05', 'junho': '06', 'julho': '07', 'agosto': '08', 
            'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12'
        }
        for nome, numero in meses.items():
            if nome in data_texto.lower():
                data_texto = data_texto.lower().replace(nome, numero)
                try:
                    data_obj = datetime.strptime(data_texto.replace(' de ', '/'), '%d/%m/%Y')
                    data_formatada = data_obj.strftime('%d/%m/%Y')
                except ValueError:
                    data_formatada = "Erro na conversão"
                break
    
    # Extrai o nome completo
