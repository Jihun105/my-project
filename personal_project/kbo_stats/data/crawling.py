import pandas as pd
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By  # By.ID 사용하기 위해 임포트
import time
from selenium.webdriver.support.ui import Select # 드롭다운 다루는 클래스 임포트


# batter offence
# batter_offence1.csv crawling
#==========================================================================================================================
def crawl_batter_offence():
    # 드라이버 설정
    service = Service( ChromeDriverManager().install() ) # 크롬 드라이버 자동 설치
    driver = webdriver.Chrome(service=service) # 실제 브라우저 실행
    # 페이지 열기
    driver.get('https://www.koreabaseball.com/Record/Player/HitterBasic/Basic1.aspx')
    datas = []
    for year in [2022, 2023, 2024, 2025, 2026]:
        select = Select(driver.find_element(By.ID, 'cphContents_cphContents_cphContents_ddlSeason_ddlSeason'))  # 드롭다운 요소 찾기
        select.select_by_value( str(year) )
        time.sleep(1)
        for position, value in [('포수', '2'), ('내야수', '3,4,5,6'), ('외야수', '7,8,9')]:
            select = Select(driver.find_element(By.ID, 'cphContents_cphContents_cphContents_ddlPos_ddlPos'))
            select.select_by_value(value)
            time.sleep(1)
            for page in range(1,6): # 1~5 페이지 반복
                try: 
                    if page > 1: # 1페이지는 이미 열려있으니까 클릭 건너뜀
                        btn = driver.find_element(By.ID, f'cphContents_cphContents_cphContents_ucPager_btnNo{page}')  # page 변수로 id 동적 생성
                        btn.click()  # 버튼 클릭
                        time.sleep(1)  # 페이지 로딩 기다리기
                except:
                    break
        #==========================================================================================================================
                html = driver.page_source # 현재 브라우저에 렌더링 된 HTML 전체 가져옴
                soup = BeautifulSoup(html, 'lxml') # lxml : 빠른 파서
                result = soup.select_one('#cphContents_cphContents_cphContents_udpContent > div.record_result > table > tbody')
                result = result.select('tr')
        #==========================================================================================================================
                columns = ['name', 'team', 'avg', 'game_cnt', 'pa', 'ab', 'r', 'hit', '2b', '3b', 'home_run', 'tb', 'rbi', 'sac', 'sf' ]
                for row in result:
                    tds = row.select('td')
                    values = [td.text.strip() for td in tds[1:]]
                    data = {'year' : year, 'position' : position}
                    data.update( dict(zip(columns, values)) )
                    datas.append(data)
    driver.quit()

    df_batter_offence = pd.DataFrame(datas)
    return df_batter_offence
#==========================================================================================================================  



# def batter_offence2.csv crawling
#==========================================================================================================================
def crawl_batter_offence2():
    # 드라이버 설정
    service = Service( ChromeDriverManager().install() ) # 크롬 드라이버 자동 설치
    driver = webdriver.Chrome(service=service) # 실제 브라우저 실행
    # 페이지 열기
    driver.get('https://www.koreabaseball.com/Record/Player/HitterBasic/Basic2.aspx')
    datas = []
    for year in [2022, 2023, 2024, 2025, 2026]:
        select = Select(driver.find_element(By.ID, 'cphContents_cphContents_cphContents_ddlSeason_ddlSeason'))  # 드롭다운 요소 찾기
        select.select_by_value( str(year) )
        time.sleep(1)
        for position, value in [('포수', '2'), ('내야수', '3,4,5,6'), ('외야수', '7,8,9')]:
            select = Select(driver.find_element(By.ID, 'cphContents_cphContents_cphContents_ddlPos_ddlPos'))
            select.select_by_value(value)
            time.sleep(1)
            for page in range(1,6): # 1~5 페이지 반복
                try: 
                    if page > 1: # 1페이지는 이미 열려있으니까 클릭 건너뜀
                        btn = driver.find_element(By.ID, f'cphContents_cphContents_cphContents_ucPager_btnNo{page}')  # page 변수로 id 동적 생성
                        btn.click()  # 버튼 클릭
                        time.sleep(1)  # 페이지 로딩 기다리기
                except:
                    break
         #==============================================================================================================
                html = driver.page_source # 현재 브라우저에 렌더링 된 HTML 전체 가져옴
                soup = BeautifulSoup(html, 'lxml') # lxml : 빠른 파서
                result = soup.select_one('#cphContents_cphContents_cphContents_udpContent > div.record_result > table > tbody')
                result = result.select('tr')
        #===============================================================================================================
                columns = ['name', 'team', 'avg', 'bb', 'ibb', 'hbp', 'so', 'gdp', 'slg', 'obp', 'ops', 'mh', 'risp', 'ph_ba' ]
                for row in result:
                    tds = row.select('td')
                    values = [td.text.strip() for td in tds[1:]]
                    data = {'year' : year, 'position' : position}
                    data.update( dict(zip(columns, values)) )
                    datas.append(data)
    driver.quit()
    df_batter_offence2 = pd.DataFrame(datas)
    return df_batter_offence2
