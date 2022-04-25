from flask import Flask, render_template
from views import app_dir_photos

app = Flask(__name__)
app.register_blueprint(app_dir_photos)


@app.route('/')
def index():
    return render_template(
        'index.html',
    )
