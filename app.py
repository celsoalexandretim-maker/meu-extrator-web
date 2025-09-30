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

    # 1. Número do Contrato (com a nova regra sugerida por você)
    codigo = (re.search(r"Contrato de Licença de Uso\s*([A-Z0-9]{6})\s*Dados da Contratante", texto_completo, re.DOTALL).group(1)
              if re.search(r"Contrato de Licença de Uso\s*([A-Z0-9]{6})\s*Dados da Contratante", texto_completo, re.DOTALL) else "Não encontrado")

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

    # Abordagem estrutural para o produto
    itens_bloco = re.search(r"Itens adquiridos(.*?)Condição de Pagamento", texto_completo, re.DOTALL)
    produto = "Não encontrado"
    quantidade = "Não encontrado"
    if itens_bloco:
        bloco_itens = itens_bloco.group(1)
        
        match_produto = re.search(r"\d+\s+UN\s+[\w-]+\s+(.+)", bloco_itens)
        if match_produto:
            produto = match_produto.group(2).strip()
        
        match_qtde = re.search(r"(\d+)\s+UN", bloco_itens)
        if match_qtde:
            quantidade = match_qtde.group(1).strip()

    valor_total = (re.search(r"Valor Total\s*(R\$\s*[\d\.,]+)", texto_completo).group(1)
                   if re.search(r"Valor Total\s*(R\$\s*[\d\.,]+)", texto_completo) else "Não encontrado")

    data_formatada = "Não encontrada"
    match_data = re.search(r"\d{1,2} de [A-Za-z]+ de \d{4}", texto_completo)
    if match_data:
        data_texto = match_data.group(0)
        meses = {'janeiro': '01', 'fevereiro': '02', 'março': '03', 'abril': '04', 'maio': '05', 'junho': '06', 'julho': '07', 'agosto': '08', 'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12'}
        for nome, numero in meses.items():
            if nome in data_texto.lower():
                data_texto_numerico = data_texto.lower().replace(nome, numero).replace(' de ', '/')
                try:
                    data_obj = datetime.strptime(data_texto_numerico, '%d/%m/%Y')
                    data_formatada = data_obj.strftime('%d/%m/%Y')
                except ValueError: data_formatada = "Erro"
                break
    
    vendedor_completo = (re.search(r"Vendedor:\s*([^\n]+)", texto_completo).group(1).strip()
                         if re.search(r"Vendedor:\s*([^\n]+)", texto_completo) else "Não encontrado")
    primeiro_nome_vendedor = vendedor_completo.split(" ")[0] if vendedor_completo != "Não encontrado" else "Não encontrado"

    # Estrutura de saída final
    dados = {
        "CONTRATO": [codigo],
        "CNPJ": [cnpj],
        "Razão Social": [razao_social],
        "Forma de pagamento": [pagamento_final],
        "Produto": [produto],
        "Qtd Novos": [quantidade],
        "Valor Novos": [valor_total],
        "Data da Venda": [data_formatada],
        "Vendedor": [primeiro_nome_vendedor],
    }
    return pd.DataFrame.from_dict(dados)

# --- Interface Gráfica ---
st.set_page_config(page_title="Extrator de Dados de Contratos", layout="centered")
st.title("🚀 Extrator de Dados de Contratos")
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
                height=150
            )
