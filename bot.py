# Copyright (c) 2025 Murilo De Souza
# Licenciado sob os termos da licença MIT.
from telethon import TelegramClient, events
import re
import os
import requests
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pyperclip
from sentence_transformers import SentenceTransformer, util
import json
from dotenv import load_dotenv

load_dotenv()

# Configurações e envs
# Vale ressaltar que voce deve estar logado em todos os links usados no script
api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
session_name = os.environ.get("SESSION_NAME")
canal_origem = os.environ.get("CANAL_ORIGEM")
canal_destino = os.environ.get("CANAL_DESTINO")
chrome_user_data = os.environ.get("CHROME_USER_DATA") # Caminho do user data do seu usuario do windows
link_shopee = os.environ.get("LINK_SHOPEE") # https://affiliate.shopee.com.br/offer/custom_link
link_magazine = os.environ.get("LINK_MAGAZINE") # https://www.magazinevoce.com.br/magazineSEUUSUARIO/ (nome de usuario influenciador magalu)
link_kabum = os.environ.get("LINK_KABUM") # https://ui.awin.com/link-builder/br/awin/publisher/SEU_ID
link_encurtador = os.environ.get("LINK_ENCURTADOR") # https://app.short.io/users/dashboard/SEU_ID/links
link_mercadolivre = os.environ.get("LINK_MERCADOLIVRE") #https://www.mercadolivre.com.br/afiliados/linkbuilder
# Defina as variáveis em um arquivo .env, infos do bot e dos canais, links afiliados ()

client = TelegramClient("sessao_bot", api_id, api_hash)
modelo = SentenceTransformer('paraphrase-MiniLM-L6-v2')  

def extrair_nome_com_ia(mensagem):
    linhas = mensagem.splitlines()
    linhas_validas = []
    palavras_chave = ["preço", "cupom", "http", "oferta", "acesse", "promo", canal_origem, "r$", "www"]

    for linha in linhas:
        linha_limpa = linha.strip()
        if not linha_limpa:
            continue
        if any(p in linha_limpa.lower() for p in palavras_chave):
            continue
        if len(linha_limpa) < 10: 
            continue
        linhas_validas.append(linha_limpa)

    if not linhas_validas:
        return "Produto não identificado"  

    referencia = "Nome de um produto em uma loja"
    embeddings = modelo.encode([referencia] + linhas_validas)  
    similaridades = util.cos_sim(embeddings[0], embeddings[1:])[0]  
    indice_mais_provavel = similaridades.argmax() 
    return linhas_validas[indice_mais_provavel]


def extrair_link(mensagem):
    match = re.search(r'https?://\S+', mensagem)
    return match.group(0) if match else None

def expandir_link(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        return response.url
    except Exception as e:
        print(f"Erro ao expandir link: {e}")
        return url 

def identificar_loja(url):
    dominio = urlparse(url).netloc.lower()

    if "mercadolivre.com" in dominio:
        return "Mercado Livre"
    elif "kabum.com" in dominio:
        return "Kabum"
    elif "amazon.com" in dominio or "amzn.to" in dominio:
        return "Amazon"
    elif "shopee.com" in dominio:
        return "Shopee"
    elif "aliexpress.com" in dominio:
        return "AliExpress"
    elif "magazineluiza.com" in dominio or "magalu" in dominio:
        return "Magazine Luiza"
    else:
        return "Não afiliado"

def iniciar_driver_com_perfil():
    chromedriver_autoinstaller.install()
    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir={chrome_user_data}")
    chrome_options.add_argument(r'--profile-directory=Default')
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--no-first-run")
    #(executar sem interface gráfica(em testes ainda))chrome_options.add_argument("--headless")
    #(existem alguns bugs no modo headless envolvendo gpu)chrome_options.add_argument("--disable-gpu")
    #(tamanho padrao da janela (se necessario))chrome_options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=chrome_options)

def gerar_link_afiliado_shopee(link_original):
    driver = iniciar_driver_com_perfil()

    try:
        driver.get(link_shopee)

        textarea = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "textarea"))
        )
        link = link_original
        textarea.send_keys(link)
        time.sleep(1)

        generate_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(text(), 'Obter link')]]"))
        )

        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", generate_button)
        time.sleep(1.5)  

        generate_button.click()

        copy_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(text(), 'Copiar')]]"))
        )

        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", copy_button)
        time.sleep(1.5)

        driver.execute_script("arguments[0].click();", copy_button)
        time.sleep(1)

        affiliate_link = pyperclip.paste()

        return affiliate_link
    except Exception as e:
        print(f"❌ Erro ao gerar link afiliado Shopee: {e}")
        return link_original
    finally:
        driver.quit()