#==========================================================================================================================


# batter_defence.csv crawling
#==========================================================================================================================
def crawl_batter_defence():
    # 드라이버 설정
    service = Service( ChromeDriverManager().install() ) # 크롬 드라이버 자동 설치
    driver = webdriver.Chrome(service=service) # 실제 브라우저 실행
    # 페이지 열기
    driver.get('https://www.koreabaseball.com/Record/Player/Defense/Basic.aspx')
    datas = []
    for year in [2022, 2023, 2024, 2025, 2026]:
        select = Select(driver.find_element(By.ID, 'cphContents_cphContents_cphContents_ddlSeason_ddlSeason'))  # 드롭다운 요소 찾기
        select.select_by_value( str(year) )
        time.sleep(1)
        for position, value in [('포수', '2'), ('내야수', '3,4,5,6'), ('외야수', '7,8,9')]:
            select = Select(driver.find_element(By.ID, 'cphContents_cphContents_cphContents_ddlPos_ddlPos'))
            select.select_by_value(value)
            time.sleep(1)
            for page in range(1,6): # 1~5 페이지 반복
                try: 
                    if page > 1: # 1페이지는 이미 열려있으니까 클릭 건너뜀
                        btn = driver.find_element(By.ID, f'cphContents_cphContents_cphContents_ucPager_btnNo{page}')  # page 변수로 id 동적 생성
                        btn.click()  # 버튼 클릭
                        time.sleep(1)  # 페이지 로딩 기다리기
                except:
                    break
        #==============================================================================================================
                html = driver.page_source # 현재 브라우저에 렌더링 된 HTML 전체 가져옴
                soup = BeautifulSoup(html, 'lxml') # lxml : 빠른 파서
                result = soup.select_one('#cphContents_cphContents_cphContents_udpContent > div.record_result > table > tbody')
                result = result.select('tr')
        #==============================================================================================================
                columns = ['name', 'team', 'detail_position','game', 'gama_starter', 'inning_defence', 'error', 'pko', 'po', 'assist', 'double_play', 'fpct', 'pb', 'sb', 'cs', 'cs_pct']
                for row in result:
                    tds = row.select('td')
                    values = [td.text.strip() for td in tds[1:]]
                    data = {'year' : year, 'position' : position}
                    data.update( dict(zip(columns, values)) )
                    datas.append(data)
    driver.quit()
    df_batter_defence = pd.DataFrame(datas)
    return df_batter_defence
#==========================================================================================================================  


