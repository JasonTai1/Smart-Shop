from flask import Flask , render_template
from routes.main import main

app = Flask(__name__)
app.register_blueprint(main)

@app.route("/about")
def about():
    return render_template("about.html")

if __name__ == "__main__":
    app.run(debug=True)

