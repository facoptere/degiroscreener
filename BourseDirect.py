import selenium.common.exceptions
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import datetime as dt
import time
import re
import urllib.parse
import pandas as pd

class BourseDirect:
    def __init__(self, Display, login, password, download_path):
    
        self.login = login
        self.password = password
        self.dwd_path = download_path
        timeout = 5
        s = Service(ChromeDriverManager(log_level=5).install())
        chrome_options = Options()
        if download_path == None:
            pass
        else:
            prefs = {"download.default_directory": download_path}
            chrome_options.add_experimental_option("prefs", prefs)

        if Display == False: # does not worl on WSL
            chrome_options.add_argument("--headless");
            chrome_options.add_argument("--disable-gpu");
            chrome_options.add_argument("--window-size=1920,1200");
            chrome_options.add_argument("--ignore-certificate-errors");
            chrome_options.add_argument("--disable-extensions");
            chrome_options.add_argument("--no-sandbox");
            chrome_options.add_argument("--disable-dev-shm-usage");
            self.driver = webdriver.Chrome(service=s, options=chrome_options)
            self.driver.maximize_window()
        else:
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument("--window-size=1920x1080")
            self.driver = webdriver.Chrome(service=s, options=chrome_options)
            self.driver.maximize_window()

        self.driver.get("https://www.boursedirect.fr/fr/login")
        print('\n> Connexion...')

        notice = EC.presence_of_element_located((By.ID, 'didomi-notice-agree-button'))
        WebDriverWait(self.driver, timeout).until(notice).click()

        self.driver.find_element(by=By.ID, value='bd_auth_login_type_login').send_keys(str(self.login))
        self.driver.find_element(by=By.ID, value='bd_auth_login_type_password').send_keys(str(self.password))
        self.driver.find_element(by=By.ID, value='bd_auth_login_type_submit').click()

        timeout = 5
        try:
            pub = EC.presence_of_element_located((By.CLASS_NAME, 'btn-modal-close'))
            WebDriverWait(self.driver, timeout).until(pub).click()
        except selenium.common.exceptions.ElementNotInteractableException:
            pass

        print("> Connecté à Bourse Direct.",end='\r')

    def close_connection(self):
        self.driver.close()

    def execute(self, order):

        self.order = order
        self.ordertype = order['ORDERTYPE']

        searchbar = EC.presence_of_element_located((By.ID, 'searchbar-input'))
        timeout = 5
        WebDriverWait(self.driver, timeout).until(searchbar).send_keys(str(self.order['ISIN']))

        self.driver.find_element(by='id', value="searchbar-input").send_keys(Keys.ENTER)

        tradingboard = EC.presence_of_element_located((By.ID, 'quantity'))
        timeout = 5
        WebDriverWait(self.driver, timeout).until(tradingboard).send_keys(str(self.order['QUANTITE']))

        if self.order['SENS'] == 'achat':
            self.driver.find_element(by=By.XPATH,
                                     value='/html/body/div[4]/div[4]/div/div[2]/div[1]/div[2]/header/div[3]/div/div/div/div/div/div/form/div/div[2]/div/div[1]/div/div[1]/div/div[1]/div/div/label[1]').click()

        elif self.order['SENS'] == 'vente':
            self.driver.find_element(by=By.XPATH,
                                     value='/html/body/div[4]/div[4]/div/div[2]/div[1]/div[2]/header/div[3]/div/div/div/div/div/div/form/div/div[2]/div/div[1]/div/div[1]/div/div[1]/div/div/label[2]').click()

        if self.ordertype == 'market':
            self.market_order()

        elif self.ordertype == 'limit':
            self.limit_order()

        elif self.ordertype == 'best_limit':
            self.best_limit_order()

        elif self.ordertype == 'tal':
            self.tal_order()

        elif self.ordertype == 'stop':
            self.stop_order()

        elif self.ordertype == 'stop_limit':
            self.stop_limit_order()

        self.validation()
        return

    def validation(self):

        if self.order['VIRTUAL'] == 'on':
            print("[VIRTUAL]--> Ordre envoyé (heure d\'envoi) {}.".format(dt.datetime.now().strftime('%H:%M:%S')))
            return
        elif self.order['VIRTUAL'] == 'off':

            validation = EC.presence_of_element_located((By.CLASS_NAME, 'container-validate'))
            timeout = 5
            WebDriverWait(self.driver, timeout).until(validation).click()

            time.sleep(2)
            validation = EC.presence_of_element_located((By.CLASS_NAME, 'container-validate'))
            timeout = 5
            WebDriverWait(self.driver, timeout).until(validation).click()
            print('--> Ordre envoyé (heure d\'envoi) {}.'.format(dt.datetime.now().strftime('%H:%M:%S')))
            time.sleep(2)
            self.driver.find_element(by=By.XPATH,
                                     value='/html/body/div[4]/div[4]/div/div[2]/div[1]/div[2]/header/div[3]/div/div/div/div/div/div/div/div/div/p[1]/a/i').click()

            print('--> TermSheet téléchargée.')
            return

    def market_order(self):

        select = Select(self.driver.find_element(by=By.ID, value='order_type'))
        select.select_by_value('market')

    def limit_order(self):

        select = Select(self.driver.find_element(by=By.ID, value='order_type'))
        select.select_by_value('limit')

        timeout = 5
        limit = EC.presence_of_element_located((By.ID, 'limit'))
        WebDriverWait(self.driver, timeout).until(limit).send_keys(str(self.order['LIMIT/STOP']).replace('.', ','))

    def best_limit_order(self):

        select = Select(self.driver.find_element(by=By.ID, value='order_type'))
        select.select_by_value('best_limit')  # market, limit, best_limit, stop, stop_limit, tal

    def tal_order(self):

        select = Select(self.driver.find_element(by=By.ID, value='order_type'))
        select.select_by_value('tal')  # market, limit, best_limit, stop, stop_limit, tal

    def stop_order(self):

        select = Select(self.driver.find_element(by=By.ID, value='order_type'))
        select.select_by_value('stop')  # market, limit, best_limit, stop, stop_limit, tal
        self.driver.find_element(by=By.ID, value='stop').send_keys(str(self.order['LIMIT/STOP']).replace('.', ','))

    def stop_limit_order(self, order):
        select = Select(self.driver.find_element(by=By.ID, value='order_type'))
        select.select_by_value('stop_limit')  # market, limit, best_limit, stop, stop_limit, tal
        self.driver.find_element(by=By.ID, value='limit').send_keys(str(order['LIMIT/STOP'][0]).replace('.', ','))
        self.driver.find_element(by=By.ID, value='stop').send_keys(str(order['LIMIT/STOP'][1]).replace('.', ','))

    def show_portfolio(self):
        timeout = 5
        current_url = self.driver.current_url
        e = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.ID, 'user-dropdown'))
            )
        if e:
            e.click()
        
        e = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.XPATH, '//a[@id="user-dropdown"]/../div/ul/li[1]/a'))
            )
        if e:
            e.click()
            
        WebDriverWait(self.driver, timeout).until(EC.url_changes(current_url))
        current_url = self.driver.current_url
        print('got portfolio page', current_url)
        WebDriverWait(self.driver, timeout).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH,"/html/body/div[4]/div[4]/div/div[2]/iframe")))
        
        rl = self.driver.find_elements(by=By.XPATH, value="//div[@id='detailTableHolder']/table/tbody[2]/tr")
        df = pd.DataFrame()
        if rl:
            for r in rl:
                cl = r.find_elements(by=By.XPATH, value=".//td")
                if cl:
                    asset=[]
                    for c in cl:
                        t = re.sub("(^ *| *$|(?<=[0-9]) (?=[0-9])| €$| *%$|\([^\)]*\))","",c.text)
                        t =re.sub("(?<=[0-9]),(?=[0-9])",".",t)
                        if len(asset) == 0: # first cell is asset name with anchor
                            link=''
                            ticker=''
                            try:
                                e = c.find_element(by=By.XPATH, value="./a")
                                link = e.get_attribute('href')
                                link = urllib.parse.unquote(link)
                                link = re.sub("(^javascript:popupStream\(\'|\'.*$)","",link)
                                link = 'https://www.boursedirect.fr/priv/new/'+link
                                ticker = re.sub("(^.*val=E:|&.*$)","",link)
                            except:
                                pass
                            asset.append(ticker)
                            asset.append(link)
                        else:
                            try:
                                t = float(t)
                            except:
                                pass
                        asset.append(t)
                    if len(asset) == 11 and isinstance(asset[9], float): # skipping stocks where buy is in progress
                        # 11 columns: ticker url name Qté 	PRU 	Cours 	Valo 	+/-Val. 	var/PRU 	var/Veille 	%
                        row = {
                            'ticker' : asset[0],
                            'url' : asset[1],
                            'name' : asset[2],
                            'Qté' : asset[3],
                            'PRU' : asset[4],	
                            'Cours' : asset[5], 	
                            'Valo' : asset[6], 	
                            '+/-Val.' : asset[7], 	
                            'var/PRU' : asset[8], 	
                            'var/Veille' : asset[9], 	
                            '%' : asset[10],
                        }
                        df = df.append(row,ignore_index=True)
                        print(asset)
        return df    
