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

class SaleOrderCarrierCheckWizard(models.TransientModel):
    """ Model name: Order carrier check
    """
    _name = 'sale.order.carrier.check.wizard'
    _description = 'Carrier check wizard'
    
    # -------------------------------------------------------------------------
    #                            COLUMNS:
    # -------------------------------------------------------------------------    
    carrier_id = fields.Many2one('carrier.supplier', 'Carrier Supplier')
    mode_id = fields.Many2one('carrier.supplier.mode', 'Mode')
    from_date = fields.Date('From date >=', required=True)
    to_date = fields.Date('To date <', required=True)
    only_shippy = fields.Boolean('Shippy only', default=True)
    # -------------------------------------------------------------------------    

    @api.multi
    def extract_excel_report(self, ):
        ''' Extract Excel report
        '''
        order_line_pool = self.env['sale.order.line']
        excel_pool = self.env['excel.writer']
        
        from_date = self.from_date
        to_date = self.to_date
        carrier = self.carrier_id
        mode = self.mode_id
        
        domain = [
            # Header
            ('order_id.date_order', '>=', from_date),
            ('order_id.date_order', '>=', to_date),
            ]

        if carrier:
            domain.append(
                ('order.carrier_supplier_id', '=', carrier.id),
                )
        if mode:
            domain.append(
                ('order.carrier_mode_id', '=', mode.id),
                )
        if only_shippy:
            domain.append(
                ('order.carrier_shippy', '=', True),
                )

        # ---------------------------------------------------------------------
        #                           Collect data:
        # ---------------------------------------------------------------------
        # A. All stock move sale
        supplier_category_move = {}
        for move in move_pool.search(domain):            
            supplier = move.delivery_id.supplier_id
            category = move.product_id.mmac_pfu.name or ''
            if not category: # Missed category product not in report
                continue
            
            if supplier not in supplier_category_move:
                supplier_category_move[supplier] = {}
                
            if category not in supplier_category_move[supplier]:
                supplier_category_move[supplier][category] = []

            supplier_category_move[supplier][category].append(move)

        # ---------------------------------------------------------------------
        #                          EXTRACT EXCEL:
        # ---------------------------------------------------------------------
        # Excel file configuration:
        header = ('RAEE', 'Cod. Articolo', 'Descrizione', u'Q.tà', 
            'Doc Fornitore', 'Data Doc.', 'N. Fattura', 'N. Nostra fattura', 
            'Data Doc.', 'ISO stato')
            
        column_width = (
            5, 15, 45, 5, 
            15, 12, 12, 15, 
            10, 8,
            )    

        # ---------------------------------------------------------------------
        # Write detail:
        # ---------------------------------------------------------------------        
        setup_complete = False # For initial setup:
        for supplier in sorted(supplier_category_move, key=lambda x: x.name):
            ws_name = supplier.name.strip()
            
            # -----------------------------------------------------------------
            # Excel sheet creation:
            # -----------------------------------------------------------------
            excel_pool.create_worksheet(ws_name)
            excel_pool.column_width(ws_name, column_width)
            if not setup_complete: # First page only:
                setup_complete = True
                excel_pool.set_format()
                format_text = {                
                    'title': excel_pool.get_format('title'),
                    'header': excel_pool.get_format('header'),
                    'text': excel_pool.get_format('text'),
                    'number': excel_pool.get_format('number'),
                    }
                
            # Header write:
            row = 0
            excel_pool.write_xls_line(ws_name, row, [
                u'Fornitore:',
                u'',
                supplier.name or '',
                supplier.sql_supplier_code or '',
                u'',
                u'Dalla data: %s' % from_date,
                u'',
                u'Alla data: %s' % to_date,
                ], default_format=format_text['title'])
                
            row += 2
            excel_pool.write_xls_line(ws_name, row, header, 
                default_format=format_text['header'])
                
            total = 0
            for category in sorted(supplier_category_move[supplier]):
                subtotal = 0
                for move in sorted(supplier_category_move[supplier][category],
                        key=lambda x: x.date):
                    row += 1

                    # Readability:
                    order = move.logistic_load_id.order_id
                    partner = order.partner_invoice_id
                    product = move.product_id
                    qty = move.product_uom_qty # Delivered qty
                    
                    # Get invoice reference:
                    try:
                        invoice = order.logistic_picking_ids[0]
                        invoice_date = invoice.invoice_date or ''
                        invoice_number = invoice.invoice_number or '?'
                    except:
                        _logger.error('No invoice for order %s' % order.name)
                        invoice_date = ''
                        invoice_number = '?'
                        
                    # TODO check more than one error

                    # ---------------------------------------------------------
                    #                    Excel writing:
                    # ---------------------------------------------------------
                    # Total operation:
                    total += qty
                    subtotal += qty
                    
                    # ---------------------------------------------------------
                    # Write data line:
                    # ---------------------------------------------------------
                    excel_pool.write_xls_line(ws_name, row, (
                        category, #product.mmac_pfu.name,
                        product.default_code,
                        product.name_extended, #name,
                        (qty, format_text['number']), # TODO check if it's all!
                        move.delivery_id.name, # Delivery ref.
                        move.delivery_id.date,
                        '', # Number supplier invoice
                        invoice_number, # Our invoice
                        invoice_date[:10], # Date doc,
                        partner.country_id.code or '??', # ISO country
                        ), default_format=format_text['text'])
                row += 1
                excel_pool.write_xls_line(ws_name, row, (
                    subtotal,
                    ), default_format=format_text['number'], col=3)                    

            # -----------------------------------------------------------------
            # Write data line:
            # -----------------------------------------------------------------
            # Total
            row += 1
            excel_pool.write_xls_line(ws_name, row, (
                'Totale:', total,
                ), default_format=format_text['number'], col=2)
                
        # ---------------------------------------------------------------------
        # Save file:
        # ---------------------------------------------------------------------
        return excel_pool.return_attachment('Report_Carrier')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
