from openerp import http
from openerp.http import request
from openerp.addons.web.controllers.main import Session


class DeviseSession(Session):

    @http.route('/web/session/authenticate', type='json', auth="none")
    def authenticate(self, db, login, password, base_location=None):
        if isinstance(base_location, dict):
            request.session['web_email'] = base_location.get('email')
        return super(DeviseSession, self).authenticate(db, login, password,
                                                       base_location)
