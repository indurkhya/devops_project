# Main code is here
from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
# from werkzeug import secure_filename
import json
import math
import os

with open('config.json', 'r') as c:
    params = json.load(c)["params"]

local_server = True
app = Flask(__name__)
app.secret_key = 'super-secret-key'
# app.config['UPLOAD_FOLDER'] = params['file_uploader']

#  Below code is for connecting the gmail to get an update from users to my local mailbox.
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail_user'],
    MAIL_PASSWORD=params['gmail_password']
)
mail = Mail(app)
if (local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_url']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_url']
db = SQLAlchemy(app)

''' 
  sno , name email, phone_num ,msg, date
'''

class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(30), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12))


class Post(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(30), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12))
    img_file = db.Column(db.String(12))


# @app.route("/")
# def wb():
#     return render_template('index.html')
#     # return "Welcome to Flask framework"

@app.route("/home")
def home():
    # ####################################     Pagination logic  ######################################################
    posts = Post.query.filter_by().all()  # [0:params['no-of-post']]
    last = math.ceil(len(posts) / int(params["no-of-post"]))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page - 1) * int(params['no-of-post']):(page - 1) * int(params['no-of-post']) + int(params["no-of-post"])]
    if (page == 1):
        prev = "#"
        next = "/home?page=" + str(page + 1)
    elif (page == last):
        prev = "/home?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/home?page=" + str(page - 1)
        next = "/home?page=" + str(page + 1)
    # ####################################     Pagination logic  ###########################################################

    return render_template('home.html', params=params, posts=posts,prev2=prev,next2=next)
    # return render_template('index.html', params=params, posts=posts, prev=prev, next=next)


@app.route("/index")
def index():
    return render_template('index.html', params=params)

@app.route("/")
def broswer():
    return render_template('index.html', params=params)


@app.route("/about")
def about():
    return render_template('about.html', params=params)


# Dashboard page code in this page i am checking session and if meet the user details then it will passed credentials
# it will allow to view the dashboard
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    # ############################# Checking the session as user is valid or not ##############################
    if ('user' in session and session['user'] == params['admin-user']):
        # ############################# Fetching all the post from the post table from db ##############################
        posts = Post.query.all()
        # print("hello",posts)
        # render template is used to return the html page as its connected parameters
        return render_template('dashboard.html', params=params, posts=posts)

    if request.method == 'POST':
        ''' Fetch entry from the dashboard page '''
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        ''' Validate entry dashboard page '''
        if (username == params['admin-user'] and userpass == params['admin-pass']):
            ''' Set the session variable '''
            session['user'] = username
            posts = Post.query.all()
            return render_template('dashboard.html', params=params, posts=posts)

    return render_template('login.html', params=params)
    # ############################# End Section ##############################


# Edit post it will be under dashboard and it will give rights to edit or modify the post
@app.route("/edit/<string:sno>", methods=["GET", "POST"])
def edit(sno):
    # ############################# Checking the session as user is valid or not ##############################
    if ('user' in session and session['user'] == params['admin-user']):
        ''' Checking for the post request from the web page and taking the details from user and storing in db '''
        if request.method == 'POST':
            ''' Fetch entry from the post page '''
            box_title = request.form.get('title')
            tline = request.form.get('tagline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')

            if sno == '0':
                post = Post(title=box_title, slug=slug, content=content, tagline=tline, img_file=img_file)
                db.session.add(post)
                db.session.commit()
            else:
                post = Post.query.filter_by(sno=sno).first()
                post.title = box_title
                post.tagline = tline
                post.slug = slug
                post.content = content
                post.img_file = img_file
                db.session.commit()
                return redirect('/edit/' + sno)
        post = Post.query.filter_by(sno=sno).first()
    return render_template('edit.html', params=params, post=post, sno=sno)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == 'POST':
        ''' Fetch entry from the contact page '''
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        message = request.form.get('message')

        ''' Add entry to the database'''
        entry = Contact(name=name, phone_num=phone, email=email, msg=message)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from ' + name,
                          sender=email,
                          recipients=[params['gmail-user']],
                          body=message + "\n" + phone
                          )
    return render_template('contact.html', params=params)


@app.route("/post/<string:post_slug>", methods=['GET'])
def post1(post_slug):
    post = Post.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)


@app.route("/uploader", methods=["GET", "POST"])
def uploader():
    if ('user' in session and session['user'] == params['admin-user']):
        if (request.method == 'POST'):
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER']))#, secure_filename(f.filename)))
            return "Uploaded successfully"


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')


@app.route("/delete/<string:sno>", methods=["GET", "POST"])
def delete(sno):
    if ('user' in session and session['user'] == params['admin-user']):
        post = Post.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')


app.run(debug=True)