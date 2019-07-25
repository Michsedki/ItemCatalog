from flask import Flask, render_template, request, redirect, jsonify, url_for
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, CategoryItem
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response, Session, flash
import requests


from flask import Flask
app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

APPLICATION_NAME = "Catalog Application"

# Connect to Database and create database session
engine = create_engine('sqlite:///CatItem.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

'''
Appwise Routes
'''


@app.route('/')
def index():
    categories = session.query(Category).order_by(asc(Category.name))
    items = session.query(CategoryItem).order_by(
        (CategoryItem.created_date.desc()))
    return render_template('catalog_index.html', categories=categories, items=items)


'''Auth Routes'''


@app.route('/login', methods=['GET', 'POST'])
def login_form():
    if request.method == "GET":
        # Create anti-forgery state token
        state = ''.join(random.choice(string.ascii_uppercase +
                                      string.digits) for x in range(32))
        login_session['state'] = state
        return render_template('login.html', STATE=state)
    elif request.method == "POST":
        return "Login Handler"

    # # Check that the access token is valid.
    # access_token = credentials.access_token
    # url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
    #        % access_token)
    # h = httplib2.Http()
    # result = json.loads(h.request(url, 'GET')[1])
    # # If there was an error in the access token info, abort.
    # if result.get('error') is not None:
    #     response = make_response(json.dumps(result.get('error')), 500)
    #     response.headers['Content-Type'] = 'application/json'
    #     return response


'''
Catalog Routes
'''


@app.route('/catalog.json')
def catalog_json():
    result = {'Category': []}

# Get all Categories
    categories = session.query(Category).order_by(asc(Category.name))
    for cat in categories:
        cat_obj = {}
        cat_obj['id'] = cat.id
        cat_obj['name'] = cat.name
        cat_obj['Item'] = []

        # Get all Items in this category
        items = session.query(CategoryItem).filter_by(category_id=cat.id).all()
        for item in items:

            item_obj = {}
            item_obj['cat_id'] = item.category_id
            item_obj['description'] = item.description
            item_obj['id'] = item.id
            item_obj['title'] = item.name

            cat_obj['Item'].append(item_obj)

        result['Category'].append(cat_obj)
    return jsonify(result)


@app.route('/catalog/<path:item_name>/JSON')
def item_json(item_name):

    item = session.query(CategoryItem).filter_by(name=item_name).one()
    item_obj = {}
    item_obj['cat_id'] = item.category_id
    item_obj['description'] = item.description
    item_obj['id'] = item.id
    item_obj['title'] = item.name
    return jsonify('item', item_obj)


@app.route('/catalog/<path:cat_name>/items')
def catalog_index(cat_name):
    print("yahoooo")
    category = session.query(Category).filter_by(name=cat_name).one()
    items = session.query(CategoryItem).filter_by(category_id=category.id).all()
    return render_template('category/show.html', category=category, items=items)


'''
Item Routes
'''


@app.route('/catalog/<path:item_name>/edit', methods=['GET', 'POST'])
def item_edit(item_name):
    if 'username' not in login_session:
        return redirect('/login')
    item = session.query(CategoryItem).filter_by(name=item_name).one()

    if request.method == 'GET':
        categories = session.query(Category).order_by(asc(Category.name))
        return render_template('items/form.html', categories=categories, item=item)
    elif request.method == "POST":
        if request.form['name']:
            item.name = request.form['name']
        if request.form['description']:
            item.description = request.form['description']
        if request.form['category_id']:
            item.category_id = request.form['category_id']

        session.add(item)
        session.commit()

        return redirect(url_for('index'))


@app.route('/catalog/create', methods=['GET', 'POST'])
def item_create():
    if 'username' not in login_session:
        return redirect('/login')

    if request.method == 'GET':
        categories = session.query(Category).order_by(asc(Category.name))
        return render_template('items/create.html', categories=categories)
    elif request.method == "POST":
        print("yahoooooooo")
        if request.form['name'] and request.form['description'] and request.form['category_id']:
            print("in if")
            newITem = CategoryItem(user_id=1, user_email=login_session['email'], name=request.form['name'],
                                   description=request.form['description'], category_id=request.form['category_id'])
            session.add(newITem)
            session.commit()
            flash("Item added")

        else:
            flash("Item not added!")

        return redirect(url_for('index'))


@app.route('/catalog/<path:item_name>/delete', methods=['GET', 'POST'])
def item_delete(item_name):

    if 'username' not in login_session:
        return redirect('/login')

    item = session.query(CategoryItem).filter_by(name=item_name).one()
    if request.method == 'POST':
        print("wrong")
        session.delete(item)
        session.commit()
        return redirect(url_for('index'))
    else:
        return render_template('items/delete.html', item=item)


@app.route('/catalog/<path:item_name>/show')
def show(item_name):
    item = session.query(CategoryItem).filter_by(name=item_name).one()
    return render_template('items/show.html', item=item)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    print("<gco>")
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

    print(data)

    login_session['username'] = data['email']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['uid'] = data['id']

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


@app.route('/logout')
def logout():
    access_token = login_session['access_token']
    username = login_session['username']
    print('In gdisconnect access token is %s', access_token)
    print('User name is: ')
    print(login_session['username'])
    if username is None:
        print('Access Token is None')
        flash("You are already logged out!")
        return redirect(url_for('index'))

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print('result is ')
    print(result)

    if(result['status'] == 200):
        flash("Google: Token succesfully revoked")
    else:
        flash("Google: Token doesn't exist!")

    for i in ['access_token', 'gplus_id', 'username', 'email', 'picture']:
        if i in login_session:
            del login_session[i]

    return redirect(url_for('index'))


if True or __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True

    app.config['SESSION_TYPE'] = 'filesystem'

    # sess = Session()
    # sess.init_app(app)

    app.run(host='0.0.0.0', port=8000)
