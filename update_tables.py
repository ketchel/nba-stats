from scraper import pbp_scrape
import schedule
import time

def update_table()

schedule.every().day.at("02:00").do(pbp_scrape,'It is 02:00')

while(True):
    scedule.run_pending()
    time.sleep(6000)