from flask import Flask, render_template, flash, redirect, url_for, request, redirect, session
from data import Articles
from flask_mysqldb import MySQL
from flask_wtf import FlaskForm
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

Articles = Articles()

# MySQL configuration #
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'db_user'
app.config['MYSQL_PASSWORD'] = 'passw0rd'
app.config['MYSQL_DB'] = 'pythonflask_app'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

@app.route('/')
def home():
  return render_template('home.html')

@app.route('/about')
def about():
  return render_template('about.html')

@app.route('/articles')
def articles():
  # Add Cursor
  cur = mysql.connection.cursor()

  # Query for articles in database
  resultVal = cur.execute('SELECT * FROM articles')

  articleData = cur.fetchall()
  cur.close()
  if resultVal > 0 :
    # Pass the details to dashboard for display
    return render_template('articles.html', article_data = articleData)
  else:
    message = 'No Articles Found'
    return render_template('articles.html', info = message)

  return render_template('articles.html')


@app.route('/article/<string:id>')
def article(id):
  # Add Cursor
  cur = mysql.connection.cursor()

  # Query for articles in database
  cur.execute('SELECT * FROM articles WHERE id = %s',[id])

  articleData = cur.fetchone()

  return render_template('article.html', article=articleData)



@app.route('/database')
def database():
  # Defining Cursor to open a connection
  cur = mysql.connection.cursor()
  
  # Executing Query
  # cur.execute('SELECT * FROM users')
  cur.execute( 'INSERT INTO users (name,email,username,password) VALUES(%s,%s,%s,%s)', ('Test3','test3@gmail.com','test_user_3','test_3@123') )

  # Commit Changes
  mysql.connection.commit()

  # Close Connection
  cur.close()


  # returnValue = cur.fetchall()
  # return str(returnValue)
  flash('You were successfully logged in','success')
  # return "Success"
  return redirect(url_for('home'))



class RegistrationForm(Form):
  name              = StringField('Name', [validators.length( min=1 ,max=50 )] )
  username          = StringField('User Name', [validators.length( min=4 ,max=25 )] )
  email             = StringField('Email', [validators.length( min=5 ,max=50 )] )
  password          = PasswordField ('Password', [
                                # validators.DataRequired(),
                                validators.EqualTo('confirm_password', message='Passwords does not match')
                              ])
  confirm_password  = PasswordField('Confirm Password')



@app.route('/register', methods=['GET','POST'])
def register():
  form = RegistrationForm(request.form)
  if request.method == 'POST' and form.validate():
    name = form.name.data
    email = form.email.data
    username = form.username.data
    password = sha256_crypt.encrypt(form.password.data)


    # Create cursor
    cur = mysql.connection.cursor()

    # Executing Query
    cur.execute( 'INSERT INTO users (name,email,username,password) VALUES(%s,%s,%s,%s)', (name,email,username,password) )

    # Commit to MySQL
    mysql.connection.commit()

    # Close the connection
    cur.close()

    flash('You have successfully register. You can now login from Login Page', 'success')
    return redirect(url_for('login'))
  
  return render_template('register.html', form_data=form)

@app.route ('/login', methods=['GET','POST'] )
def login():

  if request.method == 'POST':
    # Get Form Fields
    username = request.form['username']
    password_candidate = request.form['password']

    # Create cursor
    cur = mysql.connection.cursor()

    # Get user by username
    result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

    if result > 0:
      # Get stored hash
      data = cur.fetchone()
      password = data['password']

      # Compare Passwords
      if sha256_crypt.verify(password_candidate, password):
          # Passed
          session['logged_in'] = True
          session['username'] = username

          flash('You are now logged in', 'success')
          return redirect(url_for('dashboard'))
      else:
          error = 'Invalid login'
          return render_template('login.html', error=error)
      # Close connection
      cur.close()
    else:
      error = 'Username not found'
      return render_template('login.html', error=error)

  return render_template('login.html')

def is_loggedin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' in session:
          return f(*args, **kwargs)
        else:
          flash('Unauthorized, please login','danger')
          return redirect(url_for('login'))
    return decorated_function




@app.route('/logout')
def logout():
  session.clear()
  flash('Successfully logged out','success')
  return redirect(url_for('home'))

@app.route('/dashboard')
@is_loggedin
def dashboard():

  # Add Cursor
  cur = mysql.connection.cursor()

  # Query for articles in database
  resultVal = cur.execute('SELECT * FROM articles')

  articleData = cur.fetchall()

  if resultVal > 0 :
    # Pass the details to dashboard for display
    return render_template('dashboard.html', article_data = articleData)
  else:
    message = 'No Articles Found'
    return render_template('dashboard.html', info = message)

  return render_template('dashboard.html')

# Article Form Class
class ArticleForm(Form):
  title   = StringField('Title', [validators.length( min=1 ,max=200 )] )
  body    = TextAreaField('Body', [validators.length( min=30 )] )


@app.route('/add_article', methods = ['GET','POST'])
@is_loggedin
def addarticle():
  form = ArticleForm(request.form)
  if request.method == 'POST' and form.validate():
    title = form.title.data
    body  = form.body.data

    # Create cursor
    cur = mysql.connection.cursor()

    # Execute query
    cur.execute('INSERT INTO articles( title, author, body) VALUES(%s,%s,%s)',(title,session['username'],body))
    # Commit the update
    mysql.connection.commit()

    # Close the connection
    cur.close()

    flash('Article posted','success')
    return redirect(url_for('dashboard'))

  return render_template('add_article.html',article_data=form)



if __name__ == "__main__":
  app.secret_key = 'secret123'
  app.run(host="0.0.0.0",port=8080,debug=True)


