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
                # Usar layout=True pode ajudar a preservar a estrutura da tabela
                texto_da_pagina = pagina.extract_text(x_tolerance=1, y_tolerance=1, layout=True)
                if texto_da_pagina:
                    texto_completo += texto_da_pagina + "\n"
    except Exception as e:
        st.error(f"Não foi possível ler o arquivo PDF. Pode ser um arquivo de imagem ou corrompido. Erro: {e}")
        return None

    if not texto_completo:
        st.warning("Nenhum texto extraível foi encontrado no PDF. Pode ser um documento scaneado (imagem).")
        return None

    # --- REGRAS DE EXTRAÇÃO ---

    codigo = (re.search(r"Contrato de Licença de Uso.*?([A-Z0-9]{6})", texto_completo, re.DOTALL).group(1)
              if re.search(r"Contrato de Licença de Uso.*?([A-Z0-9]{6})", texto_completo, re.DOTALL) else "Não encontrado")

    razao_social = (re.search(r"Razão Social:\s*(.*?)Licenciante:", texto_completo, re.DOTALL).group(1).strip().replace("\n", " ")
                    if re.search(r"Razão Social:\s*(.*?)Licenciante:", texto_completo, re.DOTALL) else "Não encontrada")
    
    cnpj = (re.search(r"CNPJ/CPF:\s*.*?(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})", texto_completo, re.DOTALL).group(1)
            if re.search(r"CNPJ/CPF:\s*.*?(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})", texto_completo, re.DOTALL) else "Não encontrado")
    
    forma_pagamento_raw = (re.search(r"Forma de Pagamento:\s*([^\n]+)", texto_completo).group(1).strip()
                           if re.search(r"Forma de Pagamento:\s*([^\n]+)", texto_completo) else "")
    parcelas_raw = (re.search(r"Parcelas:\s*(\d+)", texto_completo).group(1).strip()
                    if re.search(r"Parcelas:\s*(\d+)", texto_completo) else "")
    forma_final = forma_pagamento_raw
    if "cartao" in forma_pagamento_raw.lower():
        forma_final = "Cartão"
    elif "boleto" in forma_pagamento_raw.lower():
        forma_final = "Boleto"
    if parcelas_raw:
        pagamento_final = f"{forma_final} {parcelas_raw}x"
    else:
        pagamento_final = forma_final

    # --- CORREÇÃO FINAL NO PRODUTO - ABORDAGEM ESTRUTURAL ---
    itens_bloco = re.search(r"Itens adquiridos(.*?)Condição de Pagamento", texto_completo, re.DOTALL)
    produto = "Não encontrado"
    quantidade = "Não encontrado"
    if itens
