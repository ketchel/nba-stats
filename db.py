import sqlite3
import pandas as pd
import csv
import sys
from datetime import date, timedelta
from scraper import scrape, pbp_scrape


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

    data = pd.read_csv(dat_path)
    data = pd.DataFrame(data, columns = cols)

    data.to_sql(table_name, conn)


def BR_to_table(conn, table_name):
    """
    This function will create a table from the data in the link provided
    for all years entered in the range.
    This only needs to be run once for each page.
    The years in the range and the link should be edited for each page. e.g. per36 stats or per game stats etc.
    """
    stats = pd.DataFrame()
    frames = []

    for year in range(1956, 2021):
        url = "https://www.basketball-reference.com/leagues/NBA_"+str(year)+"_per_poss.html" # Put your own link in here
 
        temp = scrape(url)
        temp.insert(0, "Season", str(year)[2:] +"-" + str(year+1)[2:])

        frames.append(temp)

    stats = pd.concat(frames)

    # These lines will delete any empty columns
    blanks = ["\xa0", "", " "]
    for blank in blanks:
        if blank in data.columns:
            del data[blank]

    stats.to_sql(table_name, conn)

def pbp_to_table(conn):

    tbl = pd.DataFrame()

    # Put your own years in here
    # I reccommend not doing more than a few years at a time as it will take a while to run
    for year in range(2021, 2022):
        for month in [10,11,12,1,2,3,4,5,6]:
            for day in range(1,32):

                tbl = tbl.append(pbp_scrape(str(day), str(month), str(year)))
        print(str(year) + " done")

    tbl.to_sql("PBP", conn, if_exists = "append", index = False)


def update_tables(conn):
    # Just run this function and all your tables will be updates,
    # assuming they are entered in the lists pages and tables correctly.

    # Get the date today
    today = date.today().strftime("%d/%m/%Y")

    today = today.split("/")

    # This will change the format of single digit numbers e.g. '09' to '9' 
    # Double digits will be unaffected
    today[0] = str(int(today[0]))
    today[1] = str(int(today[1]))

    d, m, yr = today[0], today[1], today[2]

    if int(m) <= 12 and int(m) > 9:
        season = yr[2:] + "-" + str(int(yr)+1)[2:]
    else:
        season = str(int(yr)-1)[2:] +"-" + str(yr)[2:]

    # Need to match the stat description in the url to the table name by index
    # e.g. the url with 'totals' must have the same index as the table Totals
    # A dictionary could be used here as well if you prefer

    pages = ["totals", "per_game", "per_minute", "per_poss", "advanced"]
    tables = ["Totals", "PerGame", "Per36", "Per100", "Advanced"]

    for i in range(len(pages)):
        # Go through each table and update it

        url = "https://www.basketball-reference.com/leagues/NBA_" + str(yr) + "_" + pages[i] + ".html"

        data = scrape(url)
        data.insert(0, "Season", season)

        # These lines will delete any empty columns
        blanks = ['\xa0', '', ' ']
        for blank in blanks:
            if blank in data.columns:
                del data[blank]

        # Remove all the out of date data from the table
        query = "DELETE FROM " + tables[i] + " WHERE Season = \"" + season + "\" ;"

        execute(conn, query)

        # Finally, append the new data
        data.to_sql(tables[i], conn, if_exists = "append")
    
    # Now all that's left is to update the play-by-play table
    # Get the date of the last update

    query = "SELECT day,month,season FROM PBP WHERE rowid=(SELECT MAX(rowid) FROM PBP);"

    last_date = pd.read_sql(query,conn).values.tolist()[0]
    last_d, last_m, last_ssn = last_date[0],last_date[1],last_date[2]

    if int(last_m) <= 12 and int(last_m) > 9:
        last_yr = last_ssn[:2]
    else:
        last_yr = str(last_ssn)[3:]

    if int(last_yr)>95:
        last_yr = "19"+last_yr
    else:
        last_yr = "20"+last_yr

    # Start date is that of the last update, end date is today
    sdate = date(int(last_yr), int(last_m), int(last_d))
    edate = date(int(yr), int(m), int(d))

    delta = edate-sdate

    for i in range(delta.days+1):
        day = str(sdate + timedelta(days=i)).split("-")

        plays = pbp_scrape(str(int(day[2])), str(int(day[1])), day[0])

        plays.to_sql("PBP", conn, if_exists = "append", index = False)    

COMMANDS = {
    'csv_to_table': {
        'num_args': 2,
        'handler': csv_to_table,
        'usage': "csv_to_table <table_name> <file_name>"
    },
    'BR_to_table':{
        'num_args': 1,
        'handler': BR_to_table,
        'usage': 'BR_to_table <table_name>'
    },
    'pbp_to_table':{
        'num_args': 0,
        'handler': pbp_to_table,
        'usage': 'pbp_to_table'
    },
    'update_tables':{
        'num_args': 0,
        'handler': update_tables,
        'usage': 'update_tables'
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