#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, jsonify, \
    url_for
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, CategoryItem, Users
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response, Session, flash
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web'
                                                                ]['client_id']

APPLICATION_NAME = 'Catalog Application'

# Connect to Database and create database session

engine = create_engine('sqlite:///CatItem.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/')
def index():
    """index
    This function helps to show the Category and recent added items,
    This is the start point to the application
    Returns:
        Template : catalog_index.html
    """

    categories = session.query(Category).order_by(asc(Category.name))
    items = \
        session.query(CategoryItem).order_by(CategoryItem.created_date.desc())
    return render_template('catalog_index.html', categories=categories,
                           items=items)


@app.route('/login', methods=['GET', 'POST'])
def login_form():
    """login_form
    This functtion shows the login page if the user is not logged in already.
    Returns:
        Template : login.html
    """

    if request.method == 'GET':

        # Create anti-forgery state token

        state = ''.join(random.choice(string.ascii_uppercase +
                                      string.digits) for x in range(32))
        login_session['state'] = state
        return render_template('login.html', STATE=state)


@app.route('/catalog.json')
def catalog_json():
    """catalog_json
    This functtion return the JSON of all Category information,
    and all item information in each category.
    Returns:
        JSON : [Category][Items]
    """

    result = {'Category': []}

# Get all Categories

    categories = session.query(Category).order_by(asc(Category.name))
    for cat in categories:
        cat_obj = {}
        cat_obj['id'] = cat.id
        cat_obj['name'] = cat.name
        cat_obj['Item'] = []

        # Get all Items in this category

        items = \
            session.query(CategoryItem).filter_by(category_id=cat.id).all()
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
    """item_json
    This functtion return the JSON one item information.
    Returns:
        JSON : Item
    """

    item = session.query(CategoryItem).filter_by(name=item_name).one()
    item_obj = {}
    item_obj['cat_id'] = item.category_id
    item_obj['description'] = item.description
    item_obj['id'] = item.id
    item_obj['title'] = item.name
    return jsonify('item', item_obj)


@app.route('/catalog/<path:cat_name>/items')
def catalog_index(cat_name):
    """catalog_index
    This functtion shows all items in one category.
    Returns:
        Template : show.html
    """

    print 'yahoooo'
    category = session.query(Category).filter_by(name=cat_name).one()
    items = \
        session.query(CategoryItem).filter_by(category_id=category.id).all()
    return render_template('category/show.html', category=category,
                           items=items)


@app.route('/catalog/<path:item_name>/edit', methods=['GET', 'POST'])
def item_edit(item_name):
    """Item Edit
    This Function helps to show the edit form,
    update the item with new values.
    Returns:
    Redirect|Template --
    If get request > Template form.html
    If Post request > redirect url_for('index')
    """

    if 'username' not in login_session:
        return redirect('/login')
    item = session.query(CategoryItem).filter_by(name=item_name).one()

    if login_session['id'] != item.user_id:

        # Not Authorised

        return redirect('/login')

    if request.method == 'GET':
        categories = \
            session.query(Category).order_by(asc(Category.name))
        return render_template('items/form.html',
                               categories=categories, item=item)
    elif request.method == 'POST':
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
    """item_create
    This Function helps to show the create form,
    create the item in the database.
    Returns:
    Redirect|Template --
    If get request > Template create.html
    If Post request > redirect url_for('index')
    """

    if 'username' not in login_session:

        # Not Authenticated

        return redirect('/login')

    if request.method == 'GET':
        categories = \
            session.query(Category).order_by(asc(Category.name))
        return render_template('items/create.html',
                               categories=categories)
    elif request.method == 'POST':
        if request.form['name'] and request.form['description'] \
                and request.form['category_id']:
            print 'in if'
            currentUser = \
                session.query(Users).filter_by(email=login_session['email'
                                                                   ]).one()
            newITem = CategoryItem(user_id=currentUser.id,
                                   user_email=login_session['email'],
                                   name=request.form['name'],
                                   description=request.form['description'
                                                            ],
                                   category_id=request.form['category_id'
                                                            ])
            session.add(newITem)
            session.commit()
            flash('Item added')
        else:
            flash('Item not added!')

        return redirect(url_for('index'))


@app.route('/catalog/<path:item_name>/delete', methods=['GET', 'POST'])
def item_delete(item_name):
    """item_delete
    This Function helps to show the Delete form,
    delelte the item from the database.
    Returns:
        Redirect|Template --
        If get request > Template delete.html
        If Post request > redirect url_for('index')
    """

    if 'username' not in login_session:
        return redirect('/login')
    item = session.query(CategoryItem).filter_by(name=item_name).one()

    if login_session['id'] != item.user_id:

        # Not Authorised

        return redirect('/login')

    if request.method == 'POST':
        print 'wrong'
        session.delete(item)
        session.commit()
        return redirect(url_for('index'))
    else:
        return render_template('items/delete.html', item=item)


@app.route('/catalog/<path:item_name>/show')
def show(item_name):
    """show
    This Function helps to show the item detail form.
    Returns:
        Template -- show.html
    """

    item = session.query(CategoryItem).filter_by(name=item_name).one()
    return render_template('items/show.html', item=item)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """gconnect
    This Function helps to login with google.
    Returns:
        If user logged in already,
        OR user logged in successfully > redirect to index.
    """

    # Validate state token

    print '<gco>'
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'
                                            ), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain authorization code

    code = request.data

    try:

        # Upgrade the authorization code into a credentials object

        oauth_flow = flow_from_clientsecrets('client_secrets.json',
                                             scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = \
            make_response(json.dumps('Authorization code failed.'
                                     ), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.

    access_token = credentials.access_token
    url = \
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' \
        % access_token
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
        response = \
            make_response(json.dumps("Token Mismatch."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.

    if result['issued_to'] != CLIENT_ID:
        response = \
            make_response(json.dumps("Token's client ID does not match app's."
                                     ), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = \
            make_response(json.dumps('Current user is already connected.'
                                     ), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.

    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info

    userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['uid'] = data['id']

    existUser = \
        session.query(Users).filter_by(email=login_session['email'
                                                           ]).first()

    if existUser:
        print 'Exist user, so update info'
        existUser.name = login_session['username']
        existUser.email = login_session['email']
        existUser.picture = login_session['email']
        session.add(existUser)
        session.commit()
    else:
        print 'create new user'
        newUser = Users(name=login_session['username'],
                        email=login_session['email'],
                        picture=login_session['email'])
        session.add(newUser)
        session.commit()

    existUser = \
        session.query(Users).filter_by(email=login_session['email'
                                                           ]).first()
    login_session['id'] = existUser.id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px; '
    output += ' webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash('you are now logged in as %s' % login_session['username'])
    print 'done!'
    return output


# DISCONNECT - Revoke a current user's token and reset their login_session

@app.route('/logout')
def logout():
    """logout
    This Function helps to logout from google.
    Returns:
        redirect to index
    """

    access_token = login_session['access_token']
    username = login_session['username']
    print('In gdisconnect access token is %s', access_token)
    print 'User name is: '
    print login_session['username']
    if username is None:
        print 'Access Token is None'
        flash('You are already logged out!')
        return redirect(url_for('index'))

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
        % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result

    if result['status'] == 200:
        flash('Google: Token succesfully revoked')
    else:
        flash('Logged out successfully!')

    for i in ['access_token', 'gplus_id', 'username', 'email', 'picture'
              ]:
        if i in login_session:
            del login_session[i]

    return redirect(url_for('index'))


if True or __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(host='0.0.0.0', port=8000)
