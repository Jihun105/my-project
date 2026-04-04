import pandas as pd
import numpy as np

# 이닝 float로 바꿔주는 함수
# ======================================================================================================
def convert_ip(value):
    try:
        parts = str(value).split()
        if len(parts) == 1:
            return float(parts[0])
        v_num, v_str = parts
        v1, v2 = v_str.split('/')
        return float(v_num) + int(v1) / int(v2)
    except:
        return 0 
# ======================================================================================================


# 파일 불러오기
# ======================================================================================================
df_batter_offence = pd.read_csv('data_csv/batter_offence.csv', encoding='utf-8')
df_batter_offence2 = pd.read_csv('data_csv/batter_offence2.csv', encoding='utf-8')
df_batter_defence = pd.read_csv('data_csv/batter_defence.csv', encoding='utf-8')
df_pitcher = pd.read_csv('data_csv/pitcher.csv', encoding='utf-8')
df_team = pd.read_csv('data_csv/team.csv', encoding='utf-8')
# ======================================================================================================


# tema table 전처리
# ======================================================================================================
df = pd.DataFrame(df_team)
df_copy = df.copy()
df_team = df_copy.drop(columns = ['game' ,'winning_rate', 'games_behind', 'recent10'], axis=1)
df_team[['home_win', 'home_draw', 'home_lose']] = df_team['home'].str.split('-', expand=True).astype(int)
# expand=True : 분리된 값을 각각 컬럼으로 확장
df_team[['away_win', 'away_draw', 'away_lose']] = df_team['away'].str.split('-', expand=True).astype(int)
df_team = df_team.drop(columns=['home', 'away'], axis=1)
# ======================================================================================================


# batter offence 1, 2 전처리
# ======================================================================================================
df = pd.DataFrame(df_batter_offence)
df_copy=df.copy()
df_offence = df_copy.drop(['tb', 'sac'], axis = 1)
df_offence = df_offence.rename(columns= {'pa' : 'plate_appearance' , 'ab' : 'abat', 'r': 'scored'})
df_offence = df_offence.drop(columns=['Unnamed: 0'])
df_offence = df_offence.replace('-', np.nan)
df_offence[ df_offence.isnull().any(axis=1) ]
df_offence = df_offence.dropna()

df = pd.DataFrame(df_batter_offence2)
df_copy=df.copy()
df_offence2 = df_copy.drop(['mh','ph_ba'], axis=1)
df_offence2 = df_offence2.rename(columns = {'gdp' : 'double_play'})
df_offence2 = df_offence2.drop(columns=['Unnamed: 0'])
df_offence2 = df_offence2.replace('-', np.nan)
df_offence2[ df_offence2.isnull().any(axis=1) ]
df_offence2 = df_offence2.dropna()
# ======================================================================================================


# defence catcher 전처리
# ======================================================================================================
df = pd.DataFrame(df_batter_defence)
df_catcher = df[df['position'] == '포수']
df_catcher = df_catcher.drop(columns=['Unnamed: 0', 'pko'])
df_catcher = df_catcher.rename(columns ={'inning_defence' : 'inning'})
df_catcher[ df_catcher.isin(['-']).any(axis=1) ]
df_catcher = df_catcher.replace('-', np.nan)
df_catcher = df_catcher.dropna()
df_catcher['inning'] = df_catcher['inning'].apply(convert_ip).round(3)
# ======================================================================================================


# defence fielder 전처리
# ======================================================================================================
df = pd.DataFrame(df_batter_defence)
df_fielder = df[df['position'] != '포수']
df_fielder = df_fielder.drop(columns=['Unnamed: 0', 'pko', 'pb', 'sb', 'cs', 'cs_pct'])
df_fielder = df_fielder.rename(columns ={'inning_defence' : 'inning'})
df_fielder[df_fielder.isin(['-']).any(axis=1)]
df_fielder = df_fielder.replace('-', 0)
df_fielder['inning'] = df_fielder['inning'].apply(convert_ip).round(3)
# ======================================================================================================

# pitcher 전처리
# ======================================================================================================
df = pd.DataFrame(df_pitcher)
df_pitcher = df.copy()
df_pitcher[ df_pitcher.isin(['-']).any(axis=1) ]
df_pitcher = df_pitcher.drop(columns=['Unnamed: 0', 'wpct'])
df_pitcher['inning'] = df_pitcher['inning'].apply(convert_ip).round(3)
# ======================================================================================================




