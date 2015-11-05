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

from openerp import models, fields
from openerp.addons.connector.unit.mapper import mapping
from openerp.addons.connector.unit.mapper import (
    ExportMapper
)
from .backend import web
from openerp.addons.connector.event import on_record_create, on_record_write, on_record_unlink
from .unit.export_synchronizer import export_record
from .unit.delete_synchronizer import export_delete_record


class WebResPartner(models.Model):
    _name = 'web.res.partner'
    _inherit = 'external.binding'
    _inherits = {'res.partner': 'openerp_id'}
    _description = 'Web Partner'

    _rec_name = 'name'

    # openerp_id = openerp-side id must be declared in concrete model
    backend_id = fields.Many2one(
        comodel_name='web.backend',
        string='Devise Backend',
        required=True,
        ondelete='restrict',
    )
    # fields.Char because 0 is a valid Devise ID
    external_id = fields.Char(string='ID on Devise')
    openerp_id = fields.Many2one(comodel_name='res.partner',
                                 string='Partner',
                                 required=True,
                                 ondelete='cascade')
    sync_date = fields.Datetime()

    _sql_constraints = [
        ('web_uniq', 'unique(backend_id, external_id)',
         'A binding already exists with the same Devise ID.'),
    ]


class ResPartner(models.Model):
    _inherit = 'res.partner'

    web_bind_ids = fields.One2many(
        comodel_name='web.res.partner',
        inverse_name='openerp_id',
        string='Devise Bindings',
    )


@web
class PartnerExportMapper(ExportMapper):
    _model_name = 'web.res.partner'

    direct = [('email', 'email')]
