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
    mapping,
    ExportMapper
)
from .backend import devise


class devise_res_partner(models.Model):
    _name = 'devise.res.partner'
    _inherit = 'external.binding'
    _inherits = {'res.partner': 'openerp_id'}
    _description = 'Devise Partner'

    _rec_name = 'name'

    # openerp_id = openerp-side id must be declared in concrete model
    backend_id = fields.Many2one(
        comodel_name='devise.backend',
        string='Devise Backend',
        required=True,
        ondelete='restrict',
    )
    # fields.Char because 0 is a valid Devise ID
    web_id = fields.Char(string='ID on Devise')
    openerp_id = fields.Many2one(comodel_name='res.partner',
                                 string='Partner',
                                 required=True,
                                 ondelete='restrict')

    _sql_constraints = [
        ('devise_uniq', 'unique(backend_id, web_id)',
         'A binding already exists with the same Devise ID.'),
    ]


class ResPartner(models.Model):
    _inherit = 'res.partner'

    web_bind_ids = fields.One2many(
        comodel_name='devise.res.partner',
        inverse_name='openerp_id',
        string='Devise Bindings',
    )




@devise
class PartnerExportMapper(ExportMapper):
    _model_name = 'devise.res.partner'
# TODO


from openerp.addons.connector.event import on_record_create, on_record_write, on_record_unlink
from .unit.export_synchronizer import export_record
#from .unit.delete_synchronizer import export_delete_record

#@on_record_write(model_names='devise.res.partner')
#def devise_partner_write(session, model_name, record_id):
#    print "devise_partner_write", model_name, fields, record_id
#    export_record.delay(session, model_name, record_id)

@on_record_write(model_names='res.partner')
def partner_write(session, model_name, record_id, fields):
    print "partner_write", model_name, fields, session.context
    if session.context.get('connector_no_export'):
        return

    model = session.pool.get(model_name)
    record = model.browse(session.cr, session.uid,
                           record_id, context=session.context)
    print "bind_ids", record.web_bind_ids

    record_backend_ids = [b.id for b in record.web_bind_ids]
    for backend_id in session.search('devise.backend', []):
        binding_id = False
        for binding in record.web_bind_ids:
            if binding.backend_id == backend_id:
                binding_id = binding.id
                break
        if not binding_id:
            binding = session.env['devise.res.partner'].with_context(connector_no_export=True).create({'backend_id': backend_id, 'openerp_id': record_id})
            binding_id = binding.id

        export_record.delay(session, 'devise.res.partner', binding_id, fields)


# TODO
#@on_record_create(model_names='res.partner')
#def partner_create(session, model_name, record_id):
#    print "partner_create", model_name, record_id
#    export_record.delay(session, model_name, record_id)

#@on_record_unlink(model_names='devise.res.partner')
#def delay_unlink(session, model_name, record_id):
#    export_delete_record.delay(session, model_name, record_id)
