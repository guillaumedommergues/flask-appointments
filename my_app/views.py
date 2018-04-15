""" Gets and receives data from the client """

from my_app import app
from flask import render_template, request, redirect, url_for
from flask_login import LoginManager, logout_user, current_user
import json
from datetime import datetime
from wtforms import Form, DateField, DateTimeField
from wtforms import IntegerField, StringField, SelectField
from flask_wtf.recaptcha import RecaptchaField
from wtforms.validators import DataRequired
import pytz
from data_model import db, Role, User, Services
from flask_security import login_required
from communications import send_reminder
from crud import query_available_services, query_available_markets
from crud import query_user_appointment, query_available_days
from crud import cancel_appointments, query_market_appointments
from crud import toggle_appointments
from crud import book_appointment
from crud import add_tbd_appointments
from flask_security import utils

########################## customer-facing interface ##########################

@app.route('/',methods = ['GET','POST'])
def search_what():
    """ 1st customer-facing page - to choose the desired service."""
    
    class WhoWhereForm(Form):
        available_services = query_available_services(days_available = 10)
        wtf_what = SelectField('Product',
            choices = [(service,service) for service in available_services])
    if request.method == 'POST':
        form = WhoWhereForm(request.form)
        what =  form.wtf_what.data
        return redirect(url_for('search_where', what = what))
    if request.method == 'GET':
        form = WhoWhereForm()
        return render_template('search.html', form = form)

@app.route('/where/<what>', methods = ['GET','POST'])
def search_where(what):
    """ 2nd customer-facing page - to choose the desired market."""
    
    class WhoWhereForm(Form):
        today = datetime.now(pytz.timezone('Pacific/Honolulu')).date()
        available_locations = query_available_markets(days_available=10,
                                                    what=what)
        wtf_where = SelectField('Location',
            choices = [(branch,branch) for branch in available_locations])
    if request.method == 'POST':
        form = WhoWhereForm(request.form)
        what = what
        where = form.wtf_where.data
        return redirect(url_for('search_when', what=what, where=where))
    if request.method == 'GET':
        form = WhoWhereForm()
        return render_template('search.html', form=form, what=what)

@app.route('/when/<what>/<where>', methods=['GET','POST'])
def search_when(what, where):
    """ 3d customer-facing page - to choose the desired date."""
    
    class WhoWhereForm(Form):
        available_days = query_available_days(what, where, days_available=10)
        wtf_when = SelectField('Date',
            choices=[(day,day) for day in available_days])
    if request.method == 'POST':
        form = WhoWhereForm(request.form)
        what = what
        where = where
        when = form.wtf_when.data
        return redirect(url_for('book', what=what, where=where, when=when))
    if request.method == 'GET':
        form = WhoWhereForm()
        return render_template(
            'search.html', form=form, what=what, where=where)

@app.route('/book/<what>/<where>/<when>', methods=['GET','POST'])
def book(what, where, when):
    """ 4th customer-facing page - to book the appointment.
    
    GET request :   displays all the possible dates/times
                    for the desired service/market/dates around chosen date
    POST request :  performs a series of checks
                    sends text confirmation to customer
                    sends email invitation to employee
                    stores the appointment details in the database
        
    """
    
    class BookForm(Form):
        wtf_name = StringField('Your name',
                    validators=[DataRequired()])
        wtf_phone = StringField('Your phone number',
                    validators=[DataRequired()])
        wtf_topic = SelectField('No need - autofill',
                    choices=[(x.name,x.name) for x in Services.query.all()])
        wtf_user_id = IntegerField('banker_id')
        wtf_date = DateField('Date', format="%Y-%m-%d")
        wtf_time = DateTimeField('time', format="%Y-%m-%d-%H:%M:%S")
        recaptcha = RecaptchaField()

    if request.method == 'GET':
        form = BookForm()
        data = query_market_appointments(what, where, when)
        return render_template('book.html', data=data, form=form, what=what)
    if request.method == 'POST':
        form = BookForm(request.form)
        if form.validate():
            phone_number = form.wtf_phone.data
            user_id = form.wtf_user_id.data
            apt_time = form.wtf_time.data.time()
            apt_date = form.wtf_date.data
            topic = form.wtf_topic.data
            cust_name = form.wtf_name.data
            status = book_appointment(
                    phone_number, user_id, apt_time, apt_date, topic, cust_name)
            if status == 'customer_has_appointment':
                return render_template('cancel.html')
            if status == 'appointment_just_booked':
                return redirect(url_for('snap'))
            if status == 'all_good':
                return redirect(url_for('thanks') )                
        else:
            return 'Sorry : did you identify yourself as a human?'

