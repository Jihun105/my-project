import yfinance as yf
import FinanceDataReader as fdr
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from sqlalchemy import create_engine
from datetime import datetime
from datetime import datetime, timedelta

def input_data(name, ticker, period):
    """name : company code , ticker : company code, period : 기간(일수 또는 'all')"""
    if period == 'all':
        data = fdr.DataReader(ticker, start='2000-01-01')
    else:
        start = datetime.now() - timedelta(days=period)
        data = fdr.DataReader(ticker, start=start)
    
    print(data.columns)
    data.columns = ['Close', 'High', 'Low', 'Open', 'Volume', 'Change']
    data['MA_5'] = data['Close'].rolling(window=5).mean()
    data['MA_20'] = data['Close'].rolling(window=20).mean()

    engine = create_engine("mysql+pymysql://root:!kjh71114489@localhost/stock_db")
    data.to_sql(name=name, con=engine, if_exists='replace')


def load_stock_price(name, ticker, period):
    """name : company code, ticker : company code, period : 기간(일수 또는 'all')"""
    engine = create_engine("mysql+pymysql://root:!kjh71114489@localhost/stock_db")


    try:
        # 데이터 부족하면 새로 가져오기
        if period != 'all':
            expected_start = datetime.now() - timedelta(days=period)
            db_start = load_cdb.index.min()
            if pd.Timestamp(db_start) > pd.Timestamp(expected_start):
                input_data(name, ticker, period)
                load_cdb = pd.read_sql(query, con=engine, index_col='Date')
        
        return load_cdb
    except:
        input_data(name, ticker, period)
        if period == 'all':
            query = f"SELECT * FROM `{name}`"
        else:
            query = f"SELECT * FROM `{name}` WHERE Date >= DATE_SUB(NOW(), INTERVAL {period} DAY)"
        
        load_cdb = pd.read_sql(query, con=engine, index_col='Date')
        return load_cdb

# 재무 데이터 가져오기
def finance_data(ticker):
    stock = yf.Ticker(ticker)
    keys = ['epsCurrentYear', 'forwardPE', 'returnOnEquity', 'profitMargins', 'revenueGrowth', 'earningsGrowth', 'dividendYield', 'debtToEquity', 'currentRatio','quickRatio' ]
    valuable = {k : stock.info.get(k, None) for k in keys}
    df = pd.DataFrame([valuable])

    return df
