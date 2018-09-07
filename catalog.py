from flask import (Flask,
                   render_template,
                   request, flash,
                   redirect,
                   url_for,
                   jsonify,
                   make_response)
from flask import session as login_session

from sqlalchemy import create_engine, or_, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

import random
import string
import httplib2
import json
import requests

app = Flask(__name__)

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

CLIENT_ID = json.loads(open('client_secrets.json',
                            'r').read())['web']['client_id']


@app.route('/')
def catalog():
    """Main page"""
    latest_items = session.query(Item).order_by(desc(Item.created))\
        .limit(10).all()
    for item in latest_items:
        print(item.created)

    return render_template('latest_items.html', categories=get_categories(),
                           latestItems=latest_items)


@app.route('/catalog')
def redirect_catalog():
    """Redirect to main page"""
    return redirect(url_for('catalog'))


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """Function to connect with a google login"""
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
        print ("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already \
        connected.'), 200)
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

    if get_user_id(login_session['email']) is None:
        create_user()

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: "' \
              '150px;-webkit-border-radius: 150px;\
              -moz-border-radius: 150px;"> '
    flash("You are now logged in as %s." % login_session['username'])
    print ("done!")
    return output


@app.route("/gdisconnect")
def gdisconnect():
    """Function to disconnect"""
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % \
          login_session['access_token']
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
        flash("You successfully logged out.")
        return redirect("http://localhost:8000")
    else:
        login_session.clear()
        flash("You successfully logged out.")
        return redirect("http://localhost:8000")


@app.route('/catalog/<string:category_name>/items')
def show_category_items(category_name):
    """Shows all category items"""
    cat = session.query(Category).filter_by(name=category_name).first()
    items = session.query(Item).filter_by(category_name=cat.name).all()

    return render_template('category_items.html', categories=get_categories(),
                           cat=cat, items=items)


@app.route('/login')
def show_login():
    """Shows login template"""
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state

    return render_template('login.html', STATE=state)


@app.route('/catalog/<string:category_name>/<string:item_name>')
def show_item(category_name, item_name):
    """Shows item template"""
    item = session.query(Item).filter_by(name=item_name).\
        filter_by(category_name=category_name).first()
    return render_template('item.html', item=item)


@app.route('/catalog/add', methods=['GET', 'POST'])
def add_item():
    """Logic to add an item"""
    if 'username' not in login_session:
        flash("You are not logged in! Please log in to add items.")
        return redirect(url_for('show_login'))

    categories = session.query(Category).all()

    if request.method == 'POST':

        if session.query(Item).filter_by(name=request.form['title']).\
                filter_by(category_name=request.form['category']).first()\
                is not None:
            flash("An item with the given name already exists in the \
            description.")
            return render_template('add_item.html', categories=categories)

        item = Item(name=request.form['title'],
                    description=request.form['description'],
                    category_name=request.form['category'],
                    user_id=get_user_id(login_session['email']))
        session.add(item)
        session.commit()
        return redirect(url_for('catalog'))

    else:
        return render_template('add_item.html', categories=categories)


@app.route('/catalog/<string:category_name>/<string:item_name>/edit',
           methods=['GET', 'POST'])
def edit_item(item_name, category_name):
    """Logic to edit items"""
    # Check if user is logged in
    if 'username' not in login_session:
        flash("You are not logged in! Please log in to edit items.")
        return redirect(url_for('show_login'))

    # Query the item from item_name
    item = session.query(Item).filter_by(name=item_name)\
        .filter_by(category_name=category_name).first()

    # Check if user created the item
    if get_user_id(login_session['email']) != item.user_id or\
            get_user_id(login_session['email']) is None:
        flash("You do not have permissions to edit this item!")
        return render_template('item.html', categories=item.category.name,
                               item_name=item.name, item=item)

    # If request was POST, create a new item
    if request.method == 'POST':

        # Check if an item already exists with this name
        if session.query(Item).filter_by(name=request.form['title']).\
                filter_by(category_name=request.form['category']).first()\
                is not None and item.name != request.form['title']:
            flash("An item with the given name already exists in the\
             description.")
            return render_template('edit_item.html', item_name=item.name,
                                   categories=get_categories(), item=item)

        item.name = request.form['title']
        item.description = request.form['description']
        item.category_name = request.form['category']
        session.add(item)
        session.commit()
        return redirect('catalog')

    # If request was GET, show edit template
    else:
        return render_template('edit_item.html', item_name=item_name,
                               categories=get_categories(), item=item)


@app.route('/catalog/<string:category_name>/<string:item_name>/delete',
           methods=['GET', 'POST'])
def delete_item(category_name, item_name):
    """Logic to delete items"""
    if 'username' not in login_session:
        flash("You are not logged in! Please log in to delete items.")
        return redirect(url_for('show_login'))

    item = session.query(Item).filter_by(name=item_name).first()

    if get_user_id(login_session['email']) != item.user_id or\
            get_user_id(login_session['email']) is None:
        flash("You do not have permissions to delete this item!")
        return render_template('item.html', categories=item.category.name,
                               item_name=item.name, item=item)

    if request.method == 'POST':
        session.query(Item).filter_by(name=item_name)\
            .filter_by(category_name=category_name).delete()
        session.commit()
        return redirect(url_for('catalog'))
    else:

        return render_template('delete_confirmation.html', item_name=item_name,
                               category_name=category_name)


@app.route('/catalog.json')
def show_json():
    """Returns a json String for all categories and their items"""
    result = []
    for c in get_categories():
        category_items = session.query(Item)\
            .filter_by(category_name=c.name).all()
        serialized_items = [i.serialize for i in category_items]
        serialized_category = c.serialize
        serialized_category['Item'] = serialized_items
        result.append(serialized_category)

    return jsonify(result=result)


@app.route('/<string:category_name>/<string:item_name>.json')
def json_for_item(category_name, item_name):
    """Returns a json String for a single item"""
    category_name = category_name.capitalize()
    item = session.query(Item).filter_by(name=item_name) \
        .filter(Item.category_name.ilike(category_name)).first()
    return jsonify(item.serialize)


def get_user_id(email):
    """Returns the ID of an user for a given email address, if there is none,
        returns None"""
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def get_categories():
    """Queries all categories"""
    categories = session.query(Category).all()
    return categories


def get_user_info(user_id):
    """Returns the user object for a given user_id"""
    user = session.query(User).filter_by(id=user_id).one()
    return user


def create_user():
    """Creates a new user"""
    new_user = User(name=login_session['username'],
                    email=login_session['email'],
                    picture=login_session['picture'])
    session.add(new_user)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
