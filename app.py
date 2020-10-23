import backend
from flask import Flask, render_template, request

# creating the application named app
app = Flask(__name__)


@app.route("/", methods=["POST", "GET"])
def index():
    if request.method == "POST":
        place = request.form.get("search")
        location = backend.get_location_by_name(place)
    else:
        location = backend.get_location_by_ip()
        backend.is_location(location)
    info = backend.setting_info(location)
    return render_template("index.html", info=info)


if __name__ == '__main__':
    app.run(threaded=True, port=5000)
