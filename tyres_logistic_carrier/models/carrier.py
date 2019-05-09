#!/usr/bin/python
# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2001-2018 Micronaet S.r.l. (<https://micronaet.com>)
#    Developer: Nicola Riolini @thebrush 
#               (<https://it.linkedin.com/in/thebrush>)
#    Copyright (C) 2014 Abstract (http://www.abstract.it)
#    @author Davide Corio <davide.corio@abstract.it>
#    Copyright (C) 2014 Agile Business Group (http://www.agilebg.com)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import os
import sys
import logging
from odoo import fields, models, api
from odoo import _


_logger = logging.getLogger(__name__)


class CarrierSupplier(models.Model):
    """ Model name: Parcels supplier
    """
    
    _name = 'carrier.supplier'
    _description = 'Parcel supplier'
    _rec_name = 'name'
    
    # -------------------------------------------------------------------------
    #                                   COLUMNS:
    # -------------------------------------------------------------------------
    name = fields.Char('Name')

class CarrierParcelTemplate(models.Model):
    """ Model name: Parcels template
    """
    
    _name = 'carrier.parcel.template'
    _description = 'Parcel template'
    _rec_name = 'name'
    
    # -------------------------------------------------------------------------
    #                                   COLUMNS:
    # -------------------------------------------------------------------------
    name = fields.Char('Name')
    length = fields.Float('Length', digits=(16, 2), required=True)
    width = fields.Float('Width', digits=(16, 2), required=True)
    height = fields.Float('Height', digits=(16, 2), required=True)
    dimension_uom_id = fields.Many2one('product.uom', 'Product UOM')

    weight = fields.Float('Weight', digits=(16, 2), required=True)
    weight_uom_id = fields.Many2one('product.uom', 'Product UOM')

class SaleOrderParcel(models.Model):
    """ Model name: Parcels for sale order
    """
    
    _name = 'sale.order.parcel'
    _description = 'Sale order parcel'
    _rec_name = 'weight'
    
    # -------------------------------------------------------------------------
    #                                   COLUMNS:
    # -------------------------------------------------------------------------
    order_id = fields.Many2one('sale.order', 'Order')
    
    # Dimension:
    length = fields.Float('Length', digits=(16, 2), required=True)
    width = fields.Float('Width', digits=(16, 2), required=True)
    height = fields.Float('Height', digits=(16, 2), required=True)
    order_id = fields.Many2one('sale.order', 'Order')    
    dimension_uom_id = fields.Many2one('product.uom', 'Product UOM')
    
    # Weight:
    weight = fields.Float('Weight', digits=(16, 2), required=True)
    weight_uom_id = fields.Many2one('product.uom', 'Product UOM')
    
class SaleOrder(models.Model):
    """ Model name: Sale order carrier data
    """
    
    _inherit = 'sale.order'
    
    @api.multi
    def load_template_parcel(self, ):
        ''' Load this template
        '''
        parcel_pool = self.env['sale.order.parcel']
        template = self.carrier_parcel_template_id
        
        parcel_pool.create({
            'order_id': self.id,
            'length': template.length,
            'width': template.width,
            'height': template.height,

            'weight': template.weight,            
            })
        return True

    # -------------------------------------------------------------------------
    #                                   COLUMNS:
    # -------------------------------------------------------------------------
    carrier_supplier_id = fields.Many2one(
        'carrier.supplier', 'Supplier')
    carrier_parcel_template_id = fields.Many2one(
        'carrier.parcel.template', 'Parcel template')
    carrier_description = fields.Text('Carrier description')
    carrier_note = fields.Text('Carrier note')
    carrier_stock_note = fields.Text('Stock operator note')
    carrier_total = fields.Float('Goods value', digits=(16, 2))
    carrier_ensurance = fields.Float('Ensurance', digits=(16, 2))
    carrier_cash_delivery = fields.Float('Cash on delivery', digits=(16, 2))
    carrier_pay_mode = fields.Selection([
        ('cash', 'Cash'),
        ], 'Pay mode', default='cash')
    #carrier_incoterm = fields.selection([
    #    ('dap', 'DAP'),
    #    ], 'Pay mode', default='dap')
    parcel_ids = fields.One2many('sale.order.parcel', 'order_id', '')

    # From Carrier:
    carrier_cost = fields.Float('Cost', digits=(16, 2))
    carrier_track_id = fields.Char('Track ID', size=64)
    # TODO extra data needed!

