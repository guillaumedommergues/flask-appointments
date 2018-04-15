""" Initial data commit """

from my_app import app
from crud import add_tbd_appointments
from data_model import db, Services, Market, Branch, User, Role
from flask_security import Security,SQLAlchemyUserDatastore, utils

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

@app.before_first_request
def before_first_request():

    # Create any database tables that don't exist yet.
    db.create_all()
    db.session.commit()

    # Create the Roles "admin" and "end-user" -- unless they already exist
    user_datastore.find_or_create_role(name='admin', description='Administrator')
    user_datastore.find_or_create_role(name='end-user', description='End user')
    user_datastore.find_or_create_role(name='manager', description='Manager')
    encrypted_password = utils.encrypt_password('pwd')

    # Create the Services
    if not Services.query.filter_by(id=1).first():
        service=Services(name='Deposit Account', id=1)
        db.session.add(service)
        db.session.commit()
    if not Services.query.filter_by(id=2).first():
        service=Services(name='Credit Card', id=2)
        db.session.add(service)
        db.session.commit()
    if not Services.query.filter_by(id=3).first():
        service=Services(name='Other', id=3)
        db.session.add(service)
        db.session.commit()
    if not Services.query.filter_by(id=4).first():
        service=Services(name='Mortgage - new', id=4)
        db.session.add(service)
        db.session.commit()
    if not Services.query.filter_by(id=5).first():
        service=Services(name='Mortgage - refinance', id=5)
        db.session.add(service)
        db.session.commit()

    # Create the Markets
    if not Market.query.filter_by(id=1).first():
        market=Market(name="Guam",id=1)
        db.session.add(market)
        db.session.commit()
    if not Market.query.filter_by(id=2).first():
        market=Market(name="Oahu",id=2)
        db.session.add(market)
        db.session.commit()

    # Create the Branches
    if not Branch.query.filter_by(id=1).first():
        branch=Branch(name="Garapan",market_id=1,time_zone="Pacific/Saipan",address="Spring Plaza, Chalan Pale Arnold, 96950",id=1 )
        db.session.add(branch)
        db.session.commit()
    if not Branch.query.filter_by(id=2).first():
        branch=Branch(name="Kailua",market_id=2,time_zone="Pacific/Honolulu",address="636 KAILUA RD, 96734",id=2)
        db.session.add(branch)
        db.session.commit()
    if not Branch.query.filter_by(id=3).first():
        branch=Branch(name="Kaneohe",market_id=2,time_zone="Pacific/Honolulu",address="45-1001 KAMEHAMEHA HWY, 96744",id=3)
        db.session.add(branch)
        db.session.commit()
    if not Branch.query.filter_by(id=4).first():
        branch=Branch(name="Waikiki",market_id=2,time_zone="Pacific/Honolulu",address="2155 KALAKAUA AVE STE 104, 96815",id=4)
        db.session.add(branch)
        db.session.commit()

    # Create the Users
    # First an admin and a branch manager
    if not user_datastore.get_user('admin@example.com'):
        user_datastore.create_user(email='admin@example.com', password=encrypted_password, name="Admin User")
        user_datastore.add_role_to_user('admin@example.com', 'admin')

    if not user_datastore.get_user('waikiki@example.com'):
        user_datastore.create_user(email='waikiki@example.com', password=encrypted_password, name="Wikiki Manager", branch_id=4)
        user_datastore.add_role_to_user('waikiki@example.com', 'manager')

    # Then regular employees
    if not user_datastore.get_user("john.Garapan@example.com"):
        user_datastore.create_user(email="john.Garapan@example.com", password=encrypted_password, name="John Garapan", branch_id=1, services=Services.query.filter((Services.id==1) | (Services.id==2)  |(Services.id==3)).all() )
        add_tbd_appointments(user_datastore.get_user("john.Garapan@example.com").id)
        user_datastore.add_role_to_user("john.Garapan@example.com", "end-user")

    if not user_datastore.get_user("john.Kailua@example.com"):
        user_datastore.create_user(email="john.Kailua@example.com", password=encrypted_password, name="John Kailua", branch_id=2, services=Services.query.filter((Services.id==1) | (Services.id==2)  |(Services.id==3)).all() )
        add_tbd_appointments(user_datastore.get_user("john.Kailua@example.com").id)
        user_datastore.add_role_to_user("john.Kailua@example.com", "end-user")

    if not user_datastore.get_user("john.Kailua2@example.com"):
        user_datastore.create_user(email="john.Kailua2@example.com", password=encrypted_password, name="John Kailua II", branch_id=2, services=Services.query.filter((Services.id==4) | (Services.id==5)).all() )
        add_tbd_appointments(user_datastore.get_user("john.Kailua2@example.com").id)
        user_datastore.add_role_to_user("john.Kailua2@example.com", "end-user")

    if not user_datastore.get_user("john.kaneohe@example.com"):
        user_datastore.create_user(email="john.kaneohe@example.com", password=encrypted_password, name="John kaneohe", branch_id=3, services=Services.query.filter((Services.id==1) | (Services.id==2)  |(Services.id==3)).all() )
        add_tbd_appointments(user_datastore.get_user("john.kaneohe@example.com").id)
        user_datastore.add_role_to_user("john.kaneohe@example.com", "end-user")

    if not user_datastore.get_user("john.waikiki@example.com"):
        user_datastore.create_user(email="john.waikiki@example.com", password=encrypted_password, name="John waikiki", branch_id=4, services=Services.query.filter((Services.id==1) | (Services.id==2)  |(Services.id==3)).all() )
        add_tbd_appointments(user_datastore.get_user("john.waikiki@example.com").id)
        user_datastore.add_role_to_user("john.waikiki@example.com", "end-user")
    db.session.commit()
