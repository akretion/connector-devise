# -*- coding: utf-8 -*-
###############################################################################
#
#   Module for OpenERP
#   Copyright (C) 2015 Akretion (http://www.akretion.com).
#   @author Sébastien BEAU <sebastien.beau@akretion.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp.addons.connector.connector import Binder
from .unit.export_synchronizer import export_record
from .unit.delete_synchronizer import export_delete_record
from .connector import get_environment
from openerp.addons.connector.event import (on_record_write,
                                            on_record_create,
                                            on_record_unlink
                                            )

def delay_export(session, model_name, record_id, vals):
    """ Delay a job which export a binding record.
    (A binding record being a ``web.res.partner``, ...)
    """
    if session.context.get('connector_no_export'):
        return
    fields = vals.keys()
    export_record.delay(session, model_name, record_id, fields=fields)


def delay_export_all_bindings(session, model_name, record_id, vals):
    """ Delay a job which export all the bindings of a record.
    In this case, it is called on records of normal models and will delay
    the export for all the bindings.
    """
    if session.context.get('connector_no_export'):
        return
    record = session.env[model_name].browse(record_id)
    fields = vals.keys()
    for binding in record.web_bind_ids:
        export_record.delay(session, binding._model._name, binding.id,
                            fields=fields)

def delay_unlink(session, model_name, record_id):
    """ Delay a job which delete a record on Devise.
    Called on binding records."""
    record = session.env[model_name].browse(record_id)
    env = get_environment(session, model_name, record.backend_id.id)
    binder = env.get_connector_unit(Binder)
    external_id = binder.to_backend(record_id)
    if external_id:
        export_delete_record.delay(session, model_name,
                                   record.backend_id.id, external_id)

@on_record_write(model_names=[
    'res.partner',
    'web.res.partner',
    ])
def web_partner_write(session, model_name, record_id, vals):
    delay_export_all_bindings(session, model_name, record_id, vals)

@on_record_create(model_names=[
    'web.res.partner',
    ])
def web_partner_create(session, model_name, record_id, vals):
    delay_export(session, model_name, record_id, vals)

@on_record_unlink(model_names=[
    'web.res.partner',
    ])
def web_partner_unlink(session, model_name, record_id):
    delay_unlink(session , model_name, record_id)

