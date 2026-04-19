import FinanceDataReader as fdr
from sqlalchemy import create_engine

# KOSPI ticker, 종목명 테이블 만들기
engine = create_engine("mysql+pymysql://root:!kjh71114489@localhost/stock_db")

kospi = fdr.StockListing('KOSPI')
ticker_info = kospi[['Code', 'Name']]
ticker_info.columns = ['ticker', 'name']
ticker_info.to_sql('ticker_info', con=engine, if_exists='replace', index=False)