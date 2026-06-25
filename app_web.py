import streamlit as st
import pdfplumber
import re
import urllib.parse

# Configuração da página Web
st.set_page_config(page_title="Gerador de Notificação de Envio", page_icon="🚚", layout="centered")

st.title("🚚 Gerador de Notificação de Envio")
st.markdown("Faça o upload do PDF da Nota Fiscal para preencher os dados automaticamente.")

# Inicializa as variáveis no session_state para manter a reatividade correta
if "txt_cliente" not in st.session_state: st.session_state.txt_cliente = ""
if "txt_pedido" not in st.session_state: st.session_state.txt_pedido = ""
if "txt_data_envio" not in st.session_state: st.session_state.txt_data_envio = ""
if "txt_transportadora" not in st.session_state: st.session_state.txt_transportadora = ""
if "txt_nfe" not in st.session_state: st.session_state.txt_nfe = ""
if "txt_volumes" not in st.session_state: st.session_state.txt_volumes = ""
if "txt_qtd_total" not in st.session_state: st.session_state.txt_qtd_total = ""
if "txt_obs" not in st.session_state: st.session_state.txt_obs = ""
if "arquivo_processado" not in st.session_state: st.session_state.arquivo_processado = ""

# 1. ENTRADA DO WHATSAPP
telefone = st.text_input("📱 Telefone do Cliente (com DDD):", value="55")

# 2. UPLOAD DO ARQUIVO PDF
arquivo_pdf = st.file_uploader("📂 Arraste ou selecione o PDF da NF-e", type=["pdf"])

