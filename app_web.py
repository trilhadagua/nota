import streamlit as st
import pdfplumber
import re
import urllib.parse

# Configuração da página Web
st.set_page_config(page_title="Gerador - Disparo Automático", page_icon="⚡", layout="centered")

st.title("⚡ Central de Envios Automáticos")
st.markdown("Confira os dados extraídos do PDF, preencha os campos manuais e dispare diretamente para o setor.")

# Inicializa as variáveis no session_state para manter a reatividade correta
if "txt_cliente" not in st.session_state: st.session_state.txt_cliente = ""
if "txt_pedido" not in st.session_state: st.session_state.txt_pedido = ""
if "txt_data_envio" not in st.session_state: st.session_state.txt_data_envio = ""
if "txt_transportadora" not in st.session_state: st.session_state.txt_transportadora = ""
if "txt_link_rastreio" not in st.session_state: st.session_state.txt_link_rastreio = "https://www.google.com"
if "txt_nfe" not in st.session_state: st.session_state.txt_nfe = ""
if "txt_volumes" not in st.session_state: st.session_state.txt_volumes = ""
if "txt_qtd_total" not in st.session_state: st.session_state.txt_qtd_total = ""
if "txt_obs" not in st.session_state: st.session_state.txt_obs = ""
if "arquivo_processado" not in st.session_state: st.session_state.arquivo_processado = ""

# --- CONFIGURAÇÃO DE SETORES ---
st.markdown("### 🏢 Destinatário da Notificação")
destino_grupo = st.selectbox(
    "Selecione o setor interno/grupo que vai receber o alerta:",
    ["Expedição / Armazém 📦", "Logística / Transportadoras 🚛", "Comercial / Vendas 💰", "Faturamento / Fiscal 🧾"]
)

st.markdown("---")

# 2. UPLOAD DO ARQUIVO PDF
arquivo_pdf = st.file_uploader("📂 Arraste ou selecione o PDF da NF-e", type=["pdf"])

