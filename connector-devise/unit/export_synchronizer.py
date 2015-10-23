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

import logging
import os

from contextlib import contextmanager
from datetime import datetime

import psycopg2
import requests

import openerp
from openerp.tools.translate import _
from openerp.addons.connector.queue.job import job, related_action
from openerp.addons.connector.unit.synchronizer import Exporter
from openerp.addons.connector.exception import (IDMissingInBackend,
                                                RetryableJobError)
from ..connector import get_environment
#from ..related_action import unwrap_binding

_logger = logging.getLogger(__name__)


"""

Exporters for Devise.

"""


class WebExporter(Exporter):

    def _get_openerp_data(self):
        """ Return the raw OpenERP data for ``self.binding_id`` """
        return self.model.browse(self.binding_id)

    def _after_export(self):
        """ Can do several actions after exporting a record on a Web app """
        pass

    def __init__(self, connector_env):
        """
        :param connector_env: current environment (backend, session, ...)
        :type connector_env: :class:`connector.connector.ConnectorEnvironment`
        """
        super(WebExporter, self).__init__(connector_env)
        self.binding_id = None
        self.binding_record = None

    def _lock(self):
        """ Lock the binding record.

        Lock the binding record so we are sure that only one export
        job is running for this record if concurrent jobs have to export the
        same record.

        When concurrent jobs try to export the same record, the first one
        will lock and proceed, the others will fail to lock and will be
        retried later.

        This behavior works also when the export becomes multilevel
        with :meth:`_export_dependencies`. Each level will set its own lock
        on the binding record it has to export.

        """
        sql = ("SELECT id FROM %s WHERE ID = %%s FOR UPDATE NOWAIT" %
               self.model._table)
        try:
            self.session.cr.execute(sql, (self.binding_id, ),
                                    log_exceptions=False)
        except psycopg2.OperationalError:
            _logger.info('A concurrent job is already exporting the same '
                         'record (%s with id %s). Job delayed later.',
                         self.model._name, self.binding_id)
            raise RetryableJobError(
                'A concurrent job is already exporting the same record '
                '(%s with id %s). The job will be retried later.' %
                (self.model._name, self.binding_id))

    @contextmanager
    def _retry_unique_violation(self):
        """ Context manager: catch Unique constraint error and retry the
        job later.

        When we execute several jobs workers concurrently, it happens
        that 2 jobs are creating the same record at the same time (binding
        record created by :meth:`_export_dependency`), resulting in:

            IntegrityError: duplicate key value violates unique
            constraint "magento_product_product_openerp_uniq"
            DETAIL:  Key (backend_id, openerp_id)=(1, 4851) already exists.

        In that case, we'll retry the import just later.

        .. warning:: The unique constraint must be created on the
                     binding record to prevent 2 bindings to be created
                     for the same Magento record.

        """
        try:
            yield
        except psycopg2.IntegrityError as err:
            if err.pgcode == psycopg2.errorcodes.UNIQUE_VIOLATION:
                raise RetryableJobError(
                    'A database error caused the failure of the job:\n'
                    '%s\n\n'
                    'Likely due to 2 concurrent jobs wanting to create '
                    'the same record. The job will be retried later.' % err)
            else:
                raise

    def _map_data(self):
        """ Returns an instance of
        :py:class:`~openerp.addons.connector.unit.mapper.MapRecord`

        """
        return self.mapper.map_record(self.binding_record)

    def _validate_create_data(self, data):
        """ Check if the values to import are correct

        Pro-actively check before the ``Model.create`` if some fields
        are missing or invalid

        Raise `InvalidDataError`
        """
        return

    def _validate_update_data(self, data):
        """ Check if the values to import are correct

        Pro-actively check before the ``Model.update`` if some fields
        are missing or invalid

        Raise `InvalidDataError`
        """
        return


class DeviseExporter(WebExporter):

    def run(self, binding_id, fields=None):
        """ Flow of the synchronization, implemented in inherited classes"""
        self.binding_id = binding_id
        binding = self.model.browse(self.binding_id)
        partner = binding.openerp_id
        if not partner.email:
            return

        # prevent other jobs to export the same record
        # will be released on commit (or rollback)
        self._lock()
        payload = {'email': partner.email, 'devise_api_secret': os.environ['DEVISE_API_SECRET']}
        if binding.web_id:
            url = "%s/devise_api/update/%s.json" % (self.backend_record.location.encode('utf-8'), binding.web_id)
            requests.post(url, params=payload).json()
        else:
            url = "%s/devise_api/create.json" % (self.backend_record.location.encode('utf-8'),)
            res = requests.post(url, params=payload).json()
            binding.write({'web_id': res})
        return _('Record exported with ID %s on Devise.') % res


@job(default_channel='root.devise')
def export_record(session, model_name, binding_id, fields=None):
    """ Export a record on Devise """
    record = session.env[model_name].browse(binding_id)
    for backend_id in session.env['devise.backend'].search([]):
        env = get_environment(session, model_name, backend_id.id)
#       exporter = env.get_connector_unit(DeviseExporter)
        exporter = DeviseExporter(env)
        res = exporter.run(binding_id, fields=fields)
    return res