# Lógica de processamento reativo ao mudar o arquivo
if arquivo_pdf is not None:
    if st.session_state.arquivo_processado != arquivo_pdf.name:
        try:
            with pdfplumber.open(arquivo_pdf) as pdf:
                # TRAVA DE SEGURANÇA: Considera estritamente apenas a primeira folha
                texto = pdf.pages[0].extract_text() if pdf.pages else ""
                texto_upper = texto.upper()
                
                # Divide o texto em linhas limpas para análises estruturadas
                linhas = [l.strip() for l in texto.split('\n') if l.strip()]
                linhas_upper = [l.upper() for l in linhas]
                
                # --- 1. CAPTURA DO CLIENTE (MÚLTIPLAS CAMADAS DE SEGURANÇA) ---
                cliente_detectado = ""
                
                # Camada 1: Procura pelo cabeçalho do bloco de cadastro do Destinatário
                for idx, linha in enumerate(linhas_upper):
                    if "NOME" in linha and ("RAZAD" in linha or "RAZÃO" in linha or "RAZAO" in linha):
                        if idx + 1 < len(linhas):
                            cliente_detectado = linhas[idx + 1].strip()
                        break
                
                # Camada 2: Fallback por Regex caso a estrutura de linhas mude
                if not cliente_detectado:
                    match_cli = re.search(r'DESTINAT[AÁ]RIO\s+(.+?)\s+(?:RUA|AVENIDA|ALAMEDA|RODOVIA|ENDERE[CÇ]O)', texto_upper)
                    if match_cli:
                        cliente_detectado = match_cli.group(1).strip()
                
                # Camada 3: Validação e Formatação de Clientes Frequentes Conhecidos
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
                if "RODONAVES" in texto_upper:
                    st.session_state.txt_transportadora = "RODONAVES TRANSPORTES E ENCOMENDAS LTDA"
                elif "GOL" in texto_upper:
                    st.session_state.txt_transportadora = "GOL LINHAS AEREAS SA"
                else:
                    st.session_state.txt_transportadora = "A DEFINIR / RETIRA"
                
                # --- 5. CAPTURA DO NÚMERO DA NF-E ---
                match_nfe = re.search(r'N[°°ºª\s]*(\d+)\s*\n\s*S[EÉ]RIE', texto_upper)
                if match_nfe:
                    st.session_state.txt_nfe = match_nfe.group(1).strip()
                else:
                    nfe_nums = re.findall(r'N[°°ºª\s]+(\d+)', texto_upper)
                    st.session_state.txt_nfe = nfe_nums[0] if nfe_nums else ""
                
                # --- 6. CAPTURA DOS VOLUMES ---
                match_vol = re.search(r'(\d+)\s*\n?\s*CAIXAS', texto_upper)
                if match_vol:
                    st.session_state.txt_volumes = f"{match_vol.group(1).strip()} CAIXAS"
                else:
                    match_vol_alt = re.search(r'QUANTIDADE\s*\n\s*(\d+)', texto_upper)
                    st.session_state.txt_volumes = f"{match_vol_alt.group(1).strip()} CAIXAS" if match_vol_alt else "1 CAIXA"
                
                # --- 7. QUANTIDADE TOTAL DE ITENS ---
                match_qtd = re.search(r'QUANTIDADE\s*TOTAL\s*\n\s*([\d.,]+)', texto_upper)
                if match_qtd:
                    qtd_texto = match_qtd.group(1).strip()
                    if qtd_texto.endswith('.00') or qtd_texto.endswith(',00'): qtd_texto = qtd_texto[:-3]
                    st.session_state.txt_qtd_total = qtd_texto
                else:
                    qtd_nums = re.findall(r'QUANTIDADE\s*TOTAL\s*\n?\s*([\d.,]+)', texto_upper)
                    if qtd_nums:
                        qtd_texto = qtd_nums[0].strip()
                        if qtd_texto.endswith('.00') or qtd_texto.endswith(',00'): qtd_texto = qtd_texto[:-3]
                        st.session_state.txt_qtd_total = qtd_texto
                    else:
                        st.session_state.txt_qtd_total = ""
                    
                # --- 8. CAPTURA TEXTUAL DIRETA DO BLOCO DE INFORMAÇÕES COMPLEMENTARES ---
                match_obs = re.search(r'INFORMA[CÇ][OÕ]ES\s+COMPLEMENTARES\s*([\s\S]+?)(?=QUANTIDADE\s+TOTAL|RESERVADO|$)', texto_upper)
                if match_obs:
                    conteudo_obs = match_obs.group(1).strip()
                    
                    # Limpezas de propagandas ou dados técnicos de rodapé dos emissores
                    conteudo_obs = re.sub(r'VERS[AÃ]O\s+DO\s+SISTEMA.*', '', conteudo_obs, flags=re.IGNORECASE)
                    conteudo_obs = re.sub(r'VEJA\s+NOSSAS\s+SOLU[CÇ][OÕ]ES.*', '', conteudo_obs, flags=re.IGNORECASE)
                    
                    texto_limpo = conteudo_obs.replace('\n', ' ').strip()
                    st.session_state.txt_obs = re.sub(r'\s+', ' ', texto_limpo).strip()
                else:
                    st.session_state.txt_obs = ""
                
                # Grava o nome do arquivo atual para evitar reprocessamento infinito
                st.session_state.arquivo_processado = arquivo_pdf.name
                st.rerun()
        except Exception as e:
            st.error(f"Erro ao processar o PDF: {e}")
else:
    # Se o arquivo for removido da tela, limpa todos os campos
    if st.session_state.arquivo_processado != "":
        st.session_state.txt_cliente = ""
        st.session_state.txt_pedido = ""
        st.session_state.txt_data_envio = ""
        st.session_state.txt_transportadora = ""
        st.session_state.txt_nfe = ""
        st.session_state.txt_volumes = ""
        st.session_state.txt_qtd_total = ""
        st.session_state.txt_obs = ""
        st.session_state.arquivo_processado = ""
        st.rerun()

# --- CAMPOS EDITÁVEIS NA TELA ---
st.markdown("### 📋 Conferência dos Dados")