@app.route("/cancel", methods=['POST'])
def cancel():
    """ Cancels the appointment 
    
    This url needs to be linked to the Twilio account
    So that incoming text messages result in post request to this URL
    
    """
    phone_number = request.form['From']
    message_body = request.form['Body']
    if 'no appointment' in message_body.lower():
        cancel_appointments(phone_number)
    return 'cancelled', 200

@app.route('/thanks', methods = ['GET'])
def thanks():
    return render_template('thanks.html')

@app.route('/snap', methods=['GET'])
def snap():
    return render_template('snap.html')

########################## agent-facing interface #############################

login_manager = LoginManager()
login_manager.init_app(app)
#redirects people to login page whenever they need to do the login
login_manager.login_view = '/login' 
# this function makes Login Manager knows how to load users from an ID
@login_manager.user_loader    
def load_user(id):
    return User.query.get(int(id))

class ChangePwdForm(Form):
    user_id = StringField(validators=[DataRequired()])
    old_pwd = StringField('Please enter current password',
                          validators=[DataRequired()])
    new_pwd_1 = StringField('Please enter new password',
                            validators=[DataRequired()])
    new_pwd_2 = StringField('Please re-enter new password',
                            validators=[DataRequired()])

@app.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    """ Home page for the employee.
    
    GET request :   displays all the appointments
                    that can be, cannot be, or have been booked.
                    Employees can view their calendar, 
                    managers the calendars of their location's employees
                    
    POST request :  changes the status of appointmnents
                    from bookable to not bookable ('tbd') and vice versa.
        
    """
    if request.method == 'POST':
        data_list = json.loads(request.form['submit_check_val'])
        toggle_appointments(data_list)
        return redirect(url_for('profile'))

    if request.method == 'GET':
        form = ChangePwdForm()
        if current_user.has_role('admin'):
            return redirect('/admin')
        if current_user.has_role('end-user'):
            data = query_user_appointment(current_user.id)
            return render_template('profile.html', user_record=data, form=form)
        if current_user.has_role('manager'):
            users = (User.query
                .filter_by(branch_id=current_user.branch_id)
                .join(User.roles)
                .filter(Role.id == 2)
                .all())
            data=[query_user_appointment(user.id) for user in users]
            return render_template("manager_profile.html", data=data, form=form)

@app.route("/logout", methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('profile'))

@app.route("/change_password", methods = ['POST'])
@login_required
def change_password():
    form = ChangePwdForm(request.form)
    if form.validate():
        user = User.query.filter(User.id == request.form['user_id']).first()
        if utils.verify_and_update_password(request.form['old_pwd'], user):
            if request.form['new_pwd_1'] == request.form['new_pwd_2']:
                new_password_encrypted = utils.hash_password(request.form['new_pwd_1'])
                user.password = new_password_encrypted
                db.session.commit()
                logout_user()
                return redirect(url_for('profile'))
            return "Sorry, did you input different new passwords?"
        else:
            return "Sorry, is your old password correct?"
    return "Sorry, is there something wring in your information?"

#################### CRON jobs (recurring operations) #########################

@app.route('/cron/add_appointments', methods = ['GET', 'POST'])
def add_appointments():
    """ daily, adds 1 day's worth of appointments to the database """
    users = User.query.join(User.roles).filter(Role.id == 2).all()
    for user in users:
        add_tbd_appointments(user.id)
    return "aloha", 201

@app.route('/cron/send_reminders_hi', methods = ['GET','POST'])
def send_reminders_hi():
    """ daily, sends reminders to the HI customers """
    send_reminder(timezone = 'Pacific/Honolulu')
    return "aloha", 201

@app.route('/cron/send_reminders_wp', methods = ['GET','POST'])
def send_reminders_wp():
    """ daily, sends reminders to the West Pacific customers """
    send_reminder(timezone = 'Pacific/Guam')
    return "aloha", 201
