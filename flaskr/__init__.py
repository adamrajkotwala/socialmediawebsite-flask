import os

from flask import Flask
from flask_mail import Mail

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.config['MAIL_SERVER'] = "10.200.146.27" 
    app.config['MAIL_PORT'] = 25
    app.config['MAIL_USE_TLS'] = True 
    app.config['MAIL_USE_SSL'] = False 
    app.config['MAIL_USERNAME'] = None 
    app.config['MAIL_PASSWORD'] = None 
    app.config['MAIL_DEFAULT_SENDER'] = 'default-sender@wv.gov' 

    mail = Mail(app)

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import blog
    app.register_blueprint(blog.bp)
    app.add_url_rule('/', endpoint='index')

    from . import user
    app.register_blueprint(user.bp)

    from . import uploads
    app.register_blueprint(uploads.bp)

    from . import notifications
    app.register_blueprint(notifications.bp)

    from . import functions
    app.register_blueprint(functions.bp)

    return app