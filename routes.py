from flask import *
from functools import wraps
import sqlite3
from flask_bootstrap import Bootstrap
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_wtf import FlaskForm
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy  import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm, CsrfProtect



artists = ['Solomun', 'Dubfire']
# DJname = request.form['DJname']



DATABASE = 'Beatscrape.db'

app = Flask(__name__)
app.secret_key = 'my precious'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////mnt/C:/flask/Beatscrape.db'
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
app.config.from_object(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
csrf = CsrfProtect(app)





class LoginForm(FlaskForm):
	username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
	password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
	remember = BooleanField('remember me')


class RegisterForm(FlaskForm):
	email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
	username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
	password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])


class User(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(15), unique=True)
	email = db.Column(db.String(50), unique=True)
	password = db.Column(db.String(80))

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


   
def connect_db():
	return sqlite3.connect(app.config['DATABASE'])

@app.route('/')  
def home():
	return render_template('home.html')

@app.route('/welcome')
def welcome():
	return render_template('welcome.html')
	
	

@app.route('/register', methods=['GET', 'POST'])
def register():
	form = RegisterForm()
	if form.validate_on_submit():
		conn = sqlite3.connect('Beatscrape.db')
		cursor = conn.cursor()
		hashed_password = generate_password_hash(form.password.data, method='sha256')
		new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
		posts = [dict(username=row[0], email=row[1], password=row[2]) for row in cursor.fetchall()]
#        usr = User(username=form.username.data, email=form.email.data, password=hashed_password)
		usrname = form.username.data
		emailname = form.email.data
		pw = password=hashed_password
		cursor.execute("INSERT INTO users VALUES (NULL,?,?,?)", (usrname,emailname,pw,))
		conn.commit()
		cursor.close()
		conn.close()
		flash('User Created')
		#return '<h1>' + form.username.data + ' ' + form.email.data + ' ' + form.password.data + '</h1>'

	return render_template('register.html', form=form)




@app.route('/log', methods=['GET', 'POST'])
@csrf.exempt
def log():
	form = LoginForm()
   
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data).first()
		if user:
			if check_password_hash(user.password, form.password.data):
				login_user(user, remember=form.remember.data)
				return redirect(url_for('hello'))

		return '<h1>Invalid username or password</h1>'
		#return '<h1>' + form.username.data + ' ' + form.password.data + '</h1>'

	return render_template('log.html', form=form)
	
	

# 11/14 ... updated scrapelist2 in attempts to get the user input to be saved in ArtistMonitor table
@app.route('/scrapelist2', methods=['GET', 'POST'])
def scrapelist2():
	if request.method == 'POST':
		global feed
		conn = sqlite3.connect('Beatscrape.db')
		cursor = conn.cursor()
		posts = [dict(DJname=row[0]) for row in cursor.fetchall()]
		DJname = request.form['Producername']
		cursor.execute("INSERT INTO ArtistMonitor VALUES (NULL,?)", (DJname,))
		conn.commit()
		cursor.close()
		conn.close()
		artists.append(request.form['Producername'])
	g.db = connect_db()
	cur = g.db.execute('select DJName from ArtistMonitor')
	cur2 = g.db.execute('select * from Tracks where artist in (select DJname from ArtistMonitor)')
	pull = [dict(DJname=row[0]) for row in cur.fetchall()]
	watch = [dict(Artist=row[0], Song=row[1], Websource=row[2], Genre=row[3]) for row in cur2.fetchall()]
	g.db.close()
	return render_template('scrapelist2.html', selected='submit', pull=pull, watch=watch)

	
@app.route('/delete_artist/<DJName>', methods=['POST'])
def delete_artist(DJName):
	conn = sqlite3.connect('Beatscrape.db')
	cursor = conn.cursor()
	del1 = [dict(id=row[0], DJName=row[1]) for row in cursor.fetchall()]
#	DJName1 = request.args.get('DJName')
	cursor.execute("DELETE FROM ArtistMonitor WHERE DJName = ?", (DJName,))
	conn.commit()
	cursor.close()
	conn.close()
	flash('Artist Deleted')
	return redirect(url_for('scrapelist2', del1=del1))
	
	
def login_required(test):
	@wraps(test)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return test(*args, **kwargs)
		else:
			flash('You need to login first.')
			return redirect(url_for('log'))
	return wrap


@app.route('/logout')
def logout():
	session.pop('logged_in', None)
	flash('You were logged out')
	return redirect (url_for('log'))

@app.route('/hello')
@login_required
def hello():
	g.db = connect_db()
	cur = g.db.execute('select Artist, Song, Label, Price from BeatPortTechHouse')
	info = [dict(Artist=row[0], Song=row[1], Label=row[2], Price=row[3]) for row in cur.fetchall()]
	g.db.close()
	return render_template('hello.html', info=info)




if __name__ == '__main__':
	app.run(debug=True)