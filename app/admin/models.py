""" ADMIN MODELS"""
from app.core.models import BaseModel


class Admin(object):
    """ Ito yung mga functions sa dropdown ng model sa admin page sidebar (eg. Create new, View all)
    """
    __amfunctions__ = None
    
    """ Ito yung icon sa admin page (eg. pe-7s-users).
    Refer sa dashboardpack.com sa mga available icons
    """
    __amicon__ = ""
    
    __view_url__ = 'bp_admin.no_view_url'

    __parent_model__ = None

    @property
    def __amname__(self):
        """ Ito yung parang code nya(eg. auth) for authentication.
        Ito yung reference mo sa model sa mga code mo wag yung description
        Ex. if model.__amcode__ = 'auth': 
        """
        raise NotImplementedError('Must implement admin-model name')

    @property
    def __amdescription__(self):
        """ Ito ung visible sa admin page(eg. Authentication)
        """
        raise NotImplementedError('Must implement admin-model description')


# class AdminUserOptions(BaseModel):
#     from app.auth.models import User

#     user: User
#     header_color: str
#     sidebar_color: str

class AdminDashboard(Admin):
    __amname__ = 'admin_dashboard'
    __amdescription__ = 'Admin Dashboard'
    __amicon__ = 'pe-7s-graph1'
    __view_url__ = 'bp_admin.dashboard'


class AdminApp(Admin):
    __amname__ = 'admin_app'
    __amdescription__ = 'Apps'
    __amicon__ = 'pe-7s-graph1'
    __view_url__ = 'bp_admin.apps'

