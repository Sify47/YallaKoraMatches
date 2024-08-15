import psycopg2
import psycopg2.extras
from sqlalchemy import create_engine
import requests
import pandas as pd
from bs4 import BeautifulSoup
from tabulate import tabulate
import streamlit as st

connect_sql = psycopg2.connect(host = "localhost" , dbname = "postgres" , port= 5432 , user = "postgres", password = "01141117352")
cur = connect_sql.cursor(cursor_factory=psycopg2.extras.DictCursor)
conn_eng = create_engine("postgresql://postgres:01141117352@localhost:5432/postgres")
con = conn_eng.connect()

def commit():
    connect_sql.commit()
def close():
    connect_sql.close()

# res = requests.get(f"https://www.yallakora.com/match-center?date=8/14/2024")
res = requests.get(f"https://www.yallakora.com/match-center")
src = res.content
soup = BeautifulSoup(src , "lxml")

chamption = soup.find_all("div" , {"class" : "matchCard"})
mat = []

def get(chamption) : 
    chamption_title = chamption.contents[1].find("h2").text.strip()
    all = chamption.contents[3].find_all("div" , {"class":"item"})
    num = len(all)
    for i in range(num):
        asb = all[i].find("div" , {"class":"date"}).text.strip()
        state = all[i].find("span").text.strip()
        resl = all[i].find("div" , {"class" : "MResult"}).find_all("span" , {"class" : "score"})
        reslt = f"{resl[0].text.strip()} - {resl[1].text.strip()}"
        clock = all[i].find("div" , {"class" : "MResult"}).find("span" , {"class" : "time"}).text.strip()
        teamA = all[i].find("div" , {"class":"teamA"}).text.strip()
        teamB = all[i].find("div" , {"class":"teamB"}).text.strip()
        mat.append({"اسم البطوله":chamption_title ,"الفريق الاول": teamA ,"النتيحه" : reslt, "الفريق الثانى": teamB , "التوقيت":clock, "الاسبوع":  asb, "الحاله": state})

for i in range(len(chamption)) :
    get(chamption[i])
    
df = pd.DataFrame(mat)
df.to_sql("matches" , con , if_exists="replace")
cur.execute("SELECT * FROM matches")
x = cur.fetchall()
print(tabulate(x,tablefmt="psql"))

st.write(x)
