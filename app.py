from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
import os
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message

app = Flask(__name__)
basedir=os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'planets.db')
app.config['JWT_SECRET_KEY'] = 'super_secret' #change this later
app.config['MAIL_SERVER']='smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = '81ced89b1c30b5'
app.config['MAIL_PASSWORD'] = 'e93be68e449b7d'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

db=SQLAlchemy(app)
ma=Marshmallow(app)
jwt= JWTManager(app)
mail=Mail(app)

@app.cli.command('db_create')
def db_create():
	db.create_all()
	print('database created')


@app.cli.command('db_drop')
def db_drop():
	db.drop_all()
	print('database dropped')


@app.cli.command('db_seed')
def db_seed():
	mercury = Planet(planet_name='Mercury',
					 planet_type='Class D',
					 home_star='Sol',
					 mass=2.258e23,
					 radius=1516,
					 distance=35.98e6)

	venus = Planet(planet_name='Venus',
				   planet_type='Class K',
				   home_star='Sol',
				   mass=4.867e24,
				   radius=3760,
				   distance=67.24e6)

	earth = Planet(planet_name='Earth',
				   planet_type='Class M',
				   home_star='Sol',
				   mass=5.972e24,
				   radius=3959,
				   distance=92.96e6)
	
	db.session.add(mercury)
	db.session.add(venus)
	db.session.add(earth)

	test_user = User(	first_name='Pramod',
						last_name="pardeshi",
						email="test@test.com",
						password="passwor"
					)
	db.session.add(test_user)
	db.session.commit()
	print('database seeded')


@app.route("/")
def hello_world():
	return "hello world"


@app.route('/super_simple')
def super_simple():
	return jsonify(msg='Hello from planetary api mod')


@app.route('/not_found')
def not_found():
	return jsonify(msg='Hello from planetary api mod'), 404


@app.route('/parameters')
def parameters():
	name= request.args.get('name')
	age= int(request.args.get('age'))
	
	if age < 18:
		return jsonify(message=f"sorry {name} you are not old enough"), 401
		#401 unautorized access
	else:
		return jsonify(message=f"welcome {name}")


@app.route('/url_vars/<string:name>/<int:age>')
def url_vars(name, age):

	if age < 18:
		return jsonify(message=f"sorry {name} you are not old enough"), 401
	else:
		return jsonify(message=f"welcome {name}")


@app.route('/planets',methods=['GET'])
def planets():
	planets_list=Planet.query.all()
	#return jsonify(data=planets_list)
	# does not work jsonify cannot convert objects to json 
	#i.e. (serialisation) converting object into its text reprentation
	result = planets_schema.dump(planets_list)
	print(result)
	return jsonify(result)


@app.route('/register',methods=['Post'])
def register():
	email=request.form['email']

	if User.query.filter_by(email=email).first():#check if email already exists
		return jsonify(message='User already exist'), 409 #conflict
	else:
		first_name = request.form['first_name']
		last_name = request.form['last_name']
		password = request.form['password']
		user = User(	first_name = first_name,
						last_name = last_name,
						email = email,
						password = password
					)
		db.session.add(user)
		db.session.commit()
		return jsonify(message=f'{first_name} successfully registered'), 201 #cresated new record


@app.route('/login',methods=['POST'])
def login():
	if request.is_json:
		email = request.json['email']
		password = request.json['password']
	else:
		email = request.form['email']
		password = request.form['password']

	test = User.query.filter_by(email=email,password=password).first()
	if test:
		access_token = create_access_token(identity=email)
		return jsonify(message='login successfully', access_token=access_token)
	else:
		return jsonify(message="Invalid credentials"), 401 #permission denied


@app.route('/planet_data/<int:planet_id>')
def planet_data(planet_id):
	planet=Planet.query.filter_by(planet_id=planet_id).first()

	if planet:
		planet_info=planet_schema.dump(planet)
		return jsonify(planet_info)
	else:
		return jsonify(message="planet does not exist"), 404 #not found


@app.route('/add_planet',methods=['POST'])
@jwt_required
def add_planet():
	planet_name = request.form.get('planet_name')
	test = Planet.query.filter_by(planet_name=planet_name).first()
	if test :
		return jsonify(message=f'planet {planet_name} already exists in database'), 409
	else:
		planet_type = request.form.get('planet_type')
		home_star = request.form.get('home_star')
		mass = float(request.form.get('mass'))
		radius = float(request.form.get('radius'))
		distance = float(request.form.get('distance'))
		new_planet = Planet(planet_name = planet_name,
				   planet_type = planet_type,
				   home_star = home_star,
				   mass = mass,
				   radius = radius,
				   distance = distance)

		db.session.add(new_planet)
		db.session.commit()
		return jsonify(message=f'{planet_name} added to planets'), 201


@app.route('/update_planet',methods=['PUT'])
@jwt_required
def update_planet():
	planet_id = int(request.form.get('planet_id'))
	planet = Planet.query.filter_by(planet_id=planet_id).first()
	if planet:
		planet.planet_name = request.form.get('planet_name')
		planet.planet_type = request.form.get('planet_type')
		planet.home_star = request.form.get('home_star')
		planet.mass = float(request.form.get('mass'))
		planet.radius = float(request.form.get('radius'))
		planet.distance = float(request.form.get('distance'))
		db.session.commit()
		return jsonify(message=f"updated the data of planet {planet.planet_name}")
	else:	
		return jsonify(f'the planet with id {planet_id} does not exists in database'), 404


@app.route('/remove_planet/<int:planet_id>',methods=['DELETE'])
@jwt_required
def remove_planet(planet_id):
	planet = Planet.query.filter_by(planet_id=planet_id).first()
	if planet:
		db.session.delete(planet)
		db.session.commit()
		return jsonify(message=f"deleted planet with id {planet_id}"), 202 #change accepted
	else:
		return jsonify(f'the planet with id {planet_id} does not exists in database'), 404


# database models
class User(db.Model):
	__tablename__ = 'users'
	id = Column(Integer, primary_key=True)
	first_name = Column(String)
	last_name = Column(String)
	email = Column(String, unique=True)
	password = Column(String)


class Planet(db.Model):
	__tablename__ = 'planets'
	planet_id = Column(Integer, primary_key=True)
	planet_name = Column(String, unique=True)
	planet_type = Column(String)
	home_star = Column(String)
	mass = Column(Float)
	radius = Column(Float)
	distance = Column(Float)


@app.route('/forget_pwd/<string:email>',methods=['GET'])
def forget_pwd(email):
	user = User.query.filter_by(email=email).first()

	if user:
		msg = Message("your api password is "+user.password,sender='admin@api.com',recipients=[email])
		mail.send(msg)
		return jsonify(message=f"password sent to {email}")
	else:
		return jsonify(message=f"invalid email {email}"), 401



#marshmallow
class UserSchema(ma.Schema):
	class Meta:
		fields = ('id', 'first_name', 'last_name', 'email', 'password')


class PlanetSchema(ma.Schema):
	class Meta:
		fields = ('planet_id', 'planet_name', 'planet_type', 'home_star', 'mass', 'radius', 'distance')


user_schema = UserSchema()
users_schema = UserSchema(many=True)

planet_schema = PlanetSchema()
planets_schema = PlanetSchema(many=True)


if __name__ == '__main__':
	app.run(debug=True)

