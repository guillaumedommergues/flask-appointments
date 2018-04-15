""" Functions that involve querying the database, called from views.py """

from datetime import datetime, timedelta, time
from data_model import db, Branch, User, Appointment, Market
from data_model import Services, users_services
from communications import create_ics_file, send_outlook_invite, send_sms
from operator import attrgetter
import pytz

############################# Queries #########################################

def query_available_services(days_available):
    """ Returns the list of all services that can be booked."""
    today = datetime.now(pytz.timezone('Pacific/Honolulu')).date()
    available_services = (Services.query.distinct()
        .join(users_services)
        .join(User)
        .join(Appointment)
        .filter(Appointment.bookable_booked=='bookable')
        .filter(Appointment.date >today)
        .filter(Appointment.date <= today + timedelta (days=days_available))
        .all())
    available_services = [service.name for service in available_services]
    available_services.sort()
    return available_services

def query_available_markets(days_available, what):
    """ Returns the list of all markets where appointments can be booked."""
    today = datetime.now(pytz.timezone('Pacific/Honolulu')).date()
    available_locations = (Market.query.distinct()
                            .with_entities(Market.name)
                            .join(Branch)
                            .join(User)
                            .join(users_services)
                            .join(Appointment)
                            .filter(Appointment.bookable_booked=='bookable')
                            .filter(Appointment.date >today)
                            .join(Services)
                            .filter(Services.name == what)
                            .all())
    available_locations = [mkt.name for mkt in available_locations]
    available_locations.sort()
    return available_locations

def query_available_days(what, where, days_available):
    """ Returns the list of all days when appointments can be booked."""
    today = datetime.now(pytz.timezone('Pacific/Honolulu')).date()
    available_days = (Appointment.query
                        .distinct()
                        .filter(Appointment.bookable_booked=='bookable')
                        .filter(Appointment.date >today)
                        .join(User)
                        .join(users_services)
                        .join(Services)
                        .filter(Services.name == what)
                        .join(Branch)
                        .join(Market)
                        .filter(Market.name == where)
                        .all())        
    available_days = [apt.date.strftime('%Y-%m-%d') for apt in available_days]
    available_days = list(set(available_days))
    available_days.sort()
    return available_days

def find_relevant_days(day_picked, time_zone):
    """ Returns the first and last day to show the customer
    when booking appointment,
    The application shows days around the day chosen by the customer
    to increase the level of choice
    """
    first_apt_day = datetime.now(pytz.timezone(time_zone)).date() + timedelta(days=1)
    last_apt_day = first_apt_day + timedelta(days=13)
    if (day_picked - timedelta(days=2))< first_apt_day:
        start_query_date = first_apt_day
        end_query_date = start_query_date+timedelta(days=4)
    elif (day_picked + timedelta(days=2))>= last_apt_day:
        end_query_date = last_apt_day
        start_query_date = end_query_date - timedelta(days=4)
    else:
        start_query_date = day_picked - timedelta(days=2)
        end_query_date = day_picked + timedelta(days=2)
    return start_query_date, end_query_date

def query_market_appointments(what, where, when):
    """ Returns available appointments for a full market"""
    branches = (Branch.query
                    .join(Market)
                .filter(Market.name==where)
                .join(User)
                .join(User.services)
                .filter(Services.name==what)
                .all())
    time_zone=branches[0].time_zone
    selected_date=datetime.strptime(when, '%Y-%m-%d').date()
    start, stop = find_relevant_days(selected_date, time_zone=time_zone)
    data = [query_branch_appointment(branch, what, start, stop)
            for branch in branches]
    return data

