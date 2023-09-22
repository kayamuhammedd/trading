import pymongo
from future.types import newint

class DBHelper:
    def __init__(self, dbname="TradingBot"):
        self.dbname = dbname
        self.conn = pymongo.MongoClient("mongodb://localhost:27017")
        self.db = self.conn['TradingBot']

    def instance(self):
        return self.db

    def get_conn(self):
        return self.conn

    def setup(self):
        stmt = "CREATE TABLE IF NOT EXISTS Users (description text)"
        self.conn.execute(stmt)
        self.conn.commit()

    def insert_user(self, user_dict):
        self.db["Users"].create_index([('Email', pymongo.ASCENDING)], unique=True)
        try:
            self.db["Users"].insert_one(user_dict)
            return False
        except pymongo.errors.DuplicateKeyError as e:
            print("The user exist")
            print(e)
            return True

    def get_user(self, email, password):
        myquery = {"email": email, "password": password}
        mydoc = self.db["Users"].find(myquery)

        for x in mydoc:
            if x['email'] == email and x["password"] == password:
                print(x)
                return list(x)


    def get_active_trades(self, email):
        myquery = {"Email": email, "IsDealActive": True}
        mydoc = self.db["Trades"].find(myquery)
        tradesList = []
        trades = dict()
        for x in mydoc:
            if x['Email'] == email and x['IsDealActive']:
                lastBuyPrice = x["LastBuyPrice"]
                print(lastBuyPrice)
                averageBuy = sum(lastBuyPrice) / float(len(lastBuyPrice))
                print(averageBuy)
                trades = {"Email": x["Email"], "Symbol": x["Symbol"], "EntryPrice": x["EntryPrice"], "SafetyOrderCount": x["SafetyOrderCount"],
                          "UsedSafetyOrderCount": x["UsedSafetyOrderCount"], "SafetyOrderVolume": x["SafetyOrderVolume"],
                          "IsDealActive":x["IsDealActive"], "LastBuyPrice":x["LastBuyPrice"], "AverageBuyPrice":averageBuy}
                tradesList.append(trades)

        return tradesList

    def add_trade(self, email, symbol, price: float, isDealActive: bool, safetyOrderCount:int, usedSafetyOrderCount:int, quantity:int, safetyOrderVolume:int):
        self.db["Trades"].create_index([('Email', pymongo.ASCENDING)], unique=False)
        try:
            trade = {
                'Email': email,
                'Symbol': symbol,
                'EntryPrice': price,
                'IsDealActive': isDealActive,
                'SafetyOrderCount': safetyOrderCount,
                'UsedSafetyOrderCount': usedSafetyOrderCount,
                'Quantity': quantity,
                'SafetyOrderVolume': safetyOrderVolume,
                'LastBuyPrice': [price]
            }
            self.db["Trades"].insert_one(trade)
        except pymongo.errors.DuplicateKeyError as e:
            print("The trade exist")
            print(e)
            return True


    def update_trade(self, email, symbol, binancePrice):
        myquery = {"Email": email, "Symbol": symbol, "IsDealActive": True}
        mydoc = self.db["Trades"].find(myquery)
        for x in mydoc:
            myquery = {"Email": email, "Symbol": symbol}
            buyPrices = x["LastBuyPrice"]
            buyPrices.append(binancePrice)
            newvalues = {
                "$set": {"LastBuyPrice": buyPrices, "UsedSafetyOrderCount": x["UsedSafetyOrderCount"] + 1}}
            self.db["Trades"].update_one(myquery, newvalues)

    def insert_user_to_group(self, chat_id, telegram_id):
        myquery = {"ChatID": chat_id}
        mydoc = self.db["Groups"].find(myquery)
        for x in mydoc:
            if x['ChatID'] == chat_id:
                myquery2 = {"TelegramID": telegram_id}
                mydoc2 = self.db["Users"].find(myquery2)
                for i in mydoc2:
                    if i['TelegramID'] == telegram_id and i["isVerified"]:
                        try:
                            myquery3 = {"ChatID": chat_id}
                            newvalues = {"$push": {"Users":{"ID":telegram_id, "NumberofKicks": 0, "is_kicked": False}}}
                            users = x['Users']
                            for user in users:
                                check_id = user['ID']
                                if len(users) > 1:
                                    print(user['is_kicked'])
                                    if (int(check_id) != int(telegram_id) or user['is_kicked']) and check_id != 0:
                                        self.db["Groups"].update_one(myquery3, newvalues)
                                        return True
                                elif 0 <= len(users) or len(users) == 1:
                                    self.db["Groups"].update_one(myquery3, newvalues)
                                    return True
                        except Exception as e:
                            print(e)
                    else:
                        return False

    def is_already_on_db(self, chat_id, telegram_id):
        myquery = {"ChatID": chat_id}
        mydoc = self.db["Groups"].find(myquery)
        for x in mydoc:
            if x['ChatID'] == chat_id:
                users_db = x['Users']
                for user in users_db:
                    if user['ID'] == telegram_id:
                        return True
                return False

    def insert_group(self, group_dict):
        self.db["Groups"].create_index([('ChatID', pymongo.ASCENDING)], unique=True)
        try:
            self.db["Groups"].insert_one(group_dict)
        except pymongo.errors.DuplicateKeyError as e:
            print("The group exist")
            print(e)
            return False


    def update_user_after_verified(self, wallet_address, telegramID, balance):

        myquery = {"TelegramID": telegramID}
        newvalues = {"$set": {"wallet_address": wallet_address, "isVerified": True, "addressChange": False, "Balance": balance}}
        self.db["Users"].update_one(myquery, newvalues)


    def get_token_from_db(self, telegramID):
        myquery = {"TelegramID": telegramID}
        mydoc = self.db["Users"].find(myquery)
        for x in mydoc:
            if x['TelegramID'] == telegramID:
                print(x['Token'])
                token = x['Token']
        return token

    def get_users_telegram_id(self):
        users = []
        mydoc = self.db["Users"].find()
        for x in mydoc:
            users.append(x['TelegramID'])
        return users

    def get_users_wallet_address(self):
        users = []
        mydoc = self.db["Users"].find()
        for x in mydoc:
            if x['isVerified']:
                users.append(x['wallet_address'])
        return users

    def get_user_wallet_address(self, chat_id):
        myquery = {"TelegramID": chat_id}
        mydoc = self.db["Users"].find(myquery)
        for x in mydoc:
            wallet_address = x['wallet_address']
        return wallet_address

    def get_users_wallet_address_from_group_id(self, chat_id):
        myquery = {"ChatID": chat_id}
        mydoc = self.db["Groups"].find(myquery)
        users_id = []
        users = []
        for x in mydoc:
            if x['ChatID'] == chat_id:
                users_db = x['Users']
                for user in users_db:
                    print("DB is kicked= ", user['is_kicked'])
                    if user['ID'] != 0 and not user['is_kicked']:
                        users_id.append(user['ID'])
                        users.append(self.get_user_wallet_address(user['ID']))
        return users_id, users

    def update_user_after_kicked_from_group(self, chat_id, id):

        myquery = {"ChatID": chat_id}
        mydoc = self.db["Groups"].find(myquery)
        for x in mydoc:
            if x['ChatID'] == chat_id:
                try:
                    users = x['Users']
                    for user in users:
                        if(user['ID']==id):
                            numberOfKick = user['NumberofKicks']
                    if numberOfKick < 3:
                        newvalues = {"$set": {"Users.$[id].NumberofKicks": numberOfKick+1, "Users.$[id].is_kicked": True}}
                        self.db["Groups"].update_one(myquery, newvalues, array_filters=[{"id.ID": id}])
                        return True,numberOfKick
                    else:
                        return False, numberOfKick
                except Exception as e:
                    print(e)
                    return False, numberOfKick


    def update_group_user_adding(self, chat_id, telegram_id):
        myquery = {"ChatID": chat_id}
        mydoc = self.db["Groups"].find(myquery)
        for x in mydoc:
            if x['ChatID'] == chat_id:
                try:
                    users = x['Users']
                    for user in users:
                        if(user['ID']==telegram_id):
                            numberOfKick = user['NumberofKicks']
                    if(numberOfKick < 3):
                        newvalues = {"$set": {"Users.$[id].is_kicked": False}}
                        self.db["Groups"].update_one(myquery, newvalues, array_filters=[{"id.ID": telegram_id}])
                        return True
                    else:
                        return False
                except Exception as e:
                    print(e)
                    return False


    def get_group_balance(self, chat_id):
        myquery = {"ChatID": chat_id}
        mydoc = self.db["Groups"].find(myquery)
        for x in mydoc:
            if x['ChatID'] == chat_id:
                print(x['Balance'])
                balance = x['Balance']
        return balance

    def get_user_token_balance(self, wallet_address):
        myquery = {"wallet_address": wallet_address}
        mydoc = self.db["Users"].find(myquery)
        for x in mydoc:
            if x['wallet_address'] == wallet_address:
                print(x['Balance'])
                return x['Balance']

    def update_user_balance(self, wallet_address, balance):
        myquery = {"wallet_address": wallet_address}
        newvalues = { "$set": {"Balance": balance}}
        self.db["Users"].update_one(myquery, newvalues)

    def set_group_balance(self, chat_id, amount):
        myquery = {"ChatID": chat_id}
        newvalues = {"$set": {"Balance": amount, "isSetCheckBalance": True}}
        self.db["Groups"].update_one(myquery, newvalues)

    def get_isSet(self):
        mydoc = self.db["Groups"].find()
        isSet = []
        for x in mydoc:
            if x['isSetCheckBalance']:
                isSet.append(x)
                print(x)
        return isSet


    '''
            ************TWITTER************
    '''


    def insert_twitter_user(self, user_dict):
        self.db["Twitter_Users"].create_index([('Twitter_ID', pymongo.ASCENDING)], unique=True)
        try:
            self.db["Twitter_Users"].insert_one(user_dict)
            return False
        except pymongo.errors.DuplicateKeyError as e:
            print("The user exist")
            print(e)
            return True

    def insert_twitter_user_link(self, user_dict):
        self.db["Twitter_Links"].create_index([('Twitter_ID', pymongo.ASCENDING)], unique=True)
        try:
            self.db["Twitter_Links"].insert_one(user_dict)
            return False
        except pymongo.errors.DuplicateKeyError as e:
            print("The user exist")
            print(e)
            return True


    def mon_start_db(self, mon_dict):
        self.db["Twitter_Mon"].create_index([('Tweet_ID', pymongo.ASCENDING)], unique=True)
        self.db["Twitter_Mon"].insert_one(mon_dict)

    def add_rewarded_user(self, tweet_id, user_id):
        myquery = {"Tweet_ID": tweet_id}
        mydoc = self.db["Twitter_Mon"].find(myquery)
        for x in mydoc:
            total = int(x['Rewarded_Users_Count'])
            max = int(x['maxUsers'])
        if total < max:
            total = total + 1
            myquery = {"Tweet_ID": tweet_id}
            newvalues = {"$push": {"Users": user_id }, "$set":{"Rewarded_Users_Count": total}}
            self.db["Twitter_Mon"].update_one(myquery, newvalues)

    def update_mon_after_sent_reward(self, tweet_id, user_id, txhash, is_list):
        myquery = {"Tweet_ID": tweet_id}
        mydoc = self.db["Twitter_Mon"].find(myquery)
        total = 0
        rewarded = 0
        for x in mydoc:
            total = int(x['Sent_Users_Count'])
            rewarded = int(x['Rewarded_Users_Count'])
        if is_list:
            newvalues = {"$pull": {"Users": user_id}, "$push": {"Sent_Users": user_id, "txHashes": txhash},
                         "$set": {"Rewarded_Users_Count": rewarded - len(user_id),
                                  "Sent_Users_Count": total + len(user_id)}}
            self.db["Twitter_Mon"].update_one(myquery, newvalues)
        else:
            newvalues = {"$pull": {"Users": user_id}, "$push": {"Sent_Users": user_id, "txHashes": txhash},
                         "$set": {"Rewarded_Users_Count": rewarded - 1,
                                  "Sent_Users_Count": total + 1}}
            self.db["Twitter_Mon"].update_one(myquery, newvalues)

    def update_mon_after_finished(self, tweet_id):
        myquery = {"Tweet_ID": tweet_id}
        newvalues = {"$set":{"isTimedOut": True}}
        self.db["Twitter_Mon"].update_one(myquery, newvalues)

    def get_rewarded_users(self, tweet_id):
        myquery = {"Tweet_ID": tweet_id}
        mydoc = self.db["Twitter_Mon"].find(myquery)
        for x in mydoc:
            if tweet_id == x['Tweet_ID']:
                return x['Users']

    def get_twitter_mon_datas(self, tweet_id, data):
        myquery = {"Tweet_ID": tweet_id}
        mydoc = self.db["Twitter_Mon"].find(myquery)
        for x in mydoc:
            data = x[data]
        return data

    def set_link_isVerified(self, twitter_id):
        myquery = {"Twitter_ID": twitter_id}
        newvalues = {
            "$set": {"isVerified": True, "invalid_id": twitter_id, "Twitter_ID": None}}
        self.db["Twitter_Links"].update_one(myquery, newvalues)

    def get_telegram_link_token(self, user_telegram_id):
        myquery = {"Telegram_Id": user_telegram_id}
        mydoc = self.db["twitter_links"].find(myquery)
        for x in mydoc:
            token = x["token"]
        return token

    def get_user_wallet_private_twitter(self, twitter_id):
        myquery = {"Twitter_ID": twitter_id}
        mydoc = self.db["Twitter_Users"].find(myquery)
        for x in mydoc:
            wallet_address = x['wallet_private_key']
        return wallet_address

    def get_user_wallet_address_twitter(self, twitter_id):
        myquery = {"Twitter_ID": twitter_id}
        mydoc = self.db["Twitter_Users"].find(myquery)
        for x in mydoc:
            wallet_address = x['wallet_address']
        return wallet_address

    def get_user_twitter(self,twitter_ID):
        myquery = {"Twitter_ID": twitter_ID}
        mydoc = self.db["Twitter_Users"].find(myquery)
        for x in mydoc:
            if x['Twitter_ID'] == twitter_ID:
                print(x)
                return x
            else:
                return None
