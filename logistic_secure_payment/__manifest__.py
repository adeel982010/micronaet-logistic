# -*- coding: utf-8 -*-
#!/usr/bin/python
###############################################################################
#
# ODOO (ex OpenERP) 
# Open Source Management Solution
# Copyright (C) 2001-2018 Micronaet S.r.l. (<https://micronaet.com>)
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

{
    'name': 'Secure Payment',
    'version': '1.0',
    'category': 'Sale',
    'sequence': 5,
    'summary': 'Sale, Secure payment',
    #'description': '',
    'website': 'https://micronaet.com',
    'depends': [
        'base',
        'product',
        'account',
        'sale',
        'sales_team',
        ],
    'data': [
        'security/ir.model.access.csv',
        
        'views/secure_payment_view.xml',
        ],
    'demo': [],
    'css': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    }
