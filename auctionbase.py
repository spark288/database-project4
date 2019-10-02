#!/usr/bin/env python

import sys; sys.path.insert(0, 'lib') # this line is necessary for the rest
import os                             # of the imports to work!

import web
import sqlitedb
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

###########################################################################################
##########################DO NOT CHANGE ANYTHING ABOVE THIS LINE!##########################
###########################################################################################

######################BEGIN HELPER METHODS######################

# helper method to convert times from database (which will return a string)
# into datetime objects. This will allow you to compare times correctly (using
# ==, !=, <, >, etc.) instead of lexicographically as strings.

# Sample use:
# current_time = string_to_time(sqlitedb.getTime())

def string_to_time(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

# helper method to render a template in the templates/ directory
#
# `template_name': name of template file to render
#
# `**context': a dictionary of variable names mapped to values
# that is passed to Jinja2's templating engine
#
# See curr_time's `GET' method for sample usage
#
# WARNING: DO NOT CHANGE THIS METHOD
def render_template(template_name, **context):
    extensions = context.pop('extensions', [])
    globals = context.pop('globals', {})

    jinja_env = Environment(autoescape=True,
            loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
            extensions=extensions,
            )
    jinja_env.globals.update(globals)

    web.header('Content-Type','text/html; charset=utf-8', unique=True)

    return jinja_env.get_template(template_name).render(context)

#####################END HELPER METHODS#####################

urls = ('/currtime', 'curr_time',
        '/selecttime', 'select_time',
        # TODO: add additional URLs here
        # first parameter => URL, second parameter => class name
        '/', 'index',
        '/timetable', 'timetable',
        '/add_bid', 'addbid',
        '/item', 'show_item',
        '/search', 'search'
        )

class curr_time:
    # A simple GET request, to '/currtime'
    #
    # Notice that we pass in `current_time' to our `render_template' call
    # in order to have its value displayed on the web page
    def GET(self):
        current_time = sqlitedb.getTime()
        return render_template('curr_time.html', time = current_time)

class select_time:
    # Aanother GET request, this time to the URL '/selecttime'
    def GET(self):
        return render_template('select_time.html')

    # A POST request
    #
    # You can fetch the parameters passed to the URL
    # by calling `web.input()' for **both** POST requests
    # and GET requests
    def POST(self):
        post_params = web.input()
        MM = post_params['MM']
        dd = post_params['dd']
        yyyy = post_params['yyyy']
        HH = post_params['HH']
        mm = post_params['mm']
        ss = post_params['ss'];
        enter_name = post_params['entername']


        selected_time = '%s-%s-%s %s:%s:%s' % (yyyy, MM, dd, HH, mm, ss)
        update_message = '(Hello, %s. Previously selected time was: %s.)' % (enter_name, selected_time)
        # TODO: save the selected time as the current time in the database
        sqlitedb.updateTime(selected_time)

        # Here, we assign `update_message' to `message', which means
        # we'll refer to it in our template as `message'
        return render_template('select_time.html', message = update_message)

class index:
    def GET(self):
        return render_template('index.html')

class timetable:
    def GET(self):
        return render_template('timetable.html')

class show_item:
    def GET(self):
        return render_template('item.html', item = None)
    def POST(self):
        post_params = web.input()
        item_id = post_params['item_id']
        bid_result = sqlitedb.getBids(item_id)
        item = sqlitedb.getItemById(item_id)
        categories = sqlitedb.getCategory(item_id)
        current_time = sqlitedb.getTime()
        if item['Buy_Price'] is not None:
            buy_price = item['Buy_Price']
        else:
            buy_price = float('inf')

        winner = None
        if item['Ends'] > current_time and item['Currently'] < buy_price:
            open = True
        else:
            if item['Number_of_Bids'] > 0:
                winner = sqlitedb.getBuyer(item_id, item['Currently'])['UserID']
            open = False
        return render_template('item.html', bid_result = bid_result, item = item, categories = categories, open = open, winner = winner)

class addbid:
    def GET(self):
        return render_template('add_bid.html')

    def POST(self):
        current_time = sqlitedb.getTime()
        post_params = web.input()
        userID = post_params['userID']
        price = post_params['price']
        itemID = post_params['itemID']

        if sqlitedb.checkUser(userID):
            try:
                if sqlitedb.checkBid(itemID):
                    t = sqlitedb.transaction()
                    try:
                        sqlitedb.query('INSERT INTO Bids (itemID, UserID, Amount, Time) VALUES ($itemID, $userid, $price, $time) ', {'itemID': itemID, 'userid': userID, 'price': price, 'time' : current_time }, True)
                    except Exception as e:
                        t.rollback()
                        print str(e)
                        update_message = 'Failed'
                        result = False
                    else:
                        t.commit()
                        update_message = 'Success'
                        result = True
                else:
                    update_message = 'Closed item'
                    result = False
            except Exception as e:
                print(e)
                update_message = 'Item does not exist'
                result = False
        else:
            update_message = 'User does not exist'
            result = False
        return render_template('add_bid.html', add_result = result, message = update_message)

class search:
    def GET(self):
        return render_template('search.html')
    def POST(self):
        post_params = web.input()
        itemID = post_params['itemID']
        userID = post_params['userID']
        itemCategory = post_params['itemCategory']
        minPrice = post_params['minPrice']
        maxPrice = post_params['maxPrice']
        status = post_params['status']
        itemDescription = post_params['itemDescription']
        userInfo = {'itemID':itemID,'itemCategory':itemCategory,'itemDescription':itemDescription,'userID':userID,'minPrice':minPrice,'maxPrice':maxPrice,'status':status}
        searchinfo = {}
        searchlen = {'select':['distinct','*'],'from':[],'where':[]}
        searchstring = ""

        for key,value in userInfo.items():
            if value != "":
                if "itemID" == key:
                    if not sqlitedb.checkItem(value):
                            error_message = 'Following Item ID does not exist:' + value
                            return render_template('search.html',message = error_message)
                    if "Items" not in searchlen['from']:
                        searchlen['from'].append('Items')
                    searchlen['where'].append('Items.itemID = $itemID')

                elif "userID" == key:
                    if not sqlitedb.checkUser(value):
                            error_message = 'Following User ID does not exist:' + value
                            return render_template('search.html',message = error_message)
                    if "Items" not in searchlen['from']:
                        searchlen['from'].append('Items')
                    searchlen['where'].append('exists(select Users.userID from Users where Users.userID = $userID and Items.Seller_UserID==Users.userID)')

                elif "itemCategory" == key:
                    if not sqlitedb.checkCategory(value):
                            error_message = 'Following Item Category does not exist :' + value
                            return render_template('search.html',message = error_message)
                    if "Items" not in searchlen['from']:
                        searchlen['from'].append('Items')
                    searchlen['where'].append('exists(select Categories.itemID from Categories where Categories.category = $itemCategory and Categories.itemID = Items.itemID)')

                elif "itemDescription" == key:
                    if "Items" not in searchlen['from']:
                        searchlen['from'].append('Items')
                    searchlen['where'].append('Items.Description like $itemDescription')
                    value = '%' + value + '%'

                elif "minPrice" == key:
                    if not sqlitedb.checkMin(value):
                            error_message = 'Following price does not exist:' + value
                            return render_template('search.html',message = error_message)
                    if "Items" not in searchlen['from']:
                        searchlen['from'].append('Items')
                    searchlen['where'].append('Items.Currently >= $minPrice')

                elif "maxPrice" == key:
                    if not sqlitedb.checkMax(value):
                            error_message = 'Following price does not exist:' + value
                            return render_template('search.html',message = error_message)
                    if "Items" not in searchlen['from']:
                        searchlen['from'].append('Items')
                    searchlen['where'].append('Items.Currently <= $maxPrice')

                elif "status" == key:
                    currentTime=sqlitedb.getTime()
                    currentTimeString = '\''+currentTime+'\''
                    if not sqlitedb.checkStatus(value,currentTimeString):
                            error_message = 'An item does not exist with Status:' + value
                            return render_template('search.html',message = error_message)
                    if "Items" not in searchlen['from']:
                        searchlen['from'].append('Items')
                    if value == 'open':
                        searchlen['where'].append('Items.Ends>' + currentTimeString +' and Currently<Buy_Price')
                    elif value == 'close':
                        searchlen['where'].append('(Items.Ends<' + currentTimeString + ' or Currently>=Buy_Price)')
                    elif value == 'notStarted':
                        searchlen['where'].append('Items.Started>' + currentTimeString)
                    else:
                        pass
                searchinfo[key] = value
            else:
                print(key + "does not have data.")

        searchstring = 'select'
        for index,value in enumerate(searchlen['select']):
            if(index+1 != len(searchlen['from'])):
                searchstring = searchstring + ' ' + value
            else:
                searchstring = searchstring + ' ' + value

        if len(searchlen['from'])!=0:
            searchstring = searchstring + ' from'
            for index,value in enumerate(searchlen['from']):
                if(index+1 != len(searchlen['from'])):
                    searchstring = searchstring + ' ' + value + ','
                else:
                    searchstring = searchstring + ' ' + value

        if len(searchlen['where'])!=0:
            searchstring = searchstring + ' where'
            for index,value in enumerate(searchlen['where']):
                if(index+1 != len(searchlen['where'])):
                    searchstring = searchstring + ' ' + value + ' and'
                else:
                    searchstring = searchstring + ' ' + value
        t = sqlitedb.transaction()
        try:
            search_result = sqlitedb.query(searchstring, searchinfo)

        except Exception as e:
            t.rollback()
            print str(e)
        else:
            t.commit()
        return render_template('search.html',search_result = search_result, search_params=userInfo)

###########################################################################################
##########################DO NOT CHANGE ANYTHING BELOW THIS LINE!##########################
###########################################################################################

if __name__ == '__main__':
    web.internalerror = web.debugerror
    app = web.application(urls, globals())
    app.add_processor(web.loadhook(sqlitedb.enforceForeignKey))
    app.run()
