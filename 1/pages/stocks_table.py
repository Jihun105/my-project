import FinanceDataReader as fdr
from defs import finance_data

df = fdr.StockListing('KOSPI')
df_copy = df.copy()

import streamlit as st
df_copy['Ticker'] = df['Code']
stocks = df_copy[['Name', 'Ticker']]

stock_name = st.text_input('종목 명')
st.dataframe ( stocks[stocks['Name'].str.contains(stock_name)] )

ticker_input = st.text_input('티커 입력 (ex: 005930)')
if st.button('데이터 조회'):
    st.dataframe(finance_data(ticker_input + '.KS'))