def gerar_link_afiliado_magazine(nome_produto):
    driver = iniciar_driver_com_perfil()

    try:
        driver.get(link_magazine)

        time.sleep(3)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "input-search")))

        search_input = driver.find_element(By.ID, "input-search")
        search_input.send_keys(nome_produto)

        search_button = driver.find_element(By.CSS_SELECTOR, "svg[data-testid='search-submit']")
        search_button.click()
        time.sleep(5)

        product_title = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, f"//h2[contains(text(), '{nome_produto}')]"))
        )
        product_title.click()
        time.sleep(2)

        for _ in range(2):  
            driver.execute_script("window.scrollBy(0, 420);")  
            time.sleep(1)

        checkbox = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//input[@data-testid='checkbox-item']"))
        )

        checkbox.click()
        time.sleep(3)

        copy_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='copy-to-clipboard-button']"))
        )
        copy_button.click()
        time.sleep(1)

        affiliate_link = pyperclip.paste()
        
        return affiliate_link
    except Exception as e:
        print(f"❌ Erro ao gerar link afiliado Magazine: {e}")
        return link_original
    finally:
        driver.quit()

def gerar_link_afiliado_kabum(link_original):
    driver = iniciar_driver_com_perfil()

    try:
        driver.get(link_kabum)

        time.sleep(10)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "advertiserInput")))

        advertiser_input = driver.find_element(By.ID, "advertiserInput")
        advertiser_input.click()

        time.sleep(1) 
        advertiser_selection = driver.find_element(By.XPATH, "//span[contains(text(), '3DOffice - Minimalistic Home Decor AT')]")
        advertiser_selection.click()
        time.sleep(1)

        destination_input = driver.find_element(By.NAME, "destinationUrl")
        destination_input.send_keys(link_original)
        time.sleep(1)

        manage_link_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Gerenciar link')]"))
        )
        manage_link_button.click()
        time.sleep(2)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        shorten_link_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Encurtar Link')]"))
        )
        shorten_link_button.click()
        time.sleep(2)

        copy_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Copiar Link')]"))
        )
        copy_button.click()
        time.sleep(1)

        affiliate_link = pyperclip.paste()

        return affiliate_link
    except Exception as e:
        print(f"❌ Erro ao gerar link afiliado Kabum: {e}")
        return link_original
    finally:
        driver.quit()

def gerar_link_afiliado_encurtador(link_original):
    driver = iniciar_driver_com_perfil()

    try:
        driver.get(link_encurtador)

        time.sleep(1)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "create-link-input")))

        textarea = driver.find_element(By.ID, "create-link-input")

        link = link_original

        for char in link:
            textarea.send_keys(char)
            time.sleep(0.01)  
        time.sleep(1)

        create_link_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.XPATH, "//button[@data-kind='create-link-button']"))
        )

        action = ActionChains(driver)
        action.move_to_element(create_link_button).click().perform()
        time.sleep(3)

        save_button = driver.find_element(By.XPATH, "//button[@data-kind='save-link-edit']")
        save_button.click()
        time.sleep(2)

        close_button = driver.find_element(By.XPATH, "//button[@data-kind='close-link-edit']")
        close_button.click()
        time.sleep(2)

        shortened_link = driver.find_element(By.XPATH, "//span[contains(@class, 'MuiTypography-root') and contains(text(), 'short.gy')]")
        shortened_link.click()
        time.sleep(0.5)

        affiliate_link = pyperclip.paste()

        return affiliate_link
    except Exception as e:
        print(f"❌ Erro ao gerar link encurtado: {e}")
        return link_original
    finally:
        driver.quit()

def gerar_link_afiliado_amazon(link_original):
    driver = iniciar_driver_com_perfil()

    try:
        driver.get(link_original)

        get_link_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "amzn-ss-get-link-button"))
        )
        get_link_button.click()
        time.sleep(2)

        link_textarea = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "amzn-ss-text-shortlink-textarea"))
        )

        affiliate_link = link_textarea.get_attribute("value")

        pyperclip.copy(affiliate_link)

        return affiliate_link
    except Exception as e:
        print(f"❌ Erro ao gerar link afiliado Amazon: {e}")
        return link_original
    finally:
        driver.quit()

def gerar_link_afiliado_aliexpress(link_original):
    driver = iniciar_driver_com_perfil()

    try:
        driver.get(link_original)

        time.sleep(2)

        forma_do_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "get-link-pro-button"))
        )
        forma_do_link.click()
        time.sleep(2)

        copiar_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Copiar')]"))
        )
        copiar_btn.click()
        time.sleep(1)

        affiliate_link = pyperclip.paste()

        return affiliate_link
    except Exception as e:
        print(f"❌ Erro ao gerar link afiliado AliExpress: {e}")
        return link_original
    finally:
        driver.quit()

