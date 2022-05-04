# IMPORTATIONS
from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.trading_pb2 import Credentials, Update
import shelve
from degiro_connector.quotecast.api import API as QuotecastAPI
from degiro_connector.quotecast.actions.action_get_chart import ChartHelper
from degiro_connector.quotecast.models.quotecast_pb2 import Chart
import pandas as pd
from datetime import datetime
import numpy as np
import yfinance as yf
import threading 
from DictObj import DictObj

class cachedApi:
    def __init__(self, file:str, credentials=Credentials):
        self.__db = shelve.open(file)
        self.__trading_api = TradingAPI(credentials=credentials)
        self.__user_token = None
        self.__quotecast_api = None
        self.mutex = threading.Lock()
        
    def logout(self):
        self.__trading_api.logout()
    
    def cache_get(self, k):
        r = None
        #self.mutex.acquire()
        try:
            r = self.__db[k]
        except:
            None
        #self.mutex.release()
        return r

    def cache_set(self, k,v):
        self.mutex.acquire()
        self.__db[k] = v
        self.mutex.release()
    
    def get_config(self):
        return self.__trading_api.credentials

    def get_config(self,**kwargs):
        k = 'get_config' + str(kwargs)
        r = self.cache_get(k)
        if r is None:
            r = self.__trading_api.get_config(**kwargs)
            self.cache_set(k,r)
        #print(r)
        self.__user_token = r['clientId']
        #print(f"token:{self.__user_token}")
        return r

    def get_client_details(self,**kwargs):
        k = 'get_client_details' + str(kwargs)
        r = self.cache_get(k)
        if r is None:
            r = self.__trading_api.get_client_details(**kwargs)
            self.cache_set(k,r)
        #print(r)
        self.__trading_api.credentials.int_account = r["data"]["intAccount"]
        #print(f"intAccount:{self.__trading_api.credentials.int_account}")
        return r
    
    def connect(self):
        self.__trading_api.connect()
        if not self.__user_token:
            self.get_config()
        if self.__user_token:
            self.__quotecast_api = QuotecastAPI(user_token=self.__user_token)   
        session_id = self.__trading_api.connection_storage.session_id
        #print("You are now connected, with the session id :", session_id)

    def get_portfolio(self): 
        request_list = Update.RequestList()
        request_list.values.extend([
            Update.Request(option=Update.Option.PORTFOLIO, last_updated=0),
        ])
        return self.__trading_api.get_update(request_list=request_list)

    def get_list_list(self):
        return self.__trading_api.get_favourites_list(raw=True)

    def create_favourite_list(self,**kwargs):
        return self.__trading_api.create_favourite_list(**kwargs)
    
    def delete_favourite_list(self,**kwargs):
        return self.__trading_api.delete_favourite_list(**kwargs)
    
    def put_favourite_list_product(self,**kwargs):
        return self.__trading_api.put_favourite_list_product(**kwargs)
    
    def get_products_config(self,**kwargs):
        k = 'get_products_config' + str(kwargs)
        r = self.cache_get(k)
        if r is None:
            r = self.__trading_api.get_products_config(**kwargs)
            self.cache_set(k,r)
        self.indices = {}
        for li in r['indices']:
            self.indices[li['id']] = DictObj(li)
        self.countries = {}
        for li in r['countries']:
            self.countries[li['id']] = DictObj(li)
        self.exchanges = {}
        for li in r['exchanges']:
            self.exchanges[li['id']] = DictObj(li)      
        self.stockCountries =  r['stockCountries']
        return r
     
    def get_company_ratios(self,**kwargs):
        k = 'get_company_ratios' + str(kwargs)
        r = self.cache_get(k)
        if r is None:
            r = self.__trading_api.get_company_ratios(**kwargs)
            self.cache_set(k,r)
        try:
            codes = {}
                
            if 'data' in r and 'currentRatios' in r['data'] and 'ratiosGroups' in r['data']['currentRatios']:
                for an in r['data']['currentRatios']['ratiosGroups']:
                    for i in an['items']:
                        v = i.get('value') or np.NaN  # value
                        t = i.get('type') or None # type of parameter
                        k = i.get('id') or None # name of parameter
                        m = i.get('name') or "" # meaning
                        if t == 'N' and not pd.isna(v): v = float(v)
                        #elif t == 'D': v = datetime.strptime(v, '%Y-%m-%dT%H:%M:%S') #pd.to_datetime(v)
                        if not m.__contains__(' per '): v = v * 1#000000
                        if k:
                            codes[k] = { 'meaning':m, 'value':v }

            if 'data' in r and 'forecastData' in r['data'] and 'ratios' in r['data']['forecastData']:
                for i in r['data']['forecastData']['ratios']:
                    #print(i)
                    v = i.get('value') or np.NaN  # value
                    t = i.get('type') or None # type of parameter
                    k = i.get('id') or None # name of parameter
                    m = i.get('name') or "" # meaning
                    if t == 'N' and not pd.isna(v): v = float(v)
                    #elif t == 'D': v = datetime.strptime(v, '%Y-%m-%dT%H:%M:%S') #pd.to_datetime(v)
                    if not m.__contains__(' per '): v = v * 1#000000
                    if k:
                        codes[k] = { 'meaning':m, 'value':v }

            if 'data' in r and 'consRecommendationTrend' in r['data'] and 'ratings' in r['data']['consRecommendationTrend']:
                for i in r['data']['consRecommendationTrend']['ratings']:
                    #print(i)
                    v = i.get('value') or np.NaN  # value
                    k = ('ratings_'+i.get('periodType')) or None # name of parameter
                    if t == 'N' and not pd.isna(v): v = float(v)
                    #elif t == 'D': v = datetime.strptime(v, '%Y-%m-%dT%H:%M:%S') #pd.to_datetime(v)
                    if not m.__contains__(' per '): v = v * 1#000000
                    if k:
                        codes[k] = { 'meaning':'', 'value':v }
                    
            codes['priceCurrency'] = { 'meaning':'', 'value':r['data']['currentRatios']['priceCurrency'] }
            if len(codes['priceCurrency']) <= 1:
                codes['priceCurrency'] = { 'meaning':'', 'value':r['data']['currentRatios']['currency'] }
        except:
            None
        return codes

    def get_financial_statements(self,**kwargs):
        k = 'get_financial_statements' + str(kwargs)
        r = self.cache_get(k)
        if r is None:
            r = self.__trading_api.get_financial_statements(**kwargs)
            self.cache_set(k,r)
        codes_array = []
        if r:
            try:
                for t in ('annual','interim'):
                    if t in r['data']:
                        for an in r['data'][t]:
                                endDate = datetime.strptime(an.get('endDate'), '%Y-%m-%d')#T%H:%M:%S')
                                fiscalYear = an.get('fiscalYear')
                                periodNumber = an.get('periodNumber') or 'Y'
                                codes = {}
                                for st in an['statements']:
                                    periodLength = st.get('periodLength')
                                    periodType = st.get('periodType')
                                    for i in st['items']:
                                        v = i.get('value') or np.NaN 
                                        if not pd.isna(v): v = float(v)
                                        if not i.get('meaning').__contains__(' per '): v = v * 1#000000
                                        codes[i.get('code')] = { 'meaning':i.get('meaning'), 'value':v }
                                codes_array += [ codes ]
            except:
                #print(k)
                #traceback.print_exc()
                #del self.cache_get(k)
                None
        return codes_array
    
    
    
    def get_estimates_summaries(self,**kwargs):
        k = 'get_estimates_summaries_' + str(kwargs)
        r = self.cache_get(k)
            #print("get_estimates_summaries cache hit", type(r))
        if r is None:
            r = self.__trading_api.get_estimates_summaries(**kwargs)
            #print("get_estimates_summaries cache miss", type(r))
            self.cache_set(k,r)
        return r
    
    def get_products_info(self,**kwargs):
        k = 'get_products_info' + str(kwargs)
        r = self.cache_get(k)
            #print("get_products_info cache hit", r)
        if r is None:
            r = self.__trading_api.get_products_info(**kwargs)
            #print("get_products_info cache miss", r)
            self.cache_set(k,r)
        return r

    def get_chart(self,**kwargs):
        k = 'get_chart' + str(kwargs)
        r = self.cache_get(k)
            #print("get_chart cache hit", r)
        if r is None:
            r = self.__quotecast_api.get_chart(**kwargs)
            #print("get_chart cache miss", r)
            self.cache_set(k,r)
        return r

    def product_search(self,**kwargs):
        k = 'product_search' + str(kwargs)
        r = self.cache_get(k)
        if r is None:
            r = self.__trading_api.product_search(**kwargs)
