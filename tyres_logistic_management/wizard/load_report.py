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


class StockPickingInReportWizard(models.TransientModel):
    """ Model name: Delivered in report
    """
    _name = 'stock.picking.in.report.wizard'
    _description = 'Delivered report'

    # -------------------------------------------------------------------------
    #                            COLUMNS:
    # -------------------------------------------------------------------------
    supplier_id = fields.Many2one('res.partner', 'Supplier')
    from_date = fields.Date('From date >=', required=True)
    to_date = fields.Date('To date <', required=True)
    exclude_fiscal_id = fields.Many2one(
        'account.fiscal.position', 'Exclude fiscal position')
    exclude_country_id = fields.Many2one(
        'res.country', 'Exclude country')
    sort = fields.Selection([
        ('date', 'Delivery report'),
        ('pfu', 'PFU report'),
        ], 'Report mode', default='pfu', required=True)

    # -------------------------------------------------------------------------

    @api.multi
    def extract_load_report(self):
        """ Extract Excel report
        """
        move_pool = self.env['stock.move']
        excel_pool = self.env['excel.writer']

        # Wizard parameters:
        from_date = self.from_date
        to_date = self.to_date
        supplier = self.supplier_id
        exclude_fiscal_id = self.exclude_fiscal_id.id
        exclude_country_id = self.exclude_country_id.id
        sort = self.sort
        nothing = '/'

        domain = [
            # Header
            ('create_date', '>=', '%s 00:00:00' % from_date),
            ('create_date', '<', '%s 00:00:00' % to_date),
            ('logistic_load_id', '!=', False),  # Load stock move only
            ('logistic_load_id.order_id.logistic_source', 'not in', (
                'refund', )),  # Not refund
        ]
        if supplier:
            domain.append(
                ('partner_id', '=', supplier.id),
                )

        if exclude_fiscal_id:
            domain.append(
                ('logistic_purchase_id.order_id.partner_id.property_account_position_id', '!=',
                    exclude_fiscal_id),
                )

        if exclude_country_id:
            domain.append(
                ('logistic_purchase_id.order_id.partner_id.country_id', '!=',
                    exclude_country_id),
                )

        # ---------------------------------------------------------------------
        #                          EXTRACT EXCEL:
        # ---------------------------------------------------------------------
        # Excel file configuration: # TODO
        header = (
            'Fornitore', 'Data', 'Documento', 'Tipo',
            'Codice', 'Prodotto', 'PFU cat.',
            'Q.', 'Prezzo', 'Subtotal',
            )
        column_width = (
            30, 10, 20, 10,
            18, 40, 15,
            10, 10, 15,
            )

        # ---------------------------------------------------------------------
        # Write detail:
        # ---------------------------------------------------------------------
        structure = {}
        summary = {}
        summary_name = 'Sommario'
        excel_pool.create_worksheet(summary_name)

        moves = move_pool.search(domain)
        for move in moves:
            if move.product_id.is_expence:
                continue
            supplier = move.logistic_purchase_id.order_id.partner_id
            if supplier not in structure:
                structure[supplier] = []
            structure[supplier].append(move)

        if not structure:
            _logger.warning('Delivery not found!')
            raise exceptions.Warning(_('No document found with this filters!'))

        # -----------------------------------------------------------------
        #                   Excel sheet creation:
        # -----------------------------------------------------------------
        setup_complete = False
        for supplier in sorted(structure, key=lambda x: (x.name if x else '')):
            # -----------------------------------------------------------------
            #                   Excel sheet creation:
            # -----------------------------------------------------------------
            ws_name = (supplier.name or 'Non presente').strip().lower()
            try:
                excel_pool.create_worksheet(ws_name)
            except:
                _logger.error('Sheet %s yet present!' % ws_name)

            excel_pool.column_width(ws_name, column_width)
            if not setup_complete: # First page only:
                setup_complete = True
                excel_pool.set_format()
                format_text = {
                    'title': excel_pool.get_format('title'),
                    'header': excel_pool.get_format('header'),
                    'white': {
                        'text': excel_pool.get_format('text'),
                        'number': excel_pool.get_format('number'),
                        },
                    'red': {
                        'text': excel_pool.get_format('bg_normal_red'),
                        'number': excel_pool.get_format(
                            'bg_normal_red_number'),
                        },
                    'green': {
                        'text': excel_pool.get_format('bg_green'),
                        'number': excel_pool.get_format(
                            'bg_green_number'),
                        },
                    }

            # -----------------------------------------------------------------
            # Header of sheet:
            # -----------------------------------------------------------------
            row = 0
            excel_pool.write_xls_line(ws_name, row, [
                u'Fornitore: %s, Data [%s, %s]' % (
                    (supplier.name or 'Tutti').strip(),
                    from_date,
                    to_date,
                    )
                ], default_format=format_text['title'])

            row += 2
            excel_pool.write_xls_line(
                ws_name, row, header,
                default_format=format_text['header'])

            total = {
                'subtotal': {},
                'quantity': {},
                }

            if sort == 'date':
                structure_sorted = sorted(
                    structure[supplier],
                    key=lambda x: x.create_date,
                    )
            else:  # PFU
                structure_sorted = sorted(
                    structure[supplier],
                    key=lambda x: (
                        x.product_id.mmac_pfu.name or nothing,
                        x.create_date,
                        ))

            for move in structure_sorted:
                row += 1
                product = move.product_id
                mmac_pfu = product.mmac_pfu.name or nothing

                logistic_purchase = move.logistic_purchase_id
                logistic_load = move.logistic_load_id
                order = logistic_load.order_id

                # -------------------------------------------------------------
                # Total:
                # -------------------------------------------------------------
                if mmac_pfu not in total['subtotal']:
                    total['subtotal'][mmac_pfu] = 0.0
                    total['quantity'][mmac_pfu] = 0.0

                product_uom_qty = move.product_uom_qty
                price_unit = logistic_purchase.price_unit
                # price_unit = move.price_unit

                subtotal = product_uom_qty * price_unit
                total['subtotal'][mmac_pfu] += subtotal
                total['quantity'][mmac_pfu] += product_uom_qty

                if subtotal > 0.0:
                    format_color = format_text['white']
                else:
                    format_color = format_text['red']

                excel_pool.write_xls_line(ws_name, row, [
                    (supplier.name or '').strip(),
                    move.create_date[:10],
                    order.name,
                    order.logistic_source,
                    product.default_code,
                    product.name_extended,
                    product.mmac_pfu.name,
                    (product_uom_qty, format_color['number']),
                    (price_unit, format_color['number']),
                    (subtotal,  format_color['number']),
                    ], default_format=format_color['text'])

            # -----------------------------------------------------------------
            # Write data line:
            # -----------------------------------------------------------------
            # Total
            row += 1
            excel_pool.write_xls_line(ws_name, row, (
                u'Totale:',
                sum(total['quantity'].values()),
                '/',
                sum(total['subtotal'].values()),
                ), default_format=format_text['green']['number'], col=6)

            summary[supplier] = total # save for summary report

        _logger.warning('Supplier found: %s [Moves: %s]' % (
            len(structure),
            len(moves),
            ))

        # -----------------------------------------------------------------
        # Summary of sheet:
        # -----------------------------------------------------------------
        row = 0
        excel_pool.write_xls_line(summary_name, row, [
            u'Sommario fornitori, Data [%s, %s]' % (
                from_date,
                to_date,
                )
            ], default_format=format_text['title'])

        row += 2
        excel_pool.write_xls_line(summary_name, row, [
            'Fornitore', 'Nazione', 'PFU Cat.', 'Pezzi', 'Totale',
            ],
            default_format=format_text['header'])
        excel_pool.column_width(summary_name, [
            35, 15, 10, 15, 20,
            ])

        master_total = {
            'quantity': {},
            'subtotal': {},
            }

        for supplier in sorted(summary, key=lambda x: (x.name if x else '')):
            total = summary[supplier]
            for mmac_pfu in sorted(total['subtotal']): # Use this key same x q.
                quantity = total['quantity'][mmac_pfu]
                subtotal = total['subtotal'][mmac_pfu]

                if subtotal:
                    format_color = format_text['white']
                else:
                    format_color = format_text['red']

                # -------------------------------------------------------------
                # Total:
                # -------------------------------------------------------------
                if mmac_pfu not in master_total['subtotal']:
                    master_total['quantity'][mmac_pfu] = 0.0
                    master_total['subtotal'][mmac_pfu] = 0.0

                master_total['quantity'][mmac_pfu] += quantity
                master_total['subtotal'][mmac_pfu] += subtotal

                if sort == 'pfu':
                    row += 1
                    excel_pool.write_xls_line(summary_name, row, [
                        (supplier.name or '').strip(),
                        supplier.country_id.name,
                        mmac_pfu,
                        (quantity, format_color['number']),
                        (subtotal, format_color['number']),
                        ], default_format=format_color['text'])

            if sort == 'date':
                row += 1
                quantity = sum([
                    total['quantity'][key] for key in total['quantity']])
                subtotal = sum([
                    total['subtotal'][key] for key in total['subtotal']])
                if subtotal:
                    format_color = format_text['white']
                else:
                    format_color = format_text['red']

                excel_pool.write_xls_line(summary_name, row, [
                    (supplier.name or '').strip(),
                    supplier.country_id.name,
                    'Tutte',
                    (quantity, format_color['number']),
                    (subtotal, format_color['number']),
                    ], default_format=format_color['text'])

        # -----------------------------------------------------------------
        # Write data line:
        # -----------------------------------------------------------------
        # Total
        if sort == 'pfu':
            for mmac_pfu in sorted(master_total['subtotal']):
                row += 1

                subtotal = master_total['subtotal'][mmac_pfu]
                quantity = master_total['quantity'][mmac_pfu]
                excel_pool.write_xls_line(summary_name, row, (
                    'Tot. %s' % mmac_pfu,
                    quantity,
                    subtotal,
                    ), default_format=format_text['green']['number'], col=2)
        else: # date report
            row += 1

            quantity = sum([
                master_total['quantity'][key] \
                    for key in master_total['subtotal']])
            subtotal = sum([
                master_total['subtotal'][key] \
                    for key in master_total['subtotal']])

            excel_pool.write_xls_line(summary_name, row, (
                'Totale',
                quantity,
                subtotal,
                ), default_format=format_text['green']['number'], col=2)

        # ---------------------------------------------------------------------
        # Save file:
        # ---------------------------------------------------------------------
        return excel_pool.return_attachment('Report_Corrieri')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
