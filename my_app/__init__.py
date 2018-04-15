""" General configuration of the application """

from flask import Flask
app = Flask(__name__)

###################### Configuration ##########################################

# general app config
app.config['SECRET_KEY'] = 'my_secret_key'

# database config for production
# uncomment for deployment
# import MySQLdb
# CLOUDSQL_USER = 'root'
# CLOUDSQL_PASSWORD = 'Salut123'
# CLOUDSQL_DATABASE = 'apt'
# CLOUDSQL_CONNECTION_NAME = 'boh-appointments:us-central1:boh-appointments-sql-id'
# LIVE_SQLALCHEMY_DATABASE_URI = (
#     'mysql://{user}:{password}@localhost/{database}'
#     '?unix_socket=/cloudsql/{connection_name}').format(
#         user=CLOUDSQL_USER, password=CLOUDSQL_PASSWORD,
#         database=CLOUDSQL_DATABASE, connection_name=CLOUDSQL_CONNECTION_NAME)
# app.config['SQLALCHEMY_DATABASE_URI'] = LIVE_SQLALCHEMY_DATABASE_URI

# database config for test
# comment out for deployment
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# flask security config
app.config['SECURITY_PASSWORD_HASH'] = 'pbkdf2_sha512'
app.config['SECURITY_PASSWORD_SALT'] = 'bdeuyu29838ubuyyhdu90eb8y87byd89283b7u89s92'
app.config['SECURITY_POST_LOGIN_VIEW'] = '/admin'
app.config['SECURITY_POST_LOGOUT_VIEW'] = '/admin'

# reCAPTCHA config
app.config['RECAPTCHA_PUBLIC_KEY']='6LfZqEEUAAAAADQRKk0Tg6mMbo2Dij_ohT9KUdjB'
app.config['RECAPTCHA_PRIVATE_KEY']='6LfZqEEUAAAAAByaRU814F_Ea7ipXgujJoQGiNzJ'
app.config['RECAPTCHA_PARAMETERS'] = {'hl': 'en'}
app.config['RECAPTCHA_DATA_ATTRS'] = {'theme': 'light', 'size':'compact'}

###################### making sure that everything gets run once ##############

from my_app import initial_data
from my_app import views
from my_app import data_model
from my_app import admin

