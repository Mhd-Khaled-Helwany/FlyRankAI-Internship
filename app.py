from flask import Flask, jsonify, request

app = Flask(__name__)

# First endpoint, simple JSON response
# Use command "flask run" to run the server
# To see the response in browser go to http://127.0.0.1:5000/backend
# To see the response in terminal use curl command: curl http://127.0.0.1:5000/backend
@app.route("/backend")
def backend():
    result = {"message": "testing the backend"}
    return jsonify(result)


# Second endpoint, JSON response to an input
# Use command "flask run" to run the server
# To see the response in browser go to http://127.0.0.1:5000/greet
# To see the response in terminal use curl command: curl http://127.0.0.1:5000/greet
# No input will return "Hello, Guest!", to provide input add ?name=YourName at the end of the URL
# e.g., http://127.0.0.1:5000/greet?name=John
@app.route("/greet")
def greet():
    name = request.args.get("name", "Guest")
    result = {"message": f"Hello, {name}!"}
    return jsonify(result)