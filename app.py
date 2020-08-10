from flask import Flask, jsonify, request

app = Flask(__name__)

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


if __name__ == '__main__':
	app.run(debug=True)