ent_cliente = st.text_input("👤 Cliente (Nome Razão Social):", key="txt_cliente")
ent_pedido = st.text_input("📦 Pedido:", key="txt_pedido")
ent_data_envio = st.text_input("📅 Data de Envio (Emissão da NF):", key="txt_data_envio")
ent_transportadora = st.text_input("🚛 Transportadora:", key="txt_transportadora")

# Campos Manuais
ent_rastreio = st.text_input("🔎 Rastreamento (Manual):", value="")
ent_previsao = st.text_input("📍 Previsão de Entrega (Manual):", value="")

ent_nfe = st.text_input("🧾 NF-e Nº:", key="txt_nfe")
ent_volumes = st.text_input("📦 Volumes Caixas:", key="txt_volumes")
ent_qtd_total = st.text_input("📊 Quantidade Total de Itens:", key="txt_qtd_total")
ent_obs = st.text_input("⚠️ Observações (Dados Adicionais):", key="txt_obs")

# --- LÓGICA DE DETECÇÃO DO LINK DE RASTREIO ---
nome_transp = ent_transportadora.upper()
link_rastreamento = "https://www.google.com"

if "RODONAVES" in nome_transp:
    link_rastreamento = "https://cliente.rodonaves.com.br/rastreamento"
elif "GOL" in nome_transp:
    link_rastreamento = "https://www.voegol.com.br/servicos-gollog"
elif "TAM" in nome_transp or "LATAM" in nome_transp:
    link_rastreamento = "https://www.tamcargo.com.br"
elif "AZUL" in nome_transp:
    link_rastreamento = "https://www.azulcargoexpress.com.br"
elif "CORREIOS" in nome_transp:
    link_rastreamento = "https://rastreamento.correios.com.br"
elif "JADLOG" in nome_transp:
    link_rastreamento = "https://www.jadlog.com.br/tracking"
elif "TOTAL" in nome_transp:
    link_rastreamento = "https://www.totalexpress.com.br"

# --- MONTAGEM DA MENSAGEM ---
mensagem = (
    f"*🚚 PEDIDO ENVIADO*\n\n"
    f"👤 *DESTINATÁRIO / REMETENTE Cliente:* {ent_cliente}\n"
    f"📦 *Pedido:* {ent_pedido}\n"
    f"📅 *Data de envio:* {ent_data_envio}\n"
    f"🚛 *TRANSPORTADOR:* {ent_transportadora}\n"
    f"📦 *Tipo de envio:* Frete por Conta do Emitente\n"
    f"🧾 *NF-e Nº :* {ent_nfe}\n"
    f"🔎 *Rastreamento:* {ent_rastreio.strip() or 'A definir pela transportadora'}\n"
    f"🌐 *Link rastreamento:* {link_rastreamento}\n"
    f"📍 *Previsão de entrega:* {ent_previsao.strip() or 'Não especificada'}\n"
    f"📦 *Volumes Caixas:* {ent_volumes}\n"
    f"📊 *Quantidade Total de Itens:* {ent_qtd_total}\n"
    f"⚠️ *Observações:* {ent_obs}"
)

st.markdown("---")
st.markdown("### 📲 Enviar para o WhatsApp")

num_telefone = telefone.strip().replace("-", "").replace(" ", "")
if len(num_telefone) == 11:
    num_telefone = "55" + num_telefone

texto_codificado = urllib.parse.quote(mensagem)
link_whatsapp = f"https://api.whatsapp.com/send?phone={num_telefone}&text={texto_codificado}"

# Botão do WhatsApp estilo Web App
st.markdown(f'<a href="{link_whatsapp}" target="_blank"><button style="width:100%; background-color:#25d366; color:white; border:none; padding:12px; font-weight:bold; font-size:16px; border-radius:5px; cursor:pointer;">📲 Abrir no WhatsApp</button></a>', unsafe_allow_html=True)

st.markdown("#### Texto que será enviado (Cópia de segurança):")
st.code(mensagem, language="text")
