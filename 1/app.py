import pandas as pd
from sqlalchemy import create_engine
import streamlit as st
from dotenv import load_dotenv
import yfinance as yf
import os
from defs import input_data
from defs import load_stock_price
from plotly.subplots import make_subplots
import plotly.graph_objects as go

load_dotenv(override=True) # 나중에 다시 연결해보기


# 텍스트 박스 => 검색한 회사 주가 가져옴
company_ticker = st.text_input(label = 'ticker(ex: 005930 삼성전자)')
term_map = {'1개월' : 30, '3개월' : 90, '6개월' : 120, '전체' : 'all'}
term = term_map[st.selectbox("기간 선택", list(term_map.keys()))]
clicked = st.button('확인')

if clicked:
    try:
        company_data = pd.DataFrame( load_stock_price(company_ticker, company_ticker, term) )
        fig = make_subplots (rows =2 , cols = 1, shared_xaxes = True, row_heights=[0.7, 0.3])

        fig.add_trace(go.Scatter(x=company_data.index, y=company_data['Close'], name='Close'), row=1, col=1)
        fig.add_trace(go.Scatter(x=company_data.index, y=company_data['MA_5'], name='MA_5'), row=1, col=1)
        fig.add_trace(go.Scatter(x=company_data.index, y=company_data['MA_20'], name='MA_20'), row=1, col=1)

        fig.add_trace(go.Bar(x=company_data.index, y=company_data['Volume'], name='Volume'), row=2, col=1)
        
        st.plotly_chart(fig)

        highest = company_data['High'].max()
        lowest = company_data['Low'].min()
        volume_mean = company_data['Volume'].mean()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(label='최고가', value=f"{highest:,}원")
        with col2:
            st.metric(label='최저가', value=f"{lowest:,}원")
        with col3:
            st.metric(label='평균 거래량', value=f"{float(volume_mean)/1000:,.0f}K")
        with col4:
            st.metric(label='현재가', value=f"{company_data['Close'][-1]}원")
    except Exception as e:
        st.error(e)
        st.error("티커를 정확하게 입력해 주세요")



