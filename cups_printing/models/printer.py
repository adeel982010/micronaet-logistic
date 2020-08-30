#!/usr/bin/python
# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP) 
# Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<https://micronaet.com>)
# Developer: Nicola Riolini @thebrush (<https://it.linkedin.com/in/thebrush>)
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import os
import sys
import logging
import odoo
from odoo import api, fields, models, tools, exceptions, SUPERUSER_ID
from odoo.addons import decimal_precision as dp
from odoo.tools.translate import _


_logger = logging.getLogger(__name__)

class CupsPrinter(models.Model):
    """ Model name: CUPS Printer
    """
    _name = 'cups.printer'
    _description = 'Description'

    
    name = fields.Char('CUPS Printer', size=64)
    code = fields.Char('Code', size=10, help='For fast reference')
    note = fields.Text('Note')
    options = fields.Char('CUPS Options', size=100)
    

class ResUsers(models.Model):
    """ Model name: User parameter
    """
    _inherit = 'res.users'

    default_printer_id = fields.Many2one(
        'cups.printer', 'Default Printer')

class ResCompany(models.Model):
    """ Model name: User parameter
    """
    _inherit = 'res.company'

    default_printer_id = fields.Many2one(
        'cups.printer', 'Default Printer')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
