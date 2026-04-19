from defs import load_stock_price
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from plotly.subplots import make_subplots
import plotly.graph_objects as go

company_ticker = st.text_input(label = 'ticker(ex: 005930 삼성전자)')
term_map = {'1개월' : 30, '3개월' : 90, '6개월' : 120, '전체' : 'all'}
term = term_map[st.selectbox("기간 선택", list(term_map.keys()))]
clicked = st.button('확인')

if clicked:
    company_data = pd.DataFrame(load_stock_price(company_ticker, company_ticker, term))
    
    if term == 'all':
        short, long = 50, 200
    else:
        short, long = 5, 20
    
    company_data[f'MA_{short}'] = company_data['Close'].rolling(window=short).mean()
    company_data[f'MA_{long}'] = company_data['Close'].rolling(window=long).mean()

    # 매수신호
    company_data['signal'] = np.where(company_data[f'MA_{short}'] > company_data[f'MA_{long}'], 1, -1)
    company_data = company_data[19:]
    change = (company_data['signal']==1) & (company_data['signal'].shift(1) == -1)
    golden_cross = company_data[change]


    # 매도 신호
    company_data['signal'] = np.where(company_data[f'MA_{short}'] > company_data[f'MA_{long}'], 1, -1)
    company_data = company_data[19:]
    change = (company_data['signal']==-1) & (company_data['signal'].shift(1) == 1)
    dead_cross = company_data[change]


    fig = make_subplots(rows=2, cols=1)

    fig.add_trace(go.Scatter(x=company_data.index,
                            y=company_data['Close'], 
                            name='Close', mode='lines'), 
                            row=1, col=1)
    fig.add_trace(go.Scatter(x=dead_cross.index,
                            y=dead_cross['Close'],
                            mode='markers',
                            marker=dict(
                                size=10,
                                color='blue',
                                symbol='triangle-down'
                            ),name='Dead_cross'),
                            row=1,col=1)
    fig.add_trace(go.Scatter(x=golden_cross.index,
                            y=golden_cross['Close'],
                            mode='markers',
                            marker=dict(
                                size=10,
                                color='red',
                                symbol='triangle-up'
                            ),name='Golden_cross'),
                            row=1,col=1)

    fig.add_trace(go.Scatter(x=company_data.index, y=company_data['MA_5'], name='MA_5'),row=2,col=1)
    fig.add_trace(go.Scatter(x=company_data.index, y=company_data['MA_20'], name='MA_20'),row=2, col=1)
    st.plotly_chart(fig)