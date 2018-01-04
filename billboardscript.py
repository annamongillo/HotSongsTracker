#!/usr/bin/python3

from bs4 import BeautifulSoup
import requests
from lxml import html 
import pandas as pd
import datetime as dt
from datetime import datetime
import MySQLdb as mdb
import re
import os
import matplotlib
import matplotlib.pyplot as plt
matplotlib.style.use(['seaborn-talk', 'seaborn-ticks', 'seaborn-whitegrid'])
plt.rcParams['figure.figsize'] = (10, 5)
import mpld3
import numpy as np

# Make the graphs a bit prettier, and bigger


url = "http://www.billboard.com/charts/hot-100"
page = requests.get(url)
bs = BeautifulSoup(page.text, 'html.parser')
doc = html.fromstring(page.text) # parse it and create a document

# parse through results and get list of dictionary data to insert in SQL
songs = bs.findAll('div','chart-row__main-display')
data=[]
for song in songs:
    title = song.find('h2','chart-row__song').contents[0]
    featured = song.find('span','chart-row__artist') # featured artists and single artists have different html formats
    single_artist=song.find('a', 'chart-row__artist')
    rank=song.find('span', 'chart-row__current-week').contents[0]
    lastweek=song.find('span', 'chart-row__last-week').contents[0].replace('Last Week:', "")
    dates=doc.xpath('//time')
    for date in dates:
        newdate1=str(date.text)
        newdate2=pd.to_datetime(newdate1).date()
        today=datetime.strftime(newdate2, '%m/%d/%Y')
    data.append({'Title': title,
                 'Last Week Rank': lastweek,
                 'Featured Artists': featured,
                 'Single Artist': single_artist,
                 'Current Rank': rank, 'Week of': today,},)
    
# create a database
con = mdb.connect(host = 'localhost', 
                  user = 'root', 
                  passwd = 'dwdstudent2015', 
                  charset='utf8', use_unicode=True);
db_name = 'billboard'
create_db_query = "CREATE DATABASE IF NOT EXISTS {db} DEFAULT CHARACTER SET 'utf8'".format(db=db_name)
cursor = con.cursor()
cursor.execute(create_db_query)
cursor.close()

# create a table
cursor = con.cursor()
table_name = 'Top100'
create_table_query = '''CREATE TABLE IF NOT EXISTS {db}.{table}
                        (current_rank int,
                        last_week_rank varchar(250), 
                        featured_artists varchar(250),
                        single_artist varchar(250),
                        song_title varchar (250), 
                        week_of varchar(250),
                        PRIMARY KEY(song_title, current_rank, week_of))'''.format(db=db_name, table=table_name)
cursor.execute(create_table_query)
cursor.close()

# add the data
table_name = 'Top100'
query_template = '''INSERT IGNORE INTO {db}.{table}(current_rank, 
                                            last_week_rank,
                                            featured_artists,
                                            single_artist,
                                            song_title,
                                            week_of) 
                    VALUES (%s, %s, %s, %s, %s, %s)'''.format(db=db_name, table=table_name)
cursor = con.cursor()

for entry in data:
    current_rank = entry['Current Rank']
    last_week_rank = entry['Last Week Rank']
    featured_artists=entry['Featured Artists']
    single_artist=entry['Single Artist']
    song_title=entry['Title']
    week_of=entry['Week of']
    print("Inserting headline", title)
    query_parameters = (current_rank, last_week_rank, featured_artists, single_artist, song_title, week_of)
    cursor.execute(query_template, query_parameters)

con.commit()
cursor.close()

cur = con.cursor(mdb.cursors.DictCursor)
cur.execute("SELECT * FROM {db}.{table}".format(db=db_name, table=table_name))
rows = cur.fetchall()
cur.close()

top100 = pd.DataFrame(list(rows))
top100['week_of']=pd.to_datetime(top100['week_of']) # convert week to datetime format
    
# combine featured and single artist columns and clean dataframe
top100['artist']=top100['featured_artists'].fillna(top100['single_artist']) 
elements=list(top100['artist'])
items=[str(element).replace("\n", "") for element in elements]
regex = re.compile('^.*\>(.*)\<.*$', re.DOTALL)
top100['artist']=[m.group(1) for l in items for m in [regex.search(l)] if m] 
top100['artist']=top100.artist.str.replace("amp;", "")
top100=top100.drop(['featured_artists'], axis=1).drop(['single_artist'], axis=1)

top100['last_week_rank']=["NaN" if x==' --' or x=='0' else x for x in top100['last_week_rank']]
top100['last_week_rank']=[int(x)if x!='NaN' else x for x in top100['last_week_rank']]

ordered=top100.sort_values(['week_of', 'current_rank'], ascending=[False, True], axis=0)
ordered.columns=['Current Rank', 'Last Week Rank', 'Song Title', 'Week','Artist']
top10plot=ordered[:10].drop(['Artist'], axis=1).drop(['Week'], axis=1)

top10songs=[element for element in top10plot['Song Title']] #list of current top 10 songs
songs=top100.set_index('song_title').drop(['artist'], axis=1)
allsongs=[songs.loc[song] for song in top10songs] # locate top 10 songs in Top 100 df

#save top 10 plots
ax1=allsongs[0].reset_index().set_index('week_of').resample('W').sum().plot(marker="o", color='blue')
ax1.set_title('#1 '+allsongs[0].reset_index()['song_title'][0])
ax1.set_xlabel('Week')
ax1.set_ylabel('Hot 100 Ranking')
ax1.invert_yaxis()
ax1.legend(['rank'])
fig = ax1.get_figure()
mpld3.save_html(fig, "templates/plot1.html")

ax2=allsongs[1].reset_index().set_index('week_of').resample('W').sum().plot(marker="o", color='blue')
ax2.set_title('#2 '+allsongs[1].reset_index()['song_title'][0])
ax2.set_xlabel('Week')
ax2.set_ylabel('Hot 100 Ranking')
ax2.invert_yaxis()
ax2.legend(['rank'])
fig = ax2.get_figure()
mpld3.save_html(fig, "templates/plot2.html")
                
ax3=allsongs[2].reset_index().set_index('week_of').resample('W').sum().plot(marker="o", color='blue')
ax3.set_title('#3 '+allsongs[2].reset_index()['song_title'][0])
ax3.set_xlabel('Week')
ax3.set_ylabel('Hot 100 Ranking')
ax3.invert_yaxis()
ax3.legend(['rank'])
fig = ax3.get_figure()
mpld3.save_html(fig, "templates/plot3.html")
                
ax4=allsongs[3].reset_index().set_index('week_of').resample('W').sum().plot(marker="o", color='blue')
ax4.set_title('#4 '+allsongs[3].reset_index()['song_title'][0])
ax4.set_xlabel('Week')
ax4.set_ylabel('Hot 100 Ranking')
ax4.invert_yaxis()
ax4.legend(['rank'])
fig = ax4.get_figure()
mpld3.save_html(fig, "templates/plot4.html")
                
ax5=allsongs[4].reset_index().set_index('week_of').resample('W').sum().plot(marker="o", color='blue')
ax5.set_title('#5 '+allsongs[4].reset_index()['song_title'][0])
ax5.set_xlabel('Week')
ax5.set_ylabel('Hot 100 Ranking')
ax5.invert_yaxis()
ax5.legend(['rank'])
fig = ax5.get_figure()
mpld3.save_html(fig, "templates/plot5.html")            
                
ax6=allsongs[5].reset_index().set_index('week_of').resample('W').sum().plot(marker="o", color='blue')
ax6.set_title('#6 '+allsongs[5].reset_index()['song_title'][0])
ax6.set_xlabel('Week')
ax6.set_ylabel('Hot 100 Ranking')
ax6.invert_yaxis()
ax6.legend(['rank'])
fig = ax6.get_figure()
mpld3.save_html(fig, "templates/plot6.html")
                
ax7=allsongs[6].reset_index().set_index('week_of').resample('W').sum().plot(marker="o", color='blue')
ax7.set_title('#7 '+allsongs[6].reset_index()['song_title'][0])
ax7.set_xlabel('Week')
ax7.set_ylabel('Hot 100 Ranking')
ax7.invert_yaxis()
ax7.legend(['rank'])
fig = ax7.get_figure()
mpld3.save_html(fig, "templates/plot7.html")
                
ax8=allsongs[7].reset_index().set_index('week_of').resample('W').sum().plot(marker="o", color='blue')
ax8.set_title('#8 '+allsongs[7].reset_index()['song_title'][0])
ax8.set_xlabel('Week')
ax8.set_ylabel('Hot 100 Ranking')
ax8.invert_yaxis()
ax8.legend(['rank'])
fig = ax8.get_figure()
mpld3.save_html(fig, "templates/plot8.html")
                
ax9=allsongs[8].reset_index().set_index('week_of').resample('W').sum().plot(marker="o", color='blue')
ax9.set_title('#9 '+allsongs[8].reset_index()['song_title'][0])
ax9.set_xlabel('Week')
ax9.set_ylabel('Hot 100 Ranking')
ax9.invert_yaxis()
ax9.legend(['rank'])
fig = ax9.get_figure()
mpld3.save_html(fig, "templates/plot9.html")

ax10=allsongs[9].reset_index().set_index('week_of').resample('W').sum().plot(marker="o", color='blue')
ax10.set_title('#10 '+allsongs[9].reset_index()['song_title'][0])
ax10.set_xlabel('Week')
ax10.set_ylabel('Hot 100 Ranking')
ax10.invert_yaxis()
ax10.legend(['rank'])
fig = ax10.get_figure()
mpld3.save_html(fig, "templates/plot10.html")