#!/usr/bin/python3

from bs4 import BeautifulSoup
import requests
from lxml import html 
import pandas as pd
import MySQLdb as mdb
import re
import datetime as dt
from datetime import datetime

url = "http://www.billboard.com/charts/hot-100"
page = requests.get(url)
bs = BeautifulSoup(page.text, 'html.parser')
doc = html.fromstring(page.text) # parse it and create a document

# parse through results and get list of dictionary data to insert in SQL
songs = bs.findAll('div','chart-row__main-display')
data=[]
for song in songs:
    title = song.find('h2','chart-row__song').contents[0]
    dates=doc.xpath('//time')
    for date in dates:
        newdate1=str(date.text)
        newdate2=pd.to_datetime(newdate1).date()
        today=datetime.strftime(newdate2, '%m/%d/%Y')
    rank = song.find('span', 'chart-row__current-week').contents[0]
    if int(rank) > 10: #Only collect the top 10
        break
    image = song.find('div','chart-row__image')
    text = str(image)
    if text == '<div class="chart-row__image">\n</div>': #For those without an image
        text = 'https://populous.com/wp-content/uploads/2012/02/anonymous-icon.jpg' #assign anon image
    regex = re.compile(r'htt.*jpg')
    matches = regex.finditer(text)
    for match in matches:
        image_url=match.group()
    data.append({'Title': title,
                 'Image':image_url, 'Rank': rank, 'Week':today},)
    
con = mdb.connect(host = 'localhost', 
                  user = 'root', 
                  passwd = 'dwdstudent2015', 
                  charset='utf8', use_unicode=True);
db_name = 'billboard'

#CREATING THE TABLE IN SQL
cursor = con.cursor()
table_name = 'ranked_top10_images'
create_table_query = '''CREATE TABLE IF NOT EXISTS {db}.{table}
                        (song_title varchar (250), 
                        image varchar(250),
                        rank varchar(250),
                        week varchar(250),
                        PRIMARY KEY(song_title, rank, week))'''.format(db=db_name, table=table_name)
cursor.execute(create_table_query)
cursor.close()

#INSERTING DATA INTO THE TABLE
table_name = 'ranked_top10_images'
query_template = '''INSERT IGNORE INTO {db}.{table}(song_title, 
                                            image, rank, week) 
                    VALUES (%s, %s, %s, %s)'''.format(db=db_name, table=table_name)
cursor = con.cursor()

for entry in data:
    song_title=entry['Title']
    image=entry['Image']
    rank=entry['Rank']
    week=entry['Week']
    print('#', rank, song_title, ':', image, week) #To show us what we are inserting
    query_parameters = (song_title, image, rank, week)
    cursor.execute(query_template, query_parameters)

con.commit()
cursor.close()


