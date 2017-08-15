################################################################################
#####                           Imports                                    #####
################################################################################
from flask import (Flask, render_template, request,
                   redirect, jsonify, url_for, flash)
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from db_setup import Base, User, Category, Item
from flask import session as login_session
import random
import string
# from settings import CLIENT_ID
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

################################################################################
#####                           Globals                                    #####
################################################################################
app = Flask(__name__)
engine = create_engine('sqlite:///category.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())[
    'web']['client_id']

################################################################################
#####                        Authentication                                #####
################################################################################


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, CLIENT_ID=CLIENT_ID)


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

    flash("you are now logged in as {}".format(login_session['username']))
    return "Hello, {}".format(login_session['username'])


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps(
            'Current user not connected.'), 401)
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
        return render_template('logout.html', response=response)
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

################################################################################
#####                         Helper Functions                             #####
################################################################################


def get_items(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category_id=category.id)
    return items


def get_single_item(category_name, item_name):
    category = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(
        category_id=category.id, title=item_name).first()
    return item


def get_category(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    return category


def get_user_email():
    if login_session['username']:
        return login_session['email']

################################################################################
#####                         Routing                                      #####
################################################################################


@app.route('/')
@app.route('/home')
def showCatalog():
    user = login_session.get('username')
    categories = session.query(Category).all()
    items = session.query(Item).order_by(Item.created_at.desc()).limit(6).all()
    return render_template('home.html', categories=categories, user=user, items=items)


@app.route('/json')
def catalogJSON():
    items = session.query(Item).all()
    return jsonify([i.serialize for i in items])


@app.route('/<string:category_name>/items')
def showCategory(category_name):
    user = login_session.get('username')
    category = get_category(category_name)
    items = get_items(category_name)
    return render_template('items.html', category_name=category.name, items=items, user=user)


@app.route('/<string:category_name>/create', methods=['GET', 'POST'])
def createItem(category_name):
    if 'username' not in login_session:
        return redirect('/login')
    user = login_session.get('username')
    category = get_category(category_name)

    if request.method == 'POST':
        newItem = Item(
            title=request.form['title'],
            description=request.form['description'],
            category_id=category.id,
            user_id=login_session.get('email'))
        session.add(newItem)
        session.commit()

        flash('Item {}'.format(newItem.title))
        return redirect(url_for('showCategory', category_name=category_name, user=user))
    else:
        return render_template('create_item.html', category_name=category_name, user=user)


@app.route('/<string:category_name>/edit/<string:item_name>', methods=['GET', 'POST'])
def editItem(category_name, item_name):
    if 'username' not in login_session:
        return redirect('/login')

    user = login_session.get('username')
    u_email = get_user_email()
    category = get_category(category_name)
    editItem = get_single_item(category_name, item_name)

    if request.method == 'POST':
        if u_email == editItem.user_id:
            if request.form['title']:
                editItem.title = request.form['title']

            if request.form['description']:
                editItem.description = request.form['description']

            session.add(editItem)
            session.commit()
        else:
            flash('You do not have the authorization to edit that item')

        return redirect(url_for('showCategory', category_name=category_name, user=user))

    else:
        return render_template('update_item.html', user=user, category_name=category_name, item_name=editItem.title, editItem=editItem)


@app.route('/<string:category_name>/delete/<string:item_name>', methods=['GET', 'POST'])
def deleteItem(category_name, item_name):
    if 'username' not in login_session:
        return redirect('/login')
    user = login_session.get('username')
    u_email = get_user_email()
    category = get_category(category_name)
    deleteItem = get_single_item(category_name, item_name)

    if request.method == 'POST':
        if u_email == deleteItem.user_id:
            session.delete(deleteItem)
            session.commit()
        else:
            flash('You do not have the authorization to delete that item')
        return redirect(url_for('showCategory', category_name=category_name, user=user))

    else:
        return render_template('delete_item.html', user=user, category_name=category_name, item_name=deleteItem.title)


################################################################################
#####                         Run App                                      #####
################################################################################


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