# Lógica de processamento reativo ao mudar o arquivo
if arquivo_pdf is not None:
    if st.session_state.arquivo_processado != arquivo_pdf.name:
        try:
            with pdfplumber.open(arquivo_pdf) as pdf:
                texto = pdf.pages[0].extract_text() if pdf.pages else ""
                texto_upper = texto.upper()
                
                # Criamos uma lista limpa de linhas em maiúsculo
                linhas = [l.strip().upper() for l in texto.split('\n') if l.strip()]
                
                # --- 1. CAPTURA DO CLIENTE ---
                cliente_detectado = ""
                for idx, linha in enumerate(linhas):
                    if "NOME" in linha and ("RAZAD" in linha or "RAZÃO" in linha or "RAZAO" in linha):
                        if idx + 1 < len(linhas):
                            cliente_detectado = linhas[idx + 1].strip()
                        break
                
                if "HOTEL BOURBON" in texto_upper:
                    st.session_state.txt_cliente = "HOTEL BOURBON DE FOZ DO IGUACU LTDA"
                elif "LEVE CURITIBA" in texto_upper:
                    st.session_state.txt_cliente = "LEVE CURITIBA COM VOCE LTDA"
                elif "NORONHA.COM" in texto_upper:
                    st.session_state.txt_cliente = "NORONHA.COM COMERCIO DE SOUVENIRS LTDA"
                elif cliente_detectado:
                    st.session_state.txt_cliente = cliente_detectado
                else:
                    st.session_state.txt_cliente = "Não identificado"
                
                # --- 2. CAPTURA DO PEDIDO ---
                match_ped = re.search(r'PED:\s*(\d+)', texto_upper)
                if match_ped:
                    st.session_state.txt_pedido = match_ped.group(1).strip()
                else:
                    match_ped_alt = re.search(r'PEDID[OO]:?\s*(\d+)', texto_upper)
                    st.session_state.txt_pedido = match_ped_alt.group(1).strip() if match_ped_alt else ""
                
                # --- 3. CAPTURA DA DATA DE EMISSÃO ---
                match_data = re.search(r'DATA\s*EMISS[AÃ]O\s*\n?\s*([\d/]+)', texto_upper)
                if match_data:
                    st.session_state.txt_data_envio = match_data.group(1).strip()
                else:
                    datas = re.findall(r'\b\d{2}/\d{2}/\d{4}\b', texto_upper)
                    st.session_state.txt_data_envio = datas[0] if datas else ""
                    
                # --- 4. CAPTURA DA TRANSPORTADORA ---
                transp_detectada = ""
                for idx, linha in enumerate(linhas):
                    if ("RAZÃO" in linha or "RAZAD" in linha or "RAZAO" in linha or "NGME" in linha) and idx > 15:
                        if "TRANSPORTADOR" in linhas[idx-1] or "TRANSPORTADOR" in linhas[idx-2] or idx > 35:
                            if idx + 1 < len(linhas):
                                transp_detectada = linhas[idx + 1].strip()
                            break
                
                transp_upper = transp_detectada.upper()
                if "RODONAVES" in transp_upper:
                    st.session_state.txt_transportadora = "RODONAVES TRANSPORTES E ENCOMENDAS LTDA"
                elif "GOL" in transp_upper or "GOLLOG" in transp_upper:
                    st.session_state.txt_transportadora = "GOL LINHAS AEREAS SA (GOLLOG)"
                elif "BRASPRESS" in transp_upper:
                    st.session_state.txt_transportadora = "BRASPRESS TRANSPORTES URGENTES LTDA"
                elif "AZUL" in transp_upper:
                    st.session_state.txt_transportadora = "AZUL CARGO EXPRESS"
                elif "LATAM" in transp_upper:
                    st.session_state.txt_transportadora = "LATAM CARGO BRASIL"
                elif "MIGUEL" in transp_upper:
                    st.session_state.txt_transportadora = "EXPRESSO SÃO MIGUEL"
                elif "O MESMO" in transp_upper or transp_detectada == "":
                    st.session_state.txt_transportadora = "A DEFINIR / RETIRA (O MESMO)"
                else:
                    st.session_state.txt_transportadora = transp_detectada
                
                # --- MAPEAMENTO SEGURO DO LINK BASEADO APENAS NO CAMPO DA TRANSPORTADORA ---
                nome_transp_check = st.session_state.txt_transportadora.upper()
                if "RODONAVES" in nome_transp_check:
                    st.session_state.txt_link_rastreio = "https://www.rodonaves.com.br/rastreio-de-mercadoria"
                elif "GOL" in nome_transp_check:
                    st.session_state.txt_link_rastreio = "https://servicos.gollog.com.br/app/site/tracking"
                elif "BRASPRESS" in nome_transp_check:
                    st.session_state.txt_link_rastreio = "https://www.braspress.com/rastreie-sua-encomenda/"
                elif "AZUL" in nome_transp_check:
                    st.session_state.txt_link_rastreio = "https://www.azulcargo.com.br/"
                elif "LATAM" in nome_transp_check:
                    st.session_state.txt_link_rastreio = "https://www.latamcargo.com/pt/trackshipment"
                elif "MIGUEL" in nome_transp_check:
                    st.session_state.txt_link_rastreio = "https://portaldocliente.expressosaomiguel.com.br/rastrear-mercadoria"
                elif "A DEFINIR" in nome_transp_check:
                    st.session_state.txt_link_rastreio = "https://trilhadagua.com.br/"
                elif "MB" in nome_transp_check:
                    st.session_state.txt_link_rastreio = "https://trilhadagua.com.br/"
                else:
                    termo_busca = urllib.parse.quote(f"rastreamento {st.session_state.txt_transportadora}")
                    st.session_state.txt_link_rastreio = f"https://www.google.com/search?q={termo_busca}"
                
                # --- 5. CAPTURA DO NÚMERO DA NF-E ---
                match_nfe = re.search(r'N[°°ºª\s]*(\d+)\s*\n\s*S[EÉ]RIE', texto_upper)
                if match_nfe:
                    st.session_state.txt_nfe = match_nfe.group(1).strip()
                else:
                    nfe_nums = re.findall(r'N[°°ºª\s]+(\d+)', texto_upper)
                    st.session_state.txt_nfe = nfe_nums[0] if nfe_nums else ""
                
                # --- 6. CAPTURA DOS VOLUMES CAIXAS ---
                volumes_val = ""
                idx_transp = -1
                for i, linha in enumerate(linhas):
                    if "TRANSPORTADOR" in linha:
                        idx_transp = i
                        break
                
                if idx_transp != -1:
                    for j in range(idx_transp + 1, min(idx_transp + 16, len(linhas))):
                        if "QUANTIDADE" in linhas[j]:
                            bloco_busca = " ".join(linhas[j:j+4])
                            match_num = re.search(r'QUANTIDADE.*?([\d.,]+)', bloco_busca)
                            if match_num:
                                volumes_val = match_num.group(1).strip()
                                break
                
                if not volumes_val:
                    match_vol_alt = re.search(r'QUANTIDADE\s+([\d.,]+)', texto_upper)
                    if match_vol_alt:
                        volumes_val = match_vol_alt.group(1).strip()

                if volumes_val:
                    if volumes_val.endswith('.00') or volumes_val.endswith(',00'): 
                        volumes_val = volumes_val[:-3]
                    st.session_state.txt_volumes = f"{volumes_val} CAIXAS"
                else:
                    st.session_state.txt_volumes = ""
                
                # --- 7. CAPTURA DA QUANTIDADE TOTAL DA NOTA ---
                qtd_total_val = ""
                match_qtd_flex = re.search(r'QUANTIDADE\s*TOTAL\s*[:\-\s\n]*([\d.,]+)', texto_upper)
                if match_qtd_flex:
                    qtd_total_val = match_qtd_flex.group(1).strip()
                else:
                    for idx, linha in enumerate(linhas):
                        if "QUANTIDADE TOTAL" in linha or "QTD TOTAL" in linha:
                            if idx + 1 < len(linhas):
                                proxima_linha = linhas[idx + 1].strip()
                                if re.match(r'^[\d.,]+$', proxima_linha):
                                    qtd_total_val = proxima_linha
                                    break

                if qtd_total_val:
                    if qtd_total_val.endswith('.00') or qtd_total_val.endswith(',00'): 
                        qtd_total_val = qtd_total_val[:-3]
                    st.session_state.txt_qtd_total = qtd_total_val
                else:
                    st.session_state.txt_qtd_total = ""
                    
                # --- 8. CAPTURA DAS OBSERVAÇÕES (DADOS ADICIONAIS) ---
                match_obs = re.search(r'INFORMA[CÇ][OÕ]ES\s+COMPLEMENTARES\s*([\s\S]+?)(?=DADOS\s+DO\s+PRODUTO|RESERVADO|$)', texto_upper)
                if match_obs:
                    st.session_state.txt_obs = re.sub(r'\s+', ' ', match_obs.group(1).replace('\n', ' ')).strip()
                else:
                    st.session_state.txt_obs = ""
                
                st.session_state.arquivo_processado = arquivo_pdf.name
                st.rerun()
        except Exception as e:
            st.error(f"Erro ao processar o PDF: {e}")

