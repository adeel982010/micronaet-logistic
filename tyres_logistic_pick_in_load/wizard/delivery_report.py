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
from odoo import api, fields, models, tools, exceptions, SUPERUSER_ID
from odoo.addons import decimal_precision as dp
from odoo.tools.translate import _


_logger = logging.getLogger(__name__)


class LogisticDeliveryReportWizard(models.TransientModel):
    """ Report wizard for delivery in period
    """
    _name = 'logistic.delivery.report.wizard'
    _description = 'Delivery report'

    # -------------------------------------------------------------------------
    #                               BUTTON EVENT:
    # -------------------------------------------------------------------------
    @api.multi
    def delivery_report_button(self):
        """ Account fees report
        """
        delivery_pool = self.env['stock.picking.delivery']
        excel_pool = self.env['excel.writer']

        filename = 'consegne_fornitore'

        # ---------------------------------------------------------------------
        # Delivery data:
        # ---------------------------------------------------------------------
        from_date = self.from_date
        to_date = self.to_date
        supplier = self.supplier_id

        domain = [
            ('date', '>=', from_date),
            ('date', '<', to_date),
            ]
        title = 'Dettaglio consegne del periodo: [%s - %s]' % (
                from_date, to_date,
                )
        if supplier:
            domain.append(('supplier_id', '=', supplier.id))
            title += ', fornitore: %s' % supplier.name
        else:
            title += ', fornitore: Tutti'

        delivery_data = delivery_pool.search(domain)

        # ---------------------------------------------------------------------
        #                               EXCEL:
        # ---------------------------------------------------------------------
        ws_name = 'Dettaglio consegne'
        excel_pool.create_worksheet(ws_name)

        excel_pool.set_format()
        format_text = {
            'title': excel_pool.get_format('title'),
            'header': excel_pool.get_format('header'),
            'text': excel_pool.get_format('text'),
            'number': excel_pool.get_format('number'),
            'total': excel_pool.get_format('text_total'),

            'red': excel_pool.get_format('text_red'),
            }

        header = [
            'Fornitore',
            'Rif.',
            'Data',
            'Utente',
            'Creazione',
            'Picking',

            'Codice',
            'Nome',
            'Q.',
            'Prezzo un.',
            'Subtotal',
            'Drop.',
            'Int.',
            ]

        width = [
            30, 10, 8, 15, 18, 12,
            12, 40, 5, 10, 15, 5, 5,
            ]

        excel_pool.column_width(ws_name, width)

        row = 0
        excel_pool.write_xls_line(ws_name, row, [
            title,
            ], default_format=format_text['title'])

        row += 2
        excel_pool.write_xls_line(ws_name, row, header,
            default_format=format_text['header'])

        total = 0.0
        for delivery in sorted(delivery_data, key=lambda x:
                (x.supplier_id.name, x.date)):

            header = [
                delivery.supplier_id.name,
                delivery.name,
                delivery.date,
                delivery.create_uid.name,
                delivery.create_date,
                delivery.picking_id.name,
                ]

            # -----------------------------------------------------------------
            # Row linked to customer order:
            # -----------------------------------------------------------------
            internal = ''
            for detail in delivery.move_line_ids:
                row += 1
                # Header:
                excel_pool.write_xls_line(ws_name, row, header,
                    default_format=format_text['text'])

                # Detail:
                subtotal = detail.product_uom_qty * detail.price_unit
                total += subtotal
                line = [
                    detail.default_code,
                    detail.name_extended,
                    (detail.product_uom_qty, format_text['number']),
                    (detail.price_unit, format_text['number']),
                    (subtotal, format_text['number']),
                    detail.dropship_manage,
                    internal,
                    ]
                excel_pool.write_xls_line(ws_name, row, line,
                    default_format=format_text['text'], col=6)

            # -----------------------------------------------------------------
            # Row linked to internal stock:
            # -----------------------------------------------------------------
            internal = 'X'
            for quant in delivery.quant_ids:
                row += 1
                # Header:
                excel_pool.write_xls_line(ws_name, row, header,
                    default_format=format_text['text'])

                # Detail:
                subtotal = quant.product_qty * quant.price
                total += subtotal
                line = [
                    quant.product_id.default_code,
                    quant.product_id.name_extended,
                    (quant.product_qty, format_text['number']),
                    (quant.price, format_text['number']),
                    (subtotal, format_text['number']),
                    '', # never for internal
                    internal,
                    ]
                excel_pool.write_xls_line(ws_name, row, line,
                    default_format=format_text['text'], col=6)

        row += 1
        # Write formatted with color
        excel_pool.write_xls_line(ws_name, row, [
            'Totale',
            (total, format_text['number']),
            ], default_format=format_text['text'], col=9)
        return excel_pool.return_attachment(filename)

    # -------------------------------------------------------------------------
    #                               COLUMNS:
    # -------------------------------------------------------------------------
    from_date = fields.Date('From date >=', required=True)
    to_date = fields.Date('To date <', required=True)
    supplier_id = fields.Many2one(
        'res.partner', 'Supplier', domain="[('supplier', '=', True)]")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
