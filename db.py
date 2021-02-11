import sqlite3
import pandas as pd
import csv
import sys
import pickle
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
    

"""
COMMANDS
"""    
    
def csv_to_table(conn, table_name, file_name):
    """
    This function takes a .csv file and creates a SQL table with the data.
    """

    dat_path = "C:\\Users\\ketch\\Desktop\\Projects\\NBA\\data\\" + file_name # Make sure the file path is correct

    cols = next(csv.reader(open(dat_path)))
    quote_illegals(cols)

    data = pd.read_csv(dat_path)
    data = pd.DataFrame(data, columns = cols)

    data.to_sql(table_name, conn)

def tables(conn):
    execute(conn, '.tables')

def schema(conn):
    execute(conn, '.schema')

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


# The following functions produce graphs
def shot_dist(conn, firstname, lastname):
    """
    Plots the shot distance vs field goals, with seperate bars for made and missed field goals
    """
    
    sql_query = 'SELECT ShotDist,ShotOutcome FROM PBP WHERE Shooter LIKE \''+firstname[0]+'. '+lastname+'%\';'

    tbl = pd.read_sql(sql_query,conn)
    dists = tbl.values[:, 0]
    outcomes = tbl.values[:, 1]

    plot_shot_dist(dists, outcomes, firstname, lastname)


def clutch(conn):
    """
    Plots points vs. FG% in clutch time (<=2 minutes left and point discrepency of <=5)
    """

    query = """SELECT Shooter,ShotOutcome FROM PBP WHERE 
                (Quarter>=4 AND SecLeft<=120 AND ABS(AwayScore-HomeScore)<=5 AND Shooter IS NOT NULL) ORDER BY Shooter;"""

    data = pd.read_sql(query, conn)    

    plot_clutch(data)


def consistency(conn, stat):
    """
    Plots the consistency of players
    """

    query = f"SELECT playFNm || ' ' || playLNm AS name,\"play{stat}\" FROM Game ORDER BY name;"

    data = pd.read_sql(query, conn)

    plot_consistency(data)
    

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