# --- CAMPOS TOTALMENTE EDITÁVEIS NA TELA ---
st.markdown("### 📋 Conferência e Edição dos Dados")

ent_cliente = st.text_input("👤 Cliente (Nome Razão Social):", key="txt_cliente")
ent_pedido = st.text_input("📦 Pedido:", key="txt_pedido")
ent_data_envio = st.text_input("📅 Data de Envio (Emissão da NF):", key="txt_data_envio")
ent_transportadora = st.text_input("🚛 Transportadora:", key="txt_transportadora")

# Campos Manuais Liberados
ent_rastreio = st.text_input("🔎 Rastreamento (Manual):", value="")
ent_previsao = st.text_input("📍 Previsão de Entrega (Manual):", value="")
ent_link_rastreio = st.text_input("🌐 Link de Rastreamento (Dinâmico):", key="txt_link_rastreio")

ent_nfe = st.text_input("🧾 NF-e Nº:", key="txt_nfe")
ent_volumes = st.text_input("📦 Volumes Caixas:", key="txt_volumes")
ent_qtd_total = st.text_input("📊 Quantidade Total de Itens:", key="txt_qtd_total")
ent_obs = st.text_input("⚠️ Observações (Dados Adicionais):", key="txt_obs")

# --- MONTAGEM DA MENSAGEM FINAL ---
mensagem = (
    f"*⚡ NOTIFICAÇÃO AUTOMÁTICA DE ENVIO*\n\n"
    f"👤 *Cliente:* {ent_cliente}\n"
    f"📦 *Pedido:* {ent_pedido}\n"
    f"📅 *Data de Envio:* {ent_data_envio}\n"
    f"🚛 *Transportador:* {ent_transportadora}\n"
    f"🧾 *NF-e Nº:* {ent_nfe}\n"
    f"🔎 *Rastreamento:* {ent_rastreio.strip() or 'A definir'}\n"
    f"🌐 *Link Rastreio:* {ent_link_rastreio}\n"
    f"📍 *Previsão de Entrega:* {ent_previsao.strip() or 'Não informada'}\n"
    f"📦 *Volumes:* {ent_volumes}\n"
    f"📊 *Quantidade Total:* {ent_qtd_total}\n"
    f"⚠️ *Observações:* {ent_obs}"
)

st.markdown("---")
st.markdown("### 🚀 Ação de Disparo")

# Entrada opcional do telefone
telefone_destino = st.text_input("📱 Número do celular destino (Opcional - Ex: 5545999999999):", value="")

# Formata o link URL amigável para o WhatsApp
mensagem_codificada = urllib.parse.quote(mensagem)
if telefone_destino.strip():
    tel_limpo = re.sub(r'\D', '', telefone_destino)
    link_whatsapp = f"https://api.whatsapp.com/send?phone={tel_limpo}&text={mensagem_codificada}"
else:
    link_whatsapp = f"https://api.whatsapp.com/send?text={mensagem_codificada}"

# Botão Verde Estilizado
st.link_button("🟢 Enviar via WhatsApp Web/App", link_whatsapp, type="primary", use_container_width=True)

st.markdown("#### Pré-visualização do texto da notificação:")
st.code(mensagem, language="text")
