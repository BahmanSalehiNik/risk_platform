import requests
import json
from pandas import DataFrame as df


def login(username, password):
    body = {'username': username, 'password': password}
    resp = requests.post('http://api.bourseview.com/login', data=json.dumps(body))
    data = json.loads(resp.text)
    print(data['token'])
    return {"token":data['token'], "expiration_date":data['expiration']}


def quotes(start_date, end_date):
    token = login("kardaninvestment","kardaninvestment")["token"]
    url = "http://api.bourseview.com/v1/stocks/quotes?items=adjusted&exchanges=IRTSENO,IRIFBNO,IRIFBOTC&date=" + "[" + start_date +"," + end_date + "]"
    header = {"Authorization": token}
    res = requests.get(url, headers=header)
    return json.loads(res.content.decode('utf-8'))['tickers']


def get_all_stocks():
    token = login("kardaninvestment","kardaninvestment")["token"]
    url = "http://api.bourseview.com/v1/stocks"
    header = {"Authorization": token}
    res = requests.get(url, headers=header)
    return json.loads(res.content.decode('utf-8'))['tickers']

def get_ticker_quotes(ticker, start_date, end_date):
    token = login("kardaninvestment", "kardaninvestment")["token"]
    url = "http://api.bourseview.com/v1/stocks/quotes?items=adjusted&exchanges=IRTSENO,IRIFBNO,IRIFBOTC&tickers=" + ticker + "&date=" + "[" + start_date +"," + end_date + "]"
    header = {"Authorization": token}
    res = requests.get(url, headers=header)
    res_j = json.loads(res.content.decode('utf-8'))['tickers']
    df_test = df(res_j[0]['items'][0]['days'])
    df_total = df()
    for index, row in df_test.iterrows():
        temp_dict = row['items'][0]['values']
        temp_dict['time'] = row['time']
        df_total = df_total.append(temp_dict, ignore_index=True)
    return df_total


# ---- test ---
if __name__=="__main__":
    data = get_ticker_quotes('IRO1GDIR0001', '20200520', '20200526')
    print(data)