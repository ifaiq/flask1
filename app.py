from flask import Flask, render_template ,request ,flash , redirect , url_for , session
from data import Articles
from flask_mysqldb import MySQL
import mysql.connector
from passlib.hash import sha256_crypt
from functools import wraps
from wtforms import Form , StringField , TextAreaField, PasswordField , validators

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = "12345678"
app.config['MYSQL_DB'] = "FLASK1"
app.config['MYSQL_CURSORCLASS'] = "DictCursor"

# Init database
mysql = MySQL(app)


class Rform(Form):
    name = StringField('Name',[validators.Length(min=4, max=44)])
    username = StringField('User',[validators.Length(min=4, max=44)])
    email = StringField('Email',[validators.length(min=4, max=44)])
    password = PasswordField('Password',[validators.DataRequired(), validators.EqualTo('confirm', message = 'not match')])
    confirm = PasswordField('Confirmed')





articles = Articles()
@app.route("/")
def home():
    return render_template('home.html')
#params<>




@app.route("/about")
def about():
    return render_template('about.html')



@app.route("/articles")
def articless():
    return render_template('articles.html', cars = articles)




class artForm(Form):
    title= StringField('Title', [validators.Length(min=2, max= 50)])
    body= TextAreaField("Body", [validators.Length(min=5)])




@app.route("/register", methods = ["GET", "POST"])
def register():
    form =  Rform(request.form)
    if request.method == 'POST' and form.validate():
        name =  form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # create cursor
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(name , email , username , password) VALUES(%s, %s , %s , %s)" ,
        (name , email , username , password))
        
        # commit to db
        mysql.connection.commit()

        # close connectioin
        cur.close()

        flash("You are now registered and can login" , "success")
        return redirect(url_for('login'))

    return render_template("register.html"  , form = form)






@app.route("/login", methods = ["POST", "GET"])
def login():
    if request.method == 'POST':
        #GET FORM FIELDS
        username = request.form['username']
        password_candid = request.form['password']

        cur = mysql.connection.cursor()
        #GET USER BY USERNAME
        result = cur.execute("SELECT * FROM users WHERE username = %s" ,[username])

        if result > 0:
            #GET STORED HASH
            data = cur.fetchone()
            password = data['password']
            if sha256_crypt.verify(password_candid , password):
                #passed
                session['logged_in'] = True
                session['username'] = username

                flash("You are now logged in " , 'success')
                return redirect(url_for('dashboard'))
            else:
                error = "Invalid LOgin"
                return render_template('login.html' , error=error)
            cur.close()
        else:
            error = "Username not found"
            return render_template('login.html' , error = error)
    return render_template('login.html')






def is_logged_in(g):
    @wraps(g)
    def wrap(*args , **kwargs):
        if 'logged_in' in session:
            return g(*args , **kwargs)
        else:
            flash("Un authorized, Please login " , "danger")
            return redirect(url_for('login'))
    return wrap






@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash("You are now logged out" , "success")
    return redirect(url_for('login'))

    



@app.route('/Dashboard')
@is_logged_in
def dashboard():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM art")
    articles = cur.fetchall()
    if result > 0:
        return render_template('Dashboard.html', articles = articles)
    else:
        msg = "No artiles found"
        return render_template('Dashboard.html', msg = msg)
    cur.close()







@app.route('/create', methods = ["GET","POST"])
@is_logged_in
def create():
    form = artForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        body = form.body.data
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO art(title, body, author) VALUES(%s, %s ,%s)",(title, body, session['username']))
        mysql.connection.commit()
        cur.close()
        flash("Article created","success")
        return redirect(url_for('dashboard'))
    return render_template('create.html', form = form)







@app.route("/edit/<id>" , methods=['GET' , 'POST'])
@is_logged_in
def edit(id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM art WHERE id = %s" , [id])
    article = cur.fetchone()
    form = artForm(request.form)

    form.title.data = article['title']
    form.body.data = article['body']

    if request.method =='POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        #create cursor
        cur = mysql.connection.cursor()

        #execute
        cur.execute("UPDATE art SET title=%s, body=%s WHERE id = %s", (title , body , id))
        
        #Commit to db
        mysql.connection.commit()

        #Close the db
        cur.close()
        flash("Article Updated" , "success")
        return redirect(url_for('dashboard'))
    return render_template("edit.html" , form=form)





@app.route("/delete/<id>" , methods=['POST'])
@is_logged_in
def delete(id):
    cur = mysql.connection.cursor() 
    cur.execute("DELETE FROM art WHERE id = %s", [id])
    mysql.connection.commit()
    cur.close()
    flash("Article Deleted" , "success")
    return redirect(url_for('dashboard'))



if __name__ == "__main__":
    app.secret_key = 'secret123'
    app.run(debug=True, port = 3000)