# pitcher crawling
#==========================================================================================================================  
def crawl_pitcher():
    # 드라이버 설정
    service = Service( ChromeDriverManager().install() ) # 크롬 드라이버 자동 설치
    driver = webdriver.Chrome(service=service) # 실제 브라우저 실행
    # 페이지 열기
    driver.get('https://www.koreabaseball.com/Record/Player/PitcherBasic/Basic1.aspx')
    datas = []
    for year in [2022, 2023, 2024, 2025, 2026]:
        select = Select(driver.find_element(By.ID, 'cphContents_cphContents_cphContents_ddlSeason_ddlSeason'))  # 드롭다운 요소 찾기
        select.select_by_value( str(year) )
        time.sleep(1)
        for page in range(1,3): # 1~2 페이지 반복
            try: 
                if page > 1: # 1페이지는 이미 열려있으니까 클릭 건너뜀
                    btn = driver.find_element(By.ID, f'cphContents_cphContents_cphContents_ucPager_btnNo{page}')  # page 변수로 id 동적 생성
                    btn.click()  # 버튼 클릭
                    time.sleep(1)  # 페이지 로딩 기다리기
            except:
                break
    #==============================================================================================================
            html = driver.page_source # 현재 브라우저에 렌더링 된 HTML 전체 가져옴
            soup = BeautifulSoup(html, 'lxml') # lxml : 빠른 파서
            result = soup.select_one('#cphContents_cphContents_cphContents_udpContent > div.record_result > table > tbody')
            result = result.select('tr')
    #==============================================================================================================
            columns = ['name', 'team', 'era', 'game_cnt', 'win', 'lose', 'save', 'hold',
                        'wpct', 'inning', 'hit', 'home_run', 'bb', 'hbp', 'kk', 'r', 'er', 'whip']
            for row in result:
                tds = row.select('td')
                values = [td.text.strip() for td in tds[1:]]
                data = {'year' : year}
                data.update( dict(zip(columns, values)) )
                datas.append(data)
    driver.quit()
    df_pitcher = pd.DataFrame(datas)
    return df_pitcher
#==========================================================================================================================  


# team.csv crawling
#==========================================================================================================================  
def crawl_team():
    # 드라이버 설정
    service = Service( ChromeDriverManager().install() ) # 크롬 드라이버 자동 설치
    driver = webdriver.Chrome(service=service) # 실제 브라우저 실행
    # 페이지 열기
    driver.get('https://www.koreabaseball.com/Record/TeamRank/TeamRank.aspx')
    datas = []
    for year in [2022, 2023, 2024, 2025, 2026]:
        select = Select(driver.find_element(By.ID, 'cphContents_cphContents_cphContents_ddlYear'))  # 드롭다운 요소 찾기
        select.select_by_value( str(year) )
        time.sleep(1)
    #==============================================================================================================
        html = driver.page_source # 현재 브라우저에 렌더링 된 HTML 전체 가져옴
        soup = BeautifulSoup(html, 'lxml') # lxml : 빠른 파서
        result = soup.select_one('#cphContents_cphContents_cphContents_udpRecord > table > tbody')
        result = result.select('tr')
    #==============================================================================================================
        columns = ['rank', 'team', 'game', 'win', 'lose', 'draw', 'winning_rate', 'games_behind', 'recent10' , 'inarow', 'home', 'away']
        for row in result:
            tds = row.select('td')
            values = [td.text.strip() for td in tds[:]]
            data = {'year' : year}
            data.update( dict(zip(columns, values)) )
            datas.append(data)
    driver.quit()
    df_team = pd.DataFrame(datas)
    return df_team
#==========================================================================================================================  


df_batter_offence = crawl_batter_offence()
df_batter_offence2 = crawl_batter_offence2()
df_batter_defence = crawl_batter_defence()
df_pitcher = crawl_pitcher()
df_team = crawl_team()

df_batter_offence.to_csv('batter_atteck.csv', index = False, encoding='utf-8')
df_batter_offence2.to_csv('data_csv/batter_offence2.csv', encoding='utf-8')
df_batter_defence.to_csv('batter_defence.csv', index = False, encoding='utf-8')
df_pitcher.to_csv('pitcher.csv', index = False, encoding='utf-8')
df_team.to_csv('team.csv', index = False, encoding='utf-8')


df = pd.read_csv('data_csv/batter_offence.csv',encoding='utf-8')
df['year'] = df['year'].astype('category')
df.to_csv('data_csv/batter_offence.csv', index=False)

df = pd.read_csv(r'data_csv\team.csv')
df = df.rename(columns={'rank' : 'ranking'})
df.to_csv('data_csv/team.csv', index=False)













