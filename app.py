import yfinance as yf
from pymongo import MongoClient
import json
import datetime
from matplotlib import pyplot as plt
import sys
import os


#Step 1: Create a db class that will connect to mongo db and contain the functions
class stock_db():
    def __init__(self) -> None:

        self.id_dict = {}
        self.date_list = []
        self.value_nested_list = [] #reason nested list is in case of future implementation where i show more than one stock graphs
        mongo_user = os.environ.get('mongo_user')
        mongo_pass = os.environ.get('mongo_pass')

        try:
            client = MongoClient(f"mongodb+srv://{mongo_user}:{mongo_pass}@kcluster.9670b.mongodb.net/stock_info?retryWrites=true&w=majority")
        except Exception:
            print("Error:" + Exception)

        self.db = client["stock_info"]
        self.myCollection = self.db["ticker_info"]
        
    def store_id(self, ticker,res):
        self.id_dict[ticker] = res
    
    def insert_one(self,ticker_json,ticker):
        res = self.myCollection.insert_one(json.loads(ticker_json))
        self.store_id(ticker,res.inserted_id)

    
    def dt64_to_date(self,dt64):
        date = datetime.datetime.fromtimestamp(dt64/1e3)
        
        return date

    def vdict_to_list(self, stock_dict):
        tempList = []
        for key in stock_dict:
            tempList.append(stock_dict[key])
        self.value_nested_list.append(tempList)
    
    def date_to_list(self,stock_dict, interval_t):
        for key in stock_dict:
            date = self.dt64_to_date(int(key))
            #valid intervals: 1d,5d,1wk,1mo,3mo
            if interval_t == "1d":
                date = date.year + (date.month / 12) + (date.day / 365)
            elif interval_t == "5d":
                date = date.year + (date.month / 12) + (date.day / 73)
            elif interval_t == "1w":
                date = date.year + (date.month / 12) + (date.day / (365/7))
            elif interval_t == "1mo":
                date = date.year + (date.month / 12)
            elif interval_t == "3mo":
                date = date.year + (date.month / 3)
            else: 
                sys.exit("Invalid interval")
            self.date_list.append(date)

    def show_plot(self,ticker):
        x_axis = self.date_list
        y_axis = self.value_nested_list[0]
        plt.plot(x_axis,y_axis)
        plt.ylabel("Stock Price $USD")
        plt.xlabel("Year")
        plt.title(ticker)
        plt.show()
        
        
if __name__ == "__main__":
    
    
    #Step 2: Get the ticker input and do a call to get the data on that stock
    #Step 3: Store the data into MongoDB for later retrieval 
    
    # ---------------------- Do not need for now as implementation is only for one stock -------------------------
    # ------------------------------ Will adjust later when showing subplots ------------------------------------- 
    # while True:
    #     ticker = input("Enter desired ticker, 'c' to continue, or 'quit': ")
    #     if ticker.lower() == "quit" or ticker.lower() == 'c':
    #         break
    #     else:
    #         ticker_obj = yf.Ticker(ticker)
    #         ticker_json = ticker_obj.history(period="10y",interval="1d").dropna().to_json()
    #         s_db.insert_one(ticker_json,ticker)
    # -------------------------------------------------------------------------------------------------------------
    loop_b = True
    while loop_b:  
        s_db = stock_db()
        ticker = input("Enter desired ticker to begin: ")
        state = input("Open, Close, High, or Low?: ")
        period_t = input("Enter period (valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max): ")
        interval_t = input("Enter interval (valid intervals: 1d,5d,1wk,1mo,3mo): ")
        ticker_obj = yf.Ticker(ticker)
        ticker_json = ticker_obj.history(period=period_t,interval=interval_t).dropna().to_json()
        s_db.insert_one(ticker_json,ticker)

        #Step 4 use the ticker_id dictionary to get data that we wish to see
        #4.5 with id_dict, use keys to index values and values to push into obj_id
        
        for key in s_db.id_dict:
            obj_id = s_db.id_dict[key]
            stock_dict = s_db.myCollection.find_one({"_id": obj_id})[state.capitalize()] #returns a dictionary with nested dictionaries
            s_db.vdict_to_list(stock_dict) 

            if s_db.date_list:
                break
            else:
                s_db.date_to_list(stock_dict, interval_t)
            
        s_db.show_plot(ticker)
        del_col = s_db.myCollection.delete_many({})
        redo = input("Do you wish to see another stock?(y/n): ")
        if redo.lower() == 'n':
            loop_b = False
    print("Have a nice day")
    