def gerar_link_afiliado_mercadolivre(link_original):
    driver = iniciar_driver_com_perfil()

    try:
        print("iniciando navegador")
        driver.get(link_mercadolivre)
        print("aba carregada")
        print(f"Link a ser acessado: {link_mercadolivre}")

        time.sleep(1)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "url-0")))
        print("input localizado")

        textarea = driver.find_element(By.ID, "url-0")
        textarea.send_keys(link_original)
        print(f"link original: {link_original}")

        print("aguardando btoao de gerar")
        generate_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Gerar')]"))
        )

        generate_button.click()
        time.sleep(3)

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Copiar')]"))
        )

        copy_button = driver.find_element(By.XPATH, "//span[contains(text(), 'Copiar')]")
        copy_button.click()
        time.sleep(0.5)  

        affiliate_link = pyperclip.paste()

        return affiliate_link
    except Exception as e:
        print(f"❌ Erro ao gerar link afiliado Mercado Livre: {e}")
        return link_original
    finally:
        driver.quit()

def extrair_preco_original(mensagem):
    for linha in mensagem.splitlines():
        if "preço" in linha.lower() or "r$" in linha.lower():
            return linha.replace("✅", "💸").strip()
    return "💸 Preço não informado"

def extrair_cupom(mensagem):
    for linha in mensagem.splitlines():
        if "Cupom:" in linha:
            return linha.strip()
    return None

def personalizar_legenda(mensagem_original, link_produto, loja):
    nome_produto = escapar_markdown(extrair_nome_com_ia(mensagem_original))
    preco = extrair_preco_original(mensagem_original)
    cupom = extrair_cupom(mensagem_original)

    legenda = f"""💥 O DEV PROGRAMOU ESSA OFERTA PRA VOCÊ!

{nome_produto}
{preco}"""
    if cupom:
        legenda += f"\n{cupom}"

    legenda += f"\n📦{link_produto}\n\n⚡️ Não esqueça de usar os cupons sempre que tiver em, o dev tá de spy em você! 😎💻"

    return legenda

def escapar_markdown(texto):
    especiais = ['*', '_', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in especiais:
        texto = texto.replace(char, f"\\{char}")
    return texto

@client.on(events.NewMessage(chats=canal_origem))
async def pegar_oferta(event):
    print(f"Nova mensagem de: {event.chat_id} | Texto: {event.message.text}")
    mensagem = event.message

    if mensagem.text and "preço" in mensagem.text.lower():
        print("\n📥 Mensagem recebida:")
        print(mensagem.text)

        link_original = extrair_link(mensagem.text)
        if link_original:
            link_expandido = expandir_link(link_original)
            loja = identificar_loja(link_expandido)

            print(f"🔎 Link expandido: {link_expandido}")
            print(f"🏪 Loja identificada: {loja}")

            nome_produto = ""
            for linha in mensagem.text.splitlines():
                if "➡️" in linha:
                    nome_produto = linha.replace("➡️", "").strip()
                    break

            if loja == "Mercado Livre":
                print("🎯 Link é do Mercado Livre! Gerando link afiliado...")
                link_expandido = gerar_link_afiliado_mercadolivre(link_expandido)
            elif loja == "Magazine Luiza":
                print("🎯 Link é do Magazine Luiza! Gerando link afiliado...")
                link_expandido = gerar_link_afiliado_magazine(nome_produto)
            elif loja == "AliExpress":
                print("🎯 Link é do AliExpress! Gerando link afiliado...")
                link_expandido = gerar_link_afiliado_aliexpress(link_expandido)
            elif loja == "Amazon":
                print("🎯 Link é do Amazon! Gerando link afiliado...")
                link_expandido = gerar_link_afiliado_amazon(link_original)
            elif loja == "Kabum":
                print("🎯 Link é do Kabum! Gerando link afiliado...")
                link_expandido = gerar_link_afiliado_kabum(link_original)
            elif loja == "Shopee":
                print("🎯 Link é do Shopee! Gerando link afiliado...")
                link_expandido = gerar_link_afiliado_shopee(link_original)
            else:
                print("🎯 Link é de uma loja não afiliada! Gerando link personalizado...")
                link_expandido = gerar_link_afiliado_encurtador(link_original)

            nova_legenda = personalizar_legenda(mensagem.text, link_expandido, loja)

            print("\n✏️ Legenda personalizada:")
            print(nova_legenda)

            try:
                if mensagem.photo:
                    await client.send_file(
                        canal_destino,
                        file=mensagem.photo,
                        caption=nova_legenda,
                        parse_mode='Markdown'
                    )
                    print("✅ Oferta enviada!\n")
                else:
                    await client.send_message(canal_destino, nova_legenda, parse_mode='Markdown')
                    print("✅ Oferta enviada!\n")
            except Exception as e:
                print(f"❌ Erro ao enviar: {e}")
        else:
            print("⚠️ Mensagem com 'Preço' mas sem link.")
    else:
        print("🔕 Ignorando mensagens de cupom")

print(f"👨🏻‍💻 Ativando o spyware no @{canal_origem} ...")
client.start()
client.run_until_disconnected()