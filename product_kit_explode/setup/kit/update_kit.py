# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP) 
# Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<http://www.micronaet.it>)
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
import erppeek


cfg_file = os.path.expanduser('../odoo.cfg')

try: # Pyton 2.7
    import ConfigParser
    config = ConfigParser.ConfigParser()
except: # Python 3 (pip install ConfigParser)
    import configparser
    config = configparser.ConfigParser()

# -----------------------------------------------------------------------------
# From config file:
# -----------------------------------------------------------------------------
config.read([cfg_file])
dbname = config.get('dbaccess', 'dbname')
user = config.get('dbaccess', 'user')
pwd = config.get('dbaccess', 'pwd')
server = config.get('dbaccess', 'server')
port = config.get('dbaccess', 'port')   # verify if it's necessary: getint
        
# -----------------------------------------------------------------------------
# Connect to ODOO:
# -----------------------------------------------------------------------------
odoo = erppeek.Client(
    'http://%s:%s' % (server, port), 
    db=dbname,
    user=user,
    password=pwd,
    )
product_pool = odoo.model('product.template')

# Update kit check:
kit_product_ids = product_pool.search([
    ('default_code', 'ilike', '#'),
    ('is_kit', '=', False),
    ])
product_pool.write(kit_product_ids, {
    'is_kit': True,
    })

# Update component:
product_ids = product_pool.search([
    ('default_code', 'ilike', '#'),
    ])

log_file = open('./product_not_found.log', 'w')
log_file.write('Kit non generati per codici prodotto mancanti:\n')
i = 0
for product in product_pool.browse(product_ids):
    i += 1
    if i % 50 == 0:
        print('Product updated: %s' % i)
    
    # Lauch button procedure:
    try:
        product.explode_kit_from_name()
    except:
        log_file.write('%s\n' % product.default_code)
log_file.close()
