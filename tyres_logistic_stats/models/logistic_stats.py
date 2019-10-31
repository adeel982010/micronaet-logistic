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
import shutil
import requests
import base64
from odoo import api, fields, models, tools, exceptions, SUPERUSER_ID
from odoo.addons import decimal_precision as dp
from odoo.tools.translate import _

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


_logger = logging.getLogger(__name__)

class SaleOrderStats(models.Model):
    """ Model name: Sale Order
    """

    _inherit = 'sale.order'

    # -------------------------------------------------------------------------
    #                           BUTTON EVENTS:
    # -------------------------------------------------------------------------
    @api.multi
    def sale_order_refresh_margin_stats(self):    
        ''' Update margin data:
        '''
        def get_net(line):
            ''' Extract net price
            '''
            # TODO
            return line.price_unit

        self.ensure_one()
        
        # Statistic data:
        amount_untaxed = self.amount_untaxed
        payment_fee = self.mmac_payment_transaction_fee
        marketplace_fee = self.mmac_marketplace_transaction_fee

        transport = pfu = purchase = 0.0
        detail_block = {
            'pfu': '',
            'transport': '',
            'purchase': '',
            }
        
        for line in self.order_line:
            # -----------------------------------------------------------------
            # PFU article
            # -----------------------------------------------------------------
            if line.product_id.default_code == 'PFU':
                price = get_net(line)
                subtotal = (price * line.product_uom_qty)
                detail_block['pfu'] += '%s x %s = %s<br/>' % (
                    line.product_uom_qty,
                    price,
                    subtotal,
                    )
                pfu += subtotal
                continue
            
            # -----------------------------------------------------------------
            # Transport article
            # -----------------------------------------------------------------
            if line.product_id.default_code == 'TRASPORTO':
                price = get_net(line)
                subtotal = (price * line.product_uom_qty)
                detail_block['pfu'] += '%s x %s = %s<br/>' % (
                    line.product_uom_qty,
                    price,
                    subtotal,
                    )
                transport += subtotal
                continue
            
            # -----------------------------------------------------------------
            # Purchase cost:
            # -----------------------------------------------------------------
            for purchase_line in line.purchase_line_ids:                
                price = purchase_line.price_unit # TODO get_net(line)?
                subtotal = (price * purchase_line.product_qty)
                detail_block['purchase'] += '%s x %s = %s<br/>' % (
                    purchase_line.product_qty,
                    price,
                    subtotal,
                    )                    
                purchase += subtotal
                continue
        
        margin = amount_untaxed - payment_fee - marketplace_fee - transport - \
            pfu - purchase

        if amount_untaxed:    
            margin_rate = 100.0 * (margin / amount_untaxed)
        else:
            margin_rate = 0.0    
        
        if margin > 0.0:
            level = 'positive'
        elif not margin:
            level = 'neutral'
        else:
            level = 'negative'

        # ---------------------------------------------------------------------
        # Log Detail:
        # ---------------------------------------------------------------------        
        detail = _('Total sold untaxed: <b>%s</b><br/>') % amount_untaxed
        
        detail += _('- Payment fee: <b>%s</b><br/>') % payment_fee
        detail += _('- Marketplace fee: <b>%s</b><br/>') % marketplace_fee

        if detail_block['transport']: 
            detail += _('- Transport: <b>%s</b><br/><i>%s</i><br/>') % (
                transport,
                detail_block['transport'],
                )

        if detail_block['pfu']: 
            detail += _('- PFU: <b>%s</b><br/><i>%s</i><br/>') % (
                pfu,
                detail_block['pfu'],
                )

        if detail_block['purchase']: 
            detail += _('- Purchase: <b>%s</b><br/><i>%s</i><br/>') % (
                purchase,
                detail_block['purchase'],
                )

        detail += _('= Margin: <b>%s</b> >> %s %%<br/>') % (
            margin,
            margin_rate,
            )

        detail += _('Sale result: <b>%s</b><br/>') % level
        
        
        # Update record with statistic:    
        self.write({
            'stat_sale': amount_untaxed,
            # payment_fee
            # marketplace_fee
            'stat_pfu': pfu,
            'stat_transport': transport,
            'stat_purchase': purchase,
            'stat_margin': margin,
            'stat_margin_rate': margin_rate,
            'stat_level': level,
            'stat_detail': detail,
            })    
        return True
        
    # -------------------------------------------------------------------------
    #                               COLUMNS:
    # -------------------------------------------------------------------------
    stat_sale = fields.Float('Sale net', digits=(16, 2))  
    # payment_fee
    # marketplace_fee
    stat_pfu = fields.Float('PFU Total', digits=(16, 2))  
    stat_transport = fields.Float('Transport total', digits=(16, 2))  
    stat_purchase = fields.Float('Purchase total', digits=(16, 2))  
    stat_margin = fields.Float('Margin', digits=(16, 2))  
    stat_margin_rate = fields.Float('Margin rate', digits=(16, 2))  
    stat_detail = fields.Text('Sale detail')  
    stat_level = fields.Selection([
        ('unset', 'Not present'),
        ('negative', 'Negative'),
        ('neutral', 'Neutral'),
        ('positive', 'Positive'),
        ], 'Margin level', default='unset',
        )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