def query_user_appointment(user_id, start_query_date=None, end_query_date=None):
    """returns the appointments of one agent
    in a way that is easy to use for the front end
    ie a dictionary with:
    user_id
    user_branch_name
    user_branch_address
    user_apt: a list of list of user appointment 
    user_apt_days: a list of all the days for which we have an appointment
    """
    user = User.query.filter_by(id=user_id).join(User.branch).first()
    if start_query_date and end_query_date:
        appointments = (Appointment.query.
                            filter_by(user_id=user.id).
                            filter(Appointment.date >=start_query_date).
                            filter(Appointment.date <=end_query_date).
                            order_by(Appointment.time.asc()).
                            all())
    else:
        time_zone = user.branch.time_zone
        today = datetime.now(pytz.timezone(time_zone)).date()
        appointments = (Appointment.query.
                            filter_by(user_id=user.id).
                            filter(Appointment.date >=today).
                            order_by(Appointment.time.asc()).
                            all())
        if not appointments:
            #checkpoint 1: the user has some appointments (ie not just added)
            add_tbd_appointments(user_id)
            appointments = (Appointment.query.
                                filter_by(user_id=user.id).
                                filter(Appointment.date >=today).
                                order_by(Appointment.time.asc()).
                                all())
    user_apt=[]
    user_apt_days=list(set([appointment.date for appointment in appointments]))
    user_apt_days.sort()
    user_apt_times=list(set([appointment.time for appointment in appointments]))
    user_apt_times.sort()
    for my_time in user_apt_times:
        user_apt.append(sorted([appointment for appointment in appointments if appointment.time==my_time],
                               key=attrgetter('date')))
    data={'user': user.name,
    'user_id': user.id,
    'user_apt':user_apt,
    'user_apt_days':user_apt_days,
    'user_branch_name':user.branch.name,
    'user_branch_address':user.branch.address }
    return data

def query_branch_appointment(branch, what, start_query_date, end_query_date):
    """returns the appointments of one branch
    in a way that is easy to use for the front end
    selecting a 'bookable' appointment for a specific time slot if possible
    ie a dictionary with:
    user_id
    user_branch_name
    user_branch_address
    user_apt: a list of list of user appointment 
    user_apt_days: a list of all the days for which we have an appointment
    """
    bookable_apt = (Appointment.query.
                join(User).
                filter(User.branch_id == branch.id).
                filter(Appointment.date >= start_query_date).
                filter(Appointment.date <= end_query_date).
                filter(Appointment.bookable_booked == 'bookable').
                join(users_services).
                join(Services).
                filter(Services.name == what).
                all())
    branch_apt_days=sorted(list(set([x.date for x in bookable_apt])))
    branch_apt_times=sorted(list(set([x.time for x in bookable_apt])) )
    branch_apt=[]
    for hour in branch_apt_times:
        my_apt=[]
        # for day in branch_apt_days:
        for day in branch_apt_days:
            try:
                first_bookable_apt=next(x for x in bookable_apt if
                                        (x.date==day) and (x.time==hour))
                my_apt.append(first_bookable_apt)
            except:
                my_apt.append(None)
        branch_apt.append(my_apt)
    data={'branch': branch.name,
    'branch_id': branch.id,
    'branch_apt':branch_apt,
    'branch_apt_days':branch_apt_days,
    'branch_address':branch.address }
    return data

def phone_has_appointment(phone_number):
    """ Returns the future appointment attached to the phone number
    if any. Else returns None. 
    
    """
    today = datetime.now().date()
    appointment = Appointment.query\
    .filter(Appointment.booked_by_phone == phone_number)\
    .filter(Appointment.date >today).first()
    return appointment
 
def toggle_appointments(data_list):
    for data in data_list:
        data_date = datetime.strptime(data['date'],"%Y-%m-%d").date()
        data_time = datetime.strptime(data['time'],"%H:%M:%S").time()
        data_user_id = data['user_id']
        data_status = data['status']
        appointment_to_toggle = Appointment.query.filter_by(date = data_date,
                                            time=data_time,
                                            bookable_booked=data_status,
                                            user_id=data_user_id).first()
        if data_status == "tbd":
            appointment_to_toggle.bookable_booked = "bookable"
        else:
            appointment_to_toggle.bookable_booked = "tbd"
        db.session.commit()
    return

