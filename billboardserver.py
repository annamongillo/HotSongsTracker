#!/bin/sh

from flask import Flask, render_template
import MySQLdb as mdb
from flask import request
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt, mpld3
import datetime as dt
from datetime import datetime
import re
import io
import base64

app = Flask(__name__)

@app.route("/")
def home():
    con = mdb.connect(host = 'localhost', 
                  user = 'root',
                  database = 'billboard',
                  passwd = 'dwdstudent2015', 
                  charset='utf8', use_unicode=True);
    
    cur = con.cursor(mdb.cursors.DictCursor)
    cur.execute("SELECT * FROM Top100 where current_rank between 1 and 10 order by week_of, current_rank")
    rows = cur.fetchall()
    cur.close()
    
    rows=rows[-10:]
    top10 = pd.DataFrame(list(rows)) # first convert 'rows' dictionary into dataframe to clean data more easily
    top10['week_of']=pd.to_datetime(top10['week_of'])
    top10['artist']=top10['featured_artists'].fillna(top10['single_artist']) # combine two sets of artist data
    
    elements=list(top10['artist'])
    items=[str(element).replace("\n", "") for element in elements]
    regex = re.compile('^.*\>(.*)\<.*$', re.DOTALL)
    top10['artist']=[m.group(1) for l in items for m in [regex.search(l)] if m] 
    top10['artist']=top10.artist.str.replace("amp;", "") # clean artist data to get just artist name
    top10=top10.drop(['featured_artists'], axis=1).drop(['single_artist'], axis=1)
    for week in top10['week_of']:
        top10['week_of']=datetime.strftime(week, '%m/%d/%Y')
    top10dict=top10.to_dict(orient='records') # convert back into dictionary to plot as table
    
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
    ordered=ordered[:100].drop(['last_week_rank'], axis=1)
    ordered=ordered[['current_rank', 'song_title', 'artist', 'week_of']]
    for week in ordered['week_of']:
        ordered['week_of']=datetime.strftime(week, '%m/%d/%Y')
    orderdict=ordered.to_dict(orient='records') # convert back into dictionary to plot as table
    
    cur = con.cursor(mdb.cursors.DictCursor)
    cur.execute("SELECT * FROM ranked_top10_images ORDER BY week DESC, rank ASC")
    rows = cur.fetchall()
    cur.close()
    imagedict=list(rows[:10])
    
    return render_template("index.html", top10dict=top10dict, orderdict=orderdict, imagedict=imagedict)

@app.route("/plot1.html")
def plot1():
    return render_template("plot1.html")

@app.route("/plot2.html")
def plot2():
    return render_template("plot2.html")

@app.route("/plot3.html")
def plot3():
    return render_template("plot3.html")

@app.route("/plot4.html")
def plot4():
    return render_template("plot4.html")

@app.route("/plot5.html")
def plot5():
    return render_template("plot5.html")

@app.route("/plot6.html")
def plot6():
    return render_template("plot6.html")

@app.route("/plot7.html")
def plot7():
    return render_template("plot7.html")

@app.route("/plot8.html")
def plot8():
    return render_template("plot8.html")

@app.route("/plot9.html")
def plot9():
    return render_template("plot9.html")

@app.route("/plot10.html")
def plot10():
    return render_template("plot10.html")

@app.route("/map.html")
def showmap():
    return render_template("map.html")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=2000, debug=True)
    