import sqlite3
import pandas as pd
import numpy as np
import csv
import sys
import os
from sklearn.neighbors import KNeighborsClassifier
from sklearn import model_selection
import pickle
from players import select_values, delete_values
from graphs import plot_shot_dist, plot_clutch, plot_consistency
from scraper import scrape


def connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Exception as e:
        print(e)

    return conn

def execute(conn, sql):
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
    except Exception as e:
        print(e)

def fetchall(conn, sql):
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception as e:
        print(e)
        return []
    

"""
COMMANDS
"""    
def quote_illegals(cols):
    """
    This function puts quotes around column names with characters, such as %,  
    that will cause SQL syntax errors without the quotes.
    This could be more efficent, but it doesn't really matter
    seeing as there will never be very many columns.
    """

    illegals =['%', '/']

    for i in range(len(cols)):
        for ill in illegals:
            if ill in cols[i] or any(x.isdigit() for x in cols[i]):
                cols[i] = f" \"{cols[i]}\" "


    
def csv_to_table(conn, table_name, file_name):
    dat_path = "C:\\Users\\ketch\\Desktop\\Projects\\NBA\\data\\" + file_name

    cols = next(csv.reader(open(dat_path)))
    quote_illegals(cols)

    data = pd.read_csv(dat_path)
    data = pd.DataFrame(data, columns = cols)

    data.to_sql(table_name, conn)

def tables(conn):
    execute(conn, '.tables')

def schema(conn):
    execute(conn, '.schema')

def assign_numbers(arr):
    arr[arr == None] = ''
    unique = np.unique(arr)
    
    lookup = dict(zip(unique, range(len(unique))))

    number_list = []
    for item in arr:
        number_list.append(lookup[item])

    return (number_list, lookup)

def get_data(conn, xs, y, table_name):
    xs_list = xs.split(',')
    sql_get_xs = select_values(xs_list, table_name)
    sql_get_y = select_values(y, table_name)
    
    xs_data = pd.read_sql(sql_get_xs, conn)
    y_data = pd.read_sql(sql_get_y, conn)

    return xs_data, y_data


# The following functions produce graphs
def shot_dist(conn, firstname, lastname):
    
    sql_query = 'SELECT ShotDist,ShotOutcome FROM PBP WHERE Shooter LIKE \''+firstname[0]+'. '+lastname+'%\';'

    tbl = pd.read_sql(sql_query,conn)
    dists = tbl.values[:, 0]
    outcomes = tbl.values[:, 1]

    plot_shot_dist(dists, outcomes, firstname, lastname)


def clutch(conn):

    query = """SELECT Shooter,ShotOutcome FROM PBP WHERE 
                (Quarter>=4 AND SecLeft<=120 AND ABS(AwayScore-HomeScore)<=5 AND Shooter IS NOT NULL) ORDER BY Shooter;"""

    data = pd.read_sql(query, conn)    

    plot_clutch(data)


def consistency(conn, stat):

    query = f"SELECT playFNm || ' ' || playLNm AS name,\"play{stat}\" FROM Game ORDER BY name;"

    data = pd.read_sql(query, conn)

    plot_consistency(data)
    

def BR_to_table(conn):
    stats = pd.DataFrame()
    frames = []

    for year in range(1950, 2021):
        url = "https://www.basketball-reference.com/leagues/NBA_"+str(year)+"_per_game.html"
        temp = scrape(url)
        temp['Year'] = year

        frames.append(temp)

    stats = pd.concat(frames)

    #del stats[u"\xa0"] # Use this if there are empty columns on the BR website

    stats.to_sql("PerGame", conn)


COMMANDS = {
    'csv_to_table': {
        'num_args': 2,
        'handler': csv_to_table,
        'usage': "csv_to_table <table_name> <file_name>"
    },
    'create_model':{
        'num_args': 4,
        'handler': create_model,
        'usage': "create_model <model_name> <xs> <y> <table_name>"
    },
    'shot_dist': {
        'num_args': 2,
        'handler': shot_dist,
        'usage': 'shot_dist <firstname> <lastname>'
    },
    'clutch':{
        'num_args': 0,
        'handler': clutch,
        'usage': 'clutch'
    },
    'consistency':{
        'num_args': 1,
        'handler': consistency,
        'usage': 'consistency <stat>'
    },
    'BR_to_table':{
        'num_args': 0,
        'handler': BR_to_table,
        'usage': 'BR_to_table <url>'
    }
}


def main(args):
    nba_db_file = '../db/nba.db'
    conn = connection(nba_db_file)

    if conn is not None:
        command = args[0]

        if command in COMMANDS:
            command_dict = COMMANDS[command]
            num_args, handler, usage = command_dict['num_args'], command_dict['handler'], command_dict['usage']

            if len(args[1:]) != num_args:
                print(usage)
                sys.exit(1)
            else:
                if num_args > 0:
                    result = handler(conn, *args[1:])
                else:
                    result = handler(conn)
        else:
            print("Invalid command")
            sys.exit(1)
    else:
        print("Error creating connection to sqlite.")
    

if __name__ == '__main__':
    main(sys.argv[1:])