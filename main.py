from flask import Flask,render_template
app = Flask(__name__)

# default-page
@app.route(“/”)
def home():
   return “hello world”

# about-page
@app.route(“/buranji”)
def about():
    return render_template(“buranji”)

if __name__ == “__main__”:
   app.run()
