from flask import Flask, render_template, request, redirect, url_for
import requests
import pymongo
from flask import flash
import os
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# Set secret key for message flashing
app.secret_key = os.urandom(24)


def send_password_to_email(to_address, password):
    # Set up the SMTP server
    smtp_server = "your_smtp_server.com"
    smtp_port = 587
    username = "abcdsfhan@gmail.com"
    password = "zpaf xboz emoh upf"
    from_address = "abcdsfhan@gmail.com"

    # Create the email message
    subject = "Your Password Recovery"
    body = f"Your password is: {password}"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_address
    msg["To"] = to_address

    try:
        # Connect to the SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(username, password)

        # Send the email
        server.sendmail(from_address, [to_address], msg.as_string())

        # Close the connection
        server.quit()

        return True  # Email sent successfully

    except Exception as e:
        print(f"Error: {e}")
        return False  # Failed to send email


# Connect to the MongoDB database
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["brewery_review_system"]

# Create a collection in the database to store reviews
reviews_collection = db["reviews"]

users_collection = db["users"] 

# Define the index route
@app.route("/",methods=["GET", "POST"])
def index():
     return render_template("home.html")

# Define the login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Check if the user exists in the database
        user = users_collection.find_one({"username": username})
        if user is not None and user["password"] == password:
            # Login successful
            return redirect(url_for("search"))
        else:
            # Invalid credentials
            error_message = "Invalid username or password"
            return render_template("login.html", error_message=error_message)
    else:
        return render_template("login.html")

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form["username"]

        # Check if the user with the provided username exists in the database
        user = users_collection.find_one({"username": username})
        if user is not None:
            # Check if the provided username matches the registered email address
            if user["username"] == user:
                # Send the password to the user's email
                send_password_to_email(user["username"], user["password"])

                # Provide a success message (you may redirect or display a success message)
                flash("Password sent to your email.", "success")
                return redirect(url_for("login"))
            else:
                # Invalid username or email address
                error_message = "Invalid username or email address"
                return render_template("forgot_password.html", error_message=error_message)
        else:
            # User with the provided username doesn't exist
            error_message = "Invalid username or email address"
            return render_template("forgot_password.html", error_message=error_message)
    else:
        return render_template("forgot_password.html")

# Define the signup route
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if len(password) < 8:
            # Password is too short, show an error message
            error_message = "Password must be at least 8 characters long"
            return render_template("signup.html", error_message=error_message)
        
        # Check if the username already exists
        user = users_collection.find_one({"username": username})
        if user is not None:
            # Username already exists
            error_message = "Username already taken"
            return render_template("signup.html", error_message=error_message)
        else:
            # Create a new user in the database
            users_collection.insert_one({"username": username, "password": password})

            # Signup successful
            return redirect(url_for("login"))
    else:
        return render_template("signup.html")



@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        search_term = request.form["search_term"]
        search_type = request.form["search_type"]

        if search_type == "by_city":
            response = requests.get("https://api.openbrewerydb.org/breweries?by_city=" + search_term)
        elif search_type == "by_name":
            response = requests.get("https://api.openbrewerydb.org/breweries?by_name=" + search_term)
        elif search_type == "by_type":
            response = requests.get("https://api.openbrewerydb.org/breweries?by_type=" + search_term)

        breweries = response.json()

        # Extract required details from the response
        formatted_breweries = []
        for brewery in breweries:
            formatted_brewery = {
                "name": brewery["name"],
                "id": brewery["id"],
                "address": brewery["address_1"],
                "phone": brewery["phone"],
                "website": brewery["website_url"],
                "state": brewery["state"],
                "city": brewery["city"]
            }
            formatted_breweries.append(formatted_brewery)

        return render_template("search.html", breweries=formatted_breweries)
    else:
        return render_template("search.html")


# Define the brewery route
@app.route("/brewery/<name>", methods=["GET", "POST"])
def brewery(name):
    brewery = requests.get(f"https://api.openbrewerydb.org/breweries?by_name={name}").json()

    # Get reviews for the brewery from the database
    brewery_reviews = reviews_collection.find({"brewery_name": name})

    if request.method == "POST":
        rating = request.form["rating"]
        description = request.form["description"]

        # Add the review to the database
        review = { "brewery_name": name ,"rating": rating, "description": description}
        reviews_collection.insert_one(review)
        
         # Flash a success message
        flash("Review and Rating submitted successfully!", "success")


    return render_template("brewery.html", brewery=brewery, reviews=brewery_reviews)

# Define the brewery info route
@app.route("/brewery_info/<name>", methods=["GET"])
def brewery_info(name):
    brewery = requests.get(f"https://api.openbrewerydb.org/breweries?by_name={name}").json()

    # Get reviews for the brewery from the database
    brewery_reviews = reviews_collection.find({"brewery_name": name})

    return render_template("brewery_info.html", brewery=brewery, reviews=brewery_reviews)

if __name__ == "__main__":
    app.run(debug=True, port=8000)
