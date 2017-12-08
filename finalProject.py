from flask import Flask, render_template, flash, url_for, redirect, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem

app = Flask(__name__)

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


@app.route('/')
@app.route('/restaurants/')
def showRestaurants():
    restaurants = session.query(Restaurant).all()
    if len(restaurants) == 0:
        flash("You currently have no restaurants")
    else :
        pass
    return render_template('restaurants.html', restaurants = restaurants)

@app.route('/restaurant/new/', methods=['GET', 'POST'])
def newRestaurant():
    restaurants = session.query(Restaurant).all()
    if request.method == 'POST':
        newRestaurant = Restaurant(name = request.form['name'])
        session.add(newRestaurant)
        session.commit()
        flash("New Restaurant Created")
        return redirect(url_for('showRestaurants'))
    else:
        return render_template('newrestaurant.html', restaurants = restaurants)

@app.route('/restaurant/<int:restaurant_id>/edit/', methods=['GET', 'POST'])
def editRestaurant(restaurant_id):
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

@app.route('/restaurant/<int:restaurant_id>/delete/', methods=['GET', 'POST'])
def deleteRestaurant(restaurant_id):
    restaurants = session.query(Restaurant).all()
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    if request.method == 'POST':
        session.delete(restaurant)
        session.commit()
        flash("Restaurant Successfully Deleted")
        return redirect(url_for('showRestaurants'))
    else:
        return render_template('deleterestaurant.html', restaurant = restaurant, restaurants = restaurants)

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

@app.route('/restaurant/<int:restaurant_id>/menu/new/', methods=['GET', 'POST'])
def newMenuItem(restaurant_id):
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


@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit/', methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
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

@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete/', methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
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

@app.route('/restaurants/JSON')
def restaurantsJSON():
    restaurants = session.query(Restaurant).all()
    return jsonify(Restaurant=[i.serialize for i in restaurants])

# Making api endpoint for all items in restaurant menu (get request)
@app.route('/restaurant/<int:restaurant_id>/menu/JSON/')
def restaurantMenuJSON(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()

    items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])

@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/JSON/')
def restaurantItemJSON(restaurant_id, menu_id):
    item = session.query(MenuItem).filter_by(id = menu_id, restaurant_id = restaurant_id).one()
    return jsonify(MenuItems=[item.serialize])

if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.debug = True
    app.run(host = '0.0.0.0', port= 5000)