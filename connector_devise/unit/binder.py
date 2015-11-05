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

import openerp
from openerp.addons.connector.connector import Binder
from ..backend import web


@web
class WebBinder(Binder):
    """
    Bindings are done directly on the binding model.

    Binding models are models called ``web.{normal_model}``,
    like ``web.res.partner``.
    They are ``_inherits`` of the normal models and contains
    the Devise ID, the ID of the Devise Backend and the additional
    fields belonging to the Devise instance.
    """
    _model_name = [
        'web.res.partner',
    ]
