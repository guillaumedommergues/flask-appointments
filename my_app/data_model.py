""" Specification of the data model """


from my_app import app
from flask_sqlalchemy import SQLAlchemy
from flask_security import RoleMixin, UserMixin

############################ Defining Tables ##########################################

db = SQLAlchemy(app)

# Helper tables for many-to-many relationshipss
# for Users-Role and Users-Services
roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)

users_services = db.Table(
    'users_services',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('services_id', db.Integer(), db.ForeignKey('services.id'))
)

# Other tables 
class Role(db.Model, RoleMixin):
    """ admin, user, or manager """
    # Our Role has three fields, ID, name and description
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))
    # __str__ is required by Flask-Admin
    # so we can have human-readable values for the Role when editing a User
    def __str__(self):
        return self.name
    # __hash__ is required to avoid the exception TypeError: unhashable 
    # type: 'Role' when saving a User
    def __hash__(self):
        return hash(self.name)

class User(db.Model, UserMixin):
    """ Defines the employees
    linked to a role, a branch, one or several services and appointments
    
    """
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=False)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    name = db.Column(db.String(120), unique=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'))
    branch=db.relationship('Branch', backref=db.backref('branch'))
    roles = db.relationship('Role',
                            secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
    services = db.relationship('Services',
                               secondary=users_services,
                               backref=db.backref('services', lazy='dynamic'))
    def __repr__(self):
        return self.name

class Branch(db.Model):
    """ Defines the branches
    linked to a market, one or several users or managers
    
    """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    address = db.Column(db.String(240), nullable=False)
    time_zone = db.Column(db.String(120), nullable=False)
    market_id=db.Column(db.Integer, db.ForeignKey('market.id'))
    market=db.relationship('Market', backref=db.backref('market'))
    def __str__(self):
        return self.name

class Market(db.Model):
    """ Defines the market
    linked to one or several branches
    
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    def __str__(self):
        return self.name

class Services(db.Model):
    """ Defines the market
    linked to one or several users
    
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    def __str__(self):
        return self.name

class Appointment(db.Model):
    """ Defines the appointments
    linked to one or several users
    
    """
    id = db.Column(db.Integer, primary_key=True)
    date= db.Column(db.Date)
    time= db.Column(db.Time)
    bookable_booked = db.Column(db.String(120))
    booked_at= db.Column(db.DateTime)
    topic = db.Column(db.String(120))
    booked_by_name = db.Column(db.String(120))
    booked_by_phone = db.Column(db.String(120))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('user'))
    def __repr__(self):
        return ('<Appointment with  %s and on %s at %s >'
                % (self.user_id, self.date, self.time))

