""" Creation of the admin pages """

from my_app import app
from data_model import db, Branch, User, Appointment, Market, Services
from wtforms import PasswordField
from flask_admin import Admin, expose, AdminIndexView
from flask_admin.contrib import sqla
from flask_login import current_user
from flask_security import utils

############################# Customization ###################################

class IndexView(AdminIndexView):
    """ Puts custom index.html the root of the admin page """
    @expose('/')
    def index(self):
        return self.render('admin/index.html')

class ProtectedAdmin(sqla.ModelView):
    """ Renders ProtectedAdmin visible to authenticated admin only """
    page_size = 100
    def is_accessible(self):
        if current_user.is_authenticated:
            return current_user.has_role('admin')
        return None

class BranchAdmin(ProtectedAdmin):
    """ Customizes the Branch Admin Interface.
    In particular, restricts the time zones to pytz strings
    
    """
    form_excluded_columns = ('branch')
    column_searchable_list = ('name', 'address','market.name')
    form_choices = {'time_zone': [('Pacific/Honolulu', 'Pacific/Honolulu'),
        ('Pacific/Guam', 'Pacific/Guam'),
        ('Pacific/Samoa','Pacific/Samoa'),
        ('Pacific/Palau','Pacific/Palau'),
        ('Pacific/Saipan','Pacific/Saipan')]}

class MarketAdmin(ProtectedAdmin):
    form_excluded_columns = ('market')

class ServicesAdmin(ProtectedAdmin):
    pass

class AppointmentAdmin(ProtectedAdmin):
    """ Customizes the Branch Admin Interface.
    In particular, appointments cannot be deleted - just updated.
    
    """
    column_filters = ('date', 'time','user.name')
    form_excluded_columns = ('appointment')
    can_create = False
    can_delete = False

class UserAdmin(ProtectedAdmin):
    """ Customizes the Branch Admin Interface.
    In particular, makes sure that passwords are hashed on change
    
    """
    column_exclude_list = ['password', 'active']
    column_searchable_list = ('name', 'email')
    form_excluded_columns = ('password','active', 'user' )
    column_auto_select_related = True
    def scaffold_form(self):
        # Create a new form_class 
        form_class = super(UserAdmin, self).scaffold_form()
        # Add a password field
        form_class.password2 = PasswordField('New Password')
        return form_class
    # when a change happens...
    def on_model_change(self, form, model, is_created):
        # ... if the password field isn't blank...
        if len(model.password2):
            # ... then encrypt the new password and save it
            model.password = utils.encrypt_password(model.password2)
        # .. and make the user must be active if this is not the case
        model.active=True

########################### Initialization ###################################

admin = Admin(app, index_view=IndexView())
admin.add_view(UserAdmin(User, db.session))
admin.add_view(BranchAdmin(Branch, db.session))
admin.add_view(MarketAdmin(Market, db.session))
admin.add_view(AppointmentAdmin(Appointment, db.session))
admin.add_view(ServicesAdmin(Services, db.session))


