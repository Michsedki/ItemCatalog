from flask import Flask, render_template, request, redirect, jsonify, url_for
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, CategoryItem
from flask import session as login_session
import random
import string
# from oauth2client.client import flow_from_clientsecrets
# from oauth2client.client import FlowExchangeError
# import httplib2
# import json
# from flask import make_response
# import requests


from flask import Flask
app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine('sqlite:///CatItem.db', connect_args={'check_same_thread': False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

'''
Appwise Routes
'''


@app.route('/')
def index():
    categories = session.query(Category).order_by(asc(Category.name))
    items = session.query(CategoryItem).order_by(asc(CategoryItem.created_date))

    return render_template('index.html', categories=categories, items=items)


'''Auth Routes'''


@app.route('/login', methods=['GET', 'POST'])
def login_form():
    if request.method == "GET":
        return render_template('login.html')
        
    elif request.method == "POST":   
        return "Login Handler"


'''
Catalog Routes
'''


@app.route('/catalog.json')
def catalog_json():
    return "index"


@app.route('/catalog/<path:cat_name>/items')
def catalog_index(cat_name):
    category = session.query(Category).filter_by(name=cat_name).one()
    items = session.query(CategoryItem).filter_by(category_id=category.id).all()
    return render_template('category/show.html', category=category, items=items)

'''
Item Routes
'''

@app.route('/catalog/<path:item_name>/edit', methods=['GET', 'POST'])
def item_edit(item_name):
    item = session.query(CategoryItem).filter_by(name=item_name).one()

    if request.method == 'GET':
        categories = session.query(Category).order_by(asc(Category.name))
        return render_template('items/form.html', categories=categories, item=item)
    elif request.method == "POST":

        modified_item = request.form
        item.name = modified_item['name']
        item.description = modified_item['description']
        item.category_id = modified_item['category_id']

        session.add(item)
        session.commit()

        return redirect(url_for('index'))


@app.route('/catalog/item_name/create', methods=['GET', 'POST'])
def item_update():
    if request.method == 'GET':
        return "Edit"
    elif request.method == "POST":
        return "Update"
    


@app.route('/catalog/item_name/delete')
def item_delete():
            # session.delete(itemToDelete)

    return "index"


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
        print("Token's client ID does not match app's.")
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
    # flash("you are now logged in as %s" % login_session['username'])
    print("done!")
    return output

    # DISCONNECT - Revoke a current user's token and reset their login_session


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)