#        if hasattr(r, 'products'):
            self.cache_set(k,r)
#        else:
#            r = None
        return r

    def get_longtermprice(self,vwdIdSecondary:str):
        qrequest = Chart.Request()
        qrequest.culture = "fr-FR"
        qrequest.period = Chart.Interval.P1Y
        qrequest.requestid = "1"
        qrequest.resolution = Chart.Interval.P1D
        qrequest.series.append("ohlc:"+vwdIdSecondary)
        qrequest.tz = "Europe/Paris"
        chart = self.get_chart(request=qrequest,raw=False)
        price = pd.DataFrame()
        try:
            c2=ChartHelper.format_chart(chart=chart, copy=False)
            price = ChartHelper.serie_to_df(serie=chart.series[0])
            price["timestamp"] = pd.to_datetime(price["timestamp"], unit="s")
        except:
            #print(f"Error chart {vwdIdSecondary}")
            None
        #price.set_index("timestamp", inplace=True)
        return price

    def get_company_profile(self,**kwargs):
        k = 'get_company_profile' + str(kwargs)
        r = self.cache_get(k)
        if r is None:
            #searching on Degiro
            r = self.__trading_api.get_company_profile(product_isin=kwargs['product_isin'], raw=kwargs['raw'])
            self.cache_set(k,r)
        
        codes = {}
        if r is not None and 'data' in r:
            r_data = r['data']
            try:
                codes['sector'] = r_data['sector']
            except:
                None
            try:
                codes['industry'] =  r_data['industry']
            except:
                None
            try:
                codes['country'] =  r_data['contacts']['COUNTRY']
            except:
                None
            try:
                codes['floatShares'] = float(r_data['shrFloating']) / 10**6
            except:
                None
            try:
                codes['businessSummary'] = r_data['businessSummary']
            except:
                None
   
            try:
                if 'ratios' in r_data and 'ratiosGroups' in r_data['ratios']:
                    for an in r_data['ratios']['ratiosGroups']:
                        for i in an['items']:
                            v = i.get('value') or np.NaN  # value
                            t = i.get('type') or None # type of parameter
                            k = i.get('id') or None # name of parameter
                            m = i.get('name') or "" # meaning
                            if t == 'N' and not pd.isna(v): v = float(v)
                            #elif t == 'D': v = datetime.strptime(v, '%Y-%m-%dT%H:%M:%S') #pd.to_datetime(v)
                            if not m.__contains__(' per '): v = v * 1#000000
                            if k:
                                codes[k] = { 'meaning':m, 'value':v }
                if 'forecastData' in r_data and 'ratios' in r_data['forecastData']:
                    for i in r_data['forecastData']['ratios']:
                        #print(i)
                        v = i.get('value') or np.NaN  # value
                        t = i.get('type') or None # type of parameter
                        k = i.get('id') or None # name of parameter
                        m = i.get('name') or "" # meaning
                        if t == 'N' and not pd.isna(v): v = float(v)
                        #elif t == 'D': v = datetime.strptime(v, '%Y-%m-%dT%H:%M:%S') #pd.to_datetime(v)
                        if not m.__contains__(' per '): v = v * 1#000000
                        if k:
                            codes[k] = { 'meaning':m, 'value':v }
            except:
                None
        else: 
            # searching on Yahoo! finance
            try:
                r = self.cache_get('Y_'+k)
            except:
                sym = yf.Ticker(kwargs['product_isin'])
                r = sym.info
                try:
                    r['marketCap'] /= 1000.0
                except:
                    pass
                self.cache_set('Y_'+k, r)
                print(f"OK from Yahoo {kwargs['product_isin']}")
            codes = r
        return codes

