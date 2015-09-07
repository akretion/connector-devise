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

import requests
from openerp.tools.translate import _
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.synchronizer import Deleter
from ..connector import get_environment


class DeviseDeleter(Deleter):

    def run(self, web_id):
        url = "%s/devise_api/destroy/%s.json" % (self.backend_record.location.encode('utf-8'), web_id)
        requests.post(url).json()
        return _('Record %s deleted on Devise') % web_id

@job(default_channel='root.devise')
def export_delete_record(session, model_name, backend_id, devise_id):
    env = get_environment(session, model_name, backend_id)
#    deleter = env.get_connector_unit(MagentoDeleter)
    deleter = DeviseDeleter(env)
    return deleter.run(devise_id)