def add_tbd_appointments(user_id):
    """ Adds new bookable appointments to the database for each agent."""
    today=datetime.today()
    for i in range(0,15):
        current_date=today+timedelta(days=i)
        current_date=current_date.date()
        for j in range (8,16):
            current_hour=time(j, 00)
            is_there_appointment=Appointment.query.filter_by(user_id=user_id,
                                                    time=current_hour,
                                                    date=current_date).first()
            if is_there_appointment:
                pass
            else:
                new_appointment=Appointment(date=current_date,
                                            time=current_hour,
                                            booked_at= None,
                                            bookable_booked="bookable",
                                            topic="topic",
                                            booked_by_name=None,
                                            booked_by_phone=None,
                                            user_id=user_id )
                db.session.add(new_appointment)
                db.session.commit()
    return

###################### High level functions ###################################

def create_appointment(appointment, phone_number, topic, booked_by_name):
    """ Takes necessary actions when a customer books an appointment, ie
    update the database,
    sends an email to the agent, 
    sends a text message to the customer
    """
    #step 1 - update the database with the client info
    appointment.bookable_booked = "booked"
    appointment.booked_by_phone = phone_number
    appointment.topic = topic
    appointment.booked_by_name = booked_by_name
    appointment.booked_at = datetime.now()
    db.session.commit()
    # "step 2 - send invite to user via email (ics file)"
    ics_file, ics_file_name = create_ics_file(
            _appointment=appointment,
            _ics_method='PUBLISH')
    send_outlook_invite(
            filename=ics_file_name,
            recepient=appointment.user.email,
            ics_file=ics_file,
            invite_method='PUBLISH')
    # "step 3 - confirm appointment to client via SMS"
    send_sms(appointment, sms_method='PUBLISH')
    return

def cancel_appointments(phone_number):
    """ Takes necessary actions when a customer cancels an appointment, ie
    sends an email to the agent, 
    sends a text message to the customer
    updates the database
    """
    #step 1 - find all the client's appointments
    today=datetime.now().date()
    appointments = (Appointment.query
                    .filter(Appointment.booked_by_phone == phone_number)
                    .filter(Appointment.date >=today)
                    .join(Appointment.user)
                    .join(User.branch)
                    .all())
    for appointment in appointments:
        # "step 2 - send cancellations to employee via email (ics file)"
        ics_file, ics_file_name=create_ics_file(
                                    _appointment=appointment,
                                    _ics_method="CANCEL")
        send_outlook_invite(
                 filename=ics_file_name,
                 recepient=appointment.user.email,
                 ics_file=ics_file,
                 invite_method='CANCEL')

        # "step 3 - confirm cancellation to client via SMS"
        send_sms(appointment, sms_method='CANCEL')

        #"step 4 - update the database"
        appointment.bookable_booked ='bookable'
        appointment.booked_by_name = None
        appointment.booked_by_phone = None
        appointment.booked_at = None
        appointment.topic = None
        db.session.commit()
    return

def book_appointment(phone_number, user_id, apt_time, apt_date, topic, name):
    """ Tries to book an appointment and return booking status
    status 'customer_has_appointment':
        self explanatory
    status 'appointment_just_booked':
        another customer just booked the appointment
    status 'all_good':
        the appointment has been booked, ie the employee was notified,
        the database was updated, the text confirmation was sent.
    
    """
    phone_number = "+1"+str(phone_number)
    today = datetime.now().date()
    appointment = (Appointment.query
        .filter(Appointment.booked_by_phone == phone_number)
        .filter(Appointment.date >today).first())
    if appointment is not None:
        return 'customer_has_appointment'
    else:
        appointment = (Appointment.query
                .filter_by(user_id=user_id, time=apt_time, date=apt_date)
                .join(Appointment.user)
                .join(User.branch)
                .first())
        if appointment.bookable_booked != "bookable":
            return 'appointment_just_booked'
        else:
            create_appointment(appointment, phone_number, topic, name)
            return 'all_good'
