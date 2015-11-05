# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Raphael Valyi
#    Copyright 2015 Akretion
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import os
import requests
from openerp.tools.translate import _
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.synchronizer import Deleter
from ..connector import get_environment
from ..backend import web


@web
class WebDeleter(Deleter):
    _model_name = ['web.res.partner']

    def run(self, external_id):
        payload = {'devise_api_secret': self.backend_record.secret}
        url = "%s/devise_api/destroy/%s.json" % (
            self.backend_record.location.encode('utf-8'),
                                                 external_id)
        requests.post(url, params=payload).json()
        return _('Record %s deleted on Devise') % external_id

@job(default_channel='root.web')
def export_delete_record(session, model_name, backend_id, external_id):
    """ Delete Record in Web """
    env = get_environment(session, model_name, backend_id)
    deleter = env.get_connector_unit(Deleter)
    return deleter.run(external_id)
