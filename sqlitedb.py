import web

db = web.database(dbn='sqlite',
        db='AuctionBase'
    )

######################BEGIN HELPER METHODS######################

# Enforce foreign key constraints
# WARNING: DO NOT REMOVE THIS!
def enforceForeignKey():
    db.query('PRAGMA foreign_keys = ON')

# initiates a transaction on the database
def transaction():
    return db.transaction()

def updateTime(selected_time):
    t = db.transaction()
    try:
        query('update CurrentTime set time = $updated_time', {'updated_time': selected_time}, True)
    except Exception as e:
        t.rollback()
        print str(e)
    else:
        t.commit()

# returns the current time from your database
def getTime():
    # TODO: update the query string to match
    # the correct column and table name in your database
    query_string = 'select time as time from CurrentTime'
    results = query(query_string)
    # alternatively: return results[0]['currenttime']
    return results[0].time # TODO: update this as well to match the
                                  # column name

# returns a single item specified by the Item's ID in the database
# Note: if the `result' list is empty (i.e. there are no items for a
# a given ID), this will throw an Exception!
def getItemById(item_id):
    # TODO: rewrite this method to catch the Exception in case `result' is empty
    query_string = 'select * from Items where ItemID = $itemID'
    result = query(query_string, {'itemID': item_id})
    try:
        result[0]
        return result[0]
    except:
        return None

# wrapper method around web.py's db.query method
# check out http://webpy.org/cookbook/query for more info
def query(query_string, vars = {}, update = False):
    if update:
        db.query(query_string, vars)
    else:
        return list(db.query(query_string, vars))

#####################END HELPER METHODS#####################
def getBids(item_id):
    try:
        query_string = 'select * from Bids where ItemID = $item_id'
        result = query(query_string, {'item_id': item_id})
        result[0]
        return result
    except:
        return None

def getBuyer(item_id, current_price):
    try:
        query_string = 'select UserID from Bids where ItemID = $item_id and Amount = $price'
        result = query(query_string, {'item_id': item_id, 'price': current_price})
        result[0]
        return result[0]
    except:
        return None

def getCategory(item_id):
    try:
        query_string = 'select Category from Categories where ItemID = $item_id'
        result = query(query_string, {'item_id': item_id})
        result[0]
        return result
    except:
        return None

def checkUser(user_id):
    try:
        query_string = 'select * from Users where UserID = $user_id'
        result = query(query_string, {'user_id': user_id})
        test = result[0]
        return True
    except Exception as e:
        return False

def checkItem(item_id):
    try:
        query_string = 'select * from Items where ItemID = $item_id limit 1'
        result = query(query_string, {'item_id': item_id})
        test = result[0]
        return True
    except Exception as e:
        return False

def checkCategory(category):
    try:
        query_string = 'select * from Categories where Category = $category limit 1'
        result = query(query_string, {'category': category})
        test = result[0]
        return True
    except Exception as e:
        return False

def checkBid(item_id):
    item = getItemById(item_id)
    currentTime = getTime()
    startTime = item.Started
    buyPrice = item.Buy_Price
    currentPrice = item.Currently
    endTime = item.Ends

    priceCheck = False
    if(buyPrice==None):
        priceCheck =True
    elif(currentPrice<buyPrice):
        priceCheck = True

    return (startTime <= currentTime and endTime >= currentTime and priceCheck)

def checkMin(minPrice):
    try:
        query_string = 'select * from Items where Items.Currently >=$minPrice limit 1'
        result = query(query_string, {'minPrice': minPrice})
        test = result[0]
        return True
    except Exception as e:
        return False

def checkMax(maxPrice):
    try:
        query_string = 'select * from Items where Items.Currently <=$maxPrice limit 1'
        result = query(query_string, {'maxPrice': maxPrice})
        test = result[0]
        return True
    except Exception as e:
        return False

def checkStatus(value,currentTimeString):
    try:
        if value == 'open':
            query_string = 'select * from Items where Items.Ends>'+currentTimeString + ' and Currently<Buy_Price limit 1'
        elif value == 'close':
            query_string = 'select * from Items where Items.Ends<'+currentTimeString + ' and Currently>=Buy_Price limit 1'
        elif value == 'notStarted':
            query_string = 'select * from Items where Items.Started>'+currentTimeString + ' limit 1'
        else:
            return True
        result = query(query_string)
        test = result[0]
        return True
    except Exception as e:
        return False
