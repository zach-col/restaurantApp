from flask import Flask, render_template, flash, url_for, redirect, request, jsonify

app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem

# imports for google login session
from flask import session as login_session
import random
import string

# stores oauth parameters
from oauth2client.client import flow_from_clientsecrets
# import for error if oauth does not work
from oauth2client.client import FlowExchangeError
import httplib2
# api to convert python to json serialize
import json
# converts function into a response object to sent to client
from flask import make_response
import requests


CLIENT_ID = json.loads(
open('client_secrets.json', 'r').read())['web']['client_id']




engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

#pseudo data for  Restaurants
# restaurant = {'name': 'The CRUDdy Crab', 'id': '1'}

# restaurants = [{'name': 'The CRUDdy Crab', 'id': '1'}, {'name':'Blue Burgers', 'id':'2'},{'name':'Taco Hut', 'id':'3'}]


# pseudo data for Menu Items
# items = [ {'name':'Cheese Pizza', 'description':'made with fresh cheese', 'price':'$5.99','course' :'Entree', 'id':'1'}, {'name':'Chocolate Cake','description':'made with Dutch Chocolate', 'price':'$3.99', 'course':'Dessert','id':'2'},{'name':'Caesar Salad', 'description':'with fresh organic vegetables','price':'$5.99', 'course':'Entree','id':'3'},{'name':'Iced Tea', 'description':'with lemon','price':'$.99', 'course':'Beverage','id':'4'},{'name':'Spinach Dip', 'description':'creamy dip with fresh spinach','price':'$1.99', 'course':'Appetizer','id':'5'} ]
# item =  {'name':'Cheese Pizza','description':'made with fresh cheese','price':'$5.99','course' :'Entree'}

# login page create anti forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# google logout/disconnect
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response



# home page all restaurants
@app.route('/')
@app.route('/restaurants/')
def showRestaurants():
    restaurants = session.query(Restaurant).all()
    if len(restaurants) == 0:
        flash("You currently have no restaurants")
    else :
        pass
    return render_template('restaurants.html', restaurants = restaurants)

# create new restaurants
@app.route('/restaurant/new/', methods=['GET', 'POST'])
def newRestaurant():
    # if user is not logged in redirect to log in
    if 'username' not in login_session:
        return redirect('/login')

    restaurants = session.query(Restaurant).all()
    if request.method == 'POST':
        newRestaurant = Restaurant(name = request.form['name'])
        session.add(newRestaurant)
        session.commit()
        flash("New Restaurant Created")
        return redirect(url_for('showRestaurants'))
    else:
        return render_template('newrestaurant.html', restaurants = restaurants)

# edit a restaurant
@app.route('/restaurant/<int:restaurant_id>/edit/', methods=['GET', 'POST'])
def editRestaurant(restaurant_id):
    # if user is not logged in redirect to log in
    if 'username' not in login_session:
        return redirect('/login')

    restaurants = session.query(Restaurant).all()
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if request.method == 'POST':
        if request.form['name']:
            restaurant.name = request.form['name']
        session.add(restaurant)
        session.commit()
        flash("Restaurant Successfully Edited")
        return redirect(url_for('showRestaurants'))
    else:
        return render_template('editrestaurant.html', restaurant = restaurant, restaurants = session.query(Restaurant).all())

# delete a restaurant
@app.route('/restaurant/<int:restaurant_id>/delete/', methods=['GET', 'POST'])
def deleteRestaurant(restaurant_id):
    # if user is not logged in redirect to log in
    if 'username' not in login_session:
        return redirect('/login')

    restaurants = session.query(Restaurant).all()
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    if request.method == 'POST':
        session.delete(restaurant)
        session.commit()
        flash("Restaurant Successfully Deleted")
        return redirect(url_for('showRestaurants'))
    else:
        return render_template('deleterestaurant.html', restaurant = restaurant, restaurants = restaurants)

# restaurant menu
@app.route('/restaurant/<int:restaurant_id>/')
@app.route('/restaurant/<int:restaurant_id>/menu/')
def showMenu(restaurant_id):
    restaurants = session.query(Restaurant).all()
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
    if len(items) == 0:
        flash("You currently have no menu items")
    else :
        pass
    return render_template("menu.html", restaurant_id = restaurant_id, items = items, restaurant = restaurant, restaurants = restaurants)

# create new restaurant menu item
@app.route('/restaurant/<int:restaurant_id>/menu/new/', methods=['GET', 'POST'])
def newMenuItem(restaurant_id):
    # if user is not logged in redirect to log in
    if 'username' not in login_session:
        return redirect('/login')

    restaurants = session.query(Restaurant).all()
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()

    if request.method == 'POST':
        newItem = MenuItem(
            name = request.form['name'],
            description = request.form['description'],
            price = request.form['price'],
            course = request.form['course'],
            restaurant_id = restaurant_id)
        session.add(newItem)
        session.commit()
        flash("New Item Created")
        return redirect(url_for('showMenu', restaurant_id = restaurant_id))
    else:
        return render_template("newmenuitem.html", restaurant = restaurant, restaurant_id = restaurant_id, restaurants = restaurants)

# edit restaurant menu item
@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit/', methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
    # if user is not logged in redirect to log in
    if 'username' not in login_session:
        return redirect('/login')

    restaurants = session.query(Restaurant).all()
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    editItem = session.query(MenuItem).filter_by(id = menu_id).one()
    if request.method == 'POST':
        editItem.name = request.form['name']
        editItem.description = request.form['description']
        editItem.price = request.form['price']
        session.add(editItem)
        session.commit()
        flash("Item Successfully Edited")
        return redirect(url_for('showMenu', restaurant_id = restaurant_id))
    else:
        return render_template("editmenuitem.html", restaurant_id = restaurant_id, editItem = editItem, restaurants = restaurants)

    return render_template("editmenuitem.html", editItem = editItem)

# delete restaurant menu item
@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete/', methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
    # if user is not logged in redirect to log in
    if 'username' not in login_session:
        return redirect('/login')

    restaurants = session.query(Restaurant).all()
    restaurant = session.query(MenuItem).filter_by(id = restaurant_id).one()
    item = session.query(MenuItem).filter_by(id = menu_id, restaurant_id = restaurant.id).one()
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        flash("Item Successfully Deleted")
        return redirect(url_for('showMenu', restaurant_id = restaurant_id))
    else:
        return render_template("deletemenuitem.html", restaurant_id = restaurant_id, menu_id = menu_id, item = item, restaurant = restaurant, restaurants = restaurants)

# JSON endpoints
# json for all restaurants
@app.route('/restaurants/JSON')
def restaurantsJSON():
    restaurants = session.query(Restaurant).all()
    return jsonify(Restaurant=[i.serialize for i in restaurants])

# json for all restaurant menu items
@app.route('/restaurant/<int:restaurant_id>/menu/JSON/')
def restaurantMenuJSON(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()

    items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])

#json for restaurant menu item
@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/JSON/')
def restaurantItemJSON(restaurant_id, menu_id):
    item = session.query(MenuItem).filter_by(id = menu_id, restaurant_id = restaurant_id).one()
    return jsonify(MenuItems=[item.serialize])

if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.debug = True
    app.run(host = '0.0.0.0', port= 5000)