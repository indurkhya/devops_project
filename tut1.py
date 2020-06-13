from flask import Flask,render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from datetime import datetime
import json
import math
import os


with open('config.json', 'r') as c:
    params = json.load(c)["params"]

local_server = True

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['file_uploader']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL= True,
    MAIL_USERNAME = params['gmail_user'],
    MAIL_PASSWORD = params['gmail_password']
)
mail = Mail(app)
app.config['SQLALCHEMY_DATABASE_URI'] = params['local_url']
db = SQLAlchemy(app)

class Contacts(db.Model):
    # sno , name , email , phone_no , msg , date #db variables
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone_no = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120),  nullable=False)
    date = db.Column(db.String(120), nullable=True)

class Posts(db.Model):
    # sno , name , email , phone_no , msg , date #db variables
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(25), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(12), nullable=True)

@app.route('/')
def home():
    posts = Posts.query.filter_by().all() #[0:params['no_of_posts']]
    return render_template('index.html', params=params, posts=posts)

@app.route("/dashboard", methods=['GET','POST'])
def dashboard():

    if ('user' in session and session['user'] == params['admin-user']):
        posts = Posts.query.all()
        return render_template('dashboard.html',params=params, posts=posts)
    if request.method=='POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if (username==params['admin-user'] and userpass==params['admin-pass']):
            # setting session variable
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html',params=params, posts=posts)
    return render_template("login.html", params=params)

@app.route("/post/<string:post_slug>",methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()

    return render_template("post.html", params=params, post=post)

@app.route("/about")
def about():
    return render_template("about.html", params=params)

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
                post = Posts(title=box_title, slug=slug, content=content, tagline=tline, img_file=img_file,date=datetime.now())
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.tagline = tline
                post.slug = slug
                post.content = content
                post.img_file = img_file
                db.session.commit()
                return redirect('/edit/' + sno)
        post = Posts.query.filter_by(sno=sno).first()
    return render_template('edit.html', params=params, post=post, sno=sno)


@app.route("/contact", methods= ['GET', 'POST'])

def contact():
    if (request.method=='POST'):
        "Add entry to db"
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message= request.form.get('message')
        # sno , name , email , phone_no , msg , date #db variables
        entry = Contacts(name=name, phone_no=phone, email=email, date=datetime.now(), msg=message)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('Message from Blogger.com' + name,
                          sender=email,
                          recipients= [params['gmail_user']],
                          body= message + "\n" + phone
                          )
    return render_template("contact.html", params=params)

@app.route("/uploader", methods=["GET", "POST"])
def uploader():
    if ('user' in session and session['user'] == params['admin-user']):
        if (request.method == 'POST'):
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER']))#, secure_filename(f.filename)))
            return "Uploaded successfully"

@app.route("/delete/<string:sno>", methods=["GET", "POST"])
def delete(sno):
    if ('user' in session and session['user'] == params['admin-user']):
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

app.run(debug=True)




