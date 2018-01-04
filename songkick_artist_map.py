#!/usr/bin/python3

import datetime as dt
from datetime import datetime
import MySQLdb as mdb
import re
import pandas as pd
import requests
import json
from bs4 import BeautifulSoup

con = mdb.connect(host = 'localhost', 
                  user = 'root',
                  database = 'billboard',
                  passwd = 'dwdstudent2015', 
                  charset='utf8', use_unicode=True);
    
cur = con.cursor(mdb.cursors.DictCursor)
cur.execute("SELECT * FROM Top100")
rows = cur.fetchall()
cur.close()
    
top100 = pd.DataFrame(list(rows)) # first convert 'rows' dictionary into dataframe to clean data more easily
top100['week_of']=pd.to_datetime(top100['week_of'])
top100['artist']=top100['featured_artists'].fillna(top100['single_artist']) # combine two sets of artist data
    
elements=list(top100['artist'])
items=[str(element).replace("\n", "") for element in elements]
regex = re.compile('^.*\>(.*)\<.*$', re.DOTALL)
top100['artist']=[m.group(1) for l in items for m in [regex.search(l)] if m] 
top100['artist']=top100.artist.str.replace("amp;", "") # clean artist data to get just artist name
top100=top100.drop(['featured_artists'], axis=1).drop(['single_artist'], axis=1)
    
ordered=top100.sort_values(['week_of', 'current_rank'], ascending=[False, True], axis=0) # order by date and current rank
ordered=ordered[:99].drop(['last_week_rank'], axis=1)
ordered=ordered[['current_rank', 'song_title', 'artist', 'week_of']]
for week in ordered['week_of']:
    ordered['week_of']=datetime.strftime(week, '%m/%d/%Y')
orderdict=ordered.to_dict(orient='records')
topartists=[artist['artist'] for artist in orderdict]

results=[]
for artist in topartists:
    # Split based on & and ,
    separated =re.split(r'([\w\-\$\.!\* ]+)', artist)
    
    # We are still going to have a few pairs, joined by "Featuring"
    for a in separated:
        if "Featuring" in a:
            regex=re.compile(r'([\w\-\$&,\.!\* ]+)(?: Featuring )([\w\-\$&,\.!\* ]+)')
            matches=regex.finditer(a)
            for match in matches:
                results.append(match.group(1))
                results.append(match.group(2))
        else:
            results.append(a)
 
    
newartists=sorted(set([r.strip() for r in results if ',' not in r and '&' not in r]))

def get_artist_pair(artistname):
    '''
    Returns the ID of the top matching artist
    WARNING: Need to check if no results come back.
    '''
    url = "http://api.songkick.com/api/3.0/search/artists.json"
    params = {
        "apikey": "dNQoOibx7TGUf7tU",
        "query": '{'+artistname+'}'
    }
    resp=requests.get(url, params = params)
    data = resp.json()

    if data['resultsPage']['totalEntries']>0:
        return {data['resultsPage']['results']['artist'][0]['id']:artistname}
    else:
        return None
    
pairs=[get_artist_pair(artistname) for artistname in newartists]
pairs = list(filter(None, pairs))

name_id = {}
for i in pairs:
    name_id.update(i)
    
ids = list(name_id.keys())

def get_artist_info(i):
    '''
    Returns the ID of the top matching artist
    WARNING: Need to check if no results come back.
    '''
    url = "http://api.songkick.com/api/3.0/artists/"+str(i)+"/calendar.json"
    params = {
        "apikey": "dNQoOibx7TGUf7tU"
    }
    resp=requests.get(url, params = params)
    data = resp.json()
    if data['resultsPage']['status']=='ok':
        return {i:data['resultsPage']['results']}
    else:
        return None

info=[get_artist_info(i) for i in ids]
id_events = {}
for i in info:
    id_events.update(i)

alpha={}
for i in id_events.keys():
    if id_events[i] != alpha:
        print (id_events[i]['event'][0]['venue']['displayName'])
        print (str(i))
        print (name_id[i])
        print ('==============')
    
artistid = []
artistname = []
venue = []
eventname = []
city = []
lat = []
long = []
date = []
url = []
identifier = []

empty={}
for i in id_events.keys():
    if id_events[i] != empty:
        artistid.append(str(i))
        artistname.append(name_id[i])
        venue.append(id_events[i]['event'][0]['venue']['displayName'])
        eventname.append(id_events[i]['event'][0]['displayName'])
        city.append(id_events[i]['event'][0]['location']['city'])
        lat.append(id_events[i]['event'][0]['location']['lat'])
        long.append(id_events[i]['event'][0]['location']['lng'])
        date.append(id_events[i]['event'][0]['start']['date'])
        url.append(id_events[i]['event'][0]['uri'])
        identifier.append(id_events[i]['event'][0]['id']) 
        #artistname=i['event']['performance'][0]['artist']['displayName']

eventinfo = pd.DataFrame(
    {'date': date,
     'venue': venue,
     'event': eventname,
     'city': city,
     'lat':lat,
     'lon': long,
     'date': date,
     'url': url,
     'id': identifier,
     'artist': artistname,
     'artistid':artistid
    })


url = "https://www.billboard.com/charts/artist-100"
page = requests.get(url)
bs = BeautifulSoup(page.text, 'html.parser')
topartists = bs.findAll('div','chart-row__main-display')
data=[]
for a in topartists:
    artists1=a.find('a', 'chart-row__artist')
    moreartists=a.find('span', 'chart-row__artist')
    rank=a.find('span', 'chart-row__current-week').contents[0]
    data.append({'artists1': artists1,
                 'moreartists': moreartists,
                 'rank':rank},)
artistranks=pd.DataFrame(data)

artistranks['artist']=artistranks['artists1'].fillna(artistranks['moreartists']) 
elements=list(artistranks['artist'])
items=[str(element).replace("\n", "") for element in elements]
regex = re.compile('^.*\>(.*)\<.*$', re.DOTALL)
artistranks['artist']=[m.group(1) for l in items for m in [regex.search(l)] if m]
artistranks=artistranks.drop(['artists1', 'moreartists'], axis=1)
total=pd.merge(artistranks, eventinfo, on='artist', how='right').fillna(0)
total['rank']=[int(rank) for rank in total['rank']]

import folium
fmap = folium.Map(location=[15, 10], zoom_start=2,  tiles='cartodbpositron')
for name, row in total.iterrows():
    
    color = 'red' if row['rank']in range(1,26) else 'blue' # if the artist in question is ranked 10 or above, mark as red
    
    html = "<p style='font-family:sans-serif;font-size:11px'>" + \
           "<strong>Artist: </strong>" + row["artist"] + \
           "<br><strong>City: </strong>" + row["city"] + \
            "<br><strong>Date: </strong>" +str(row["date"]) +\
            "<br><a href="+row['url'] +" target=\"_blank\">Event URL</a>"
    iframe = folium.IFrame(html=html, width=200, height=100)
    popup = folium.Popup(iframe, max_width=200)

    # create markers and popups on the map
    folium.CircleMarker(location=[row["lat"], row["lon"]], 
                        radius = 5,
                        popup=popup,
                        fill=True,
                        fill_color=color,
                        fill_opacity=0.7).add_to(fmap)
    
fmap.save('templates/map.html')