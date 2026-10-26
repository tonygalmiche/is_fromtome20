# -*- coding: utf-8 -*-
import logging
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
_logger = logging.getLogger(__name__)


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    is_dlc_ddm         = fields.Date('DLC / DDM', related="lot_id.is_dlc_ddm")
    is_fournisseur_id  = fields.Many2one('res.partner', 'Fournisseur par défaut', related="product_id.product_tmpl_id.is_fournisseur_id", store=True)
    inventory_quantity = fields.Float(digits="Product Unit")
    available_quantity = fields.Float(digits="Product Unit")
    quantity           = fields.Float(digits="Product Unit")
    reserved_quantity  = fields.Float(digits="Product Unit")

    # v20 : stock.inventory supprimé : stock valorisé au dernier prix facturé (en v14 sur stock.inventory.line)
    @api.depends('product_id','quantity')
    def compute_is_dernier_prix(self):
        cr = self.env.cr
        for obj in self:
            SQL="""
                SELECT ail.price_unit,ail.product_uom_id
                FROM account_move_line ail inner join account_move ai on ail.move_id=ai.id
                WHERE ail.product_id=%s  and ai.state='posted' and ai.move_type='in_invoice'
                ORDER BY ail.id desc
                limit 1
            """
            cr.execute(SQL,[obj.product_id.id])
            prix=0
            uom_id = obj.uom_id.id
            for row in cr.fetchall():
                prix = row[0]
                uom_id=row[1]
            obj.is_dernier_prix   = prix
            obj.is_stock_valorise = prix*obj.quantity
            obj.is_uom_facture_id = uom_id

    is_dernier_prix    = fields.Float("Dernier prix facturé"       , compute=compute_is_dernier_prix, store=False)
    is_stock_valorise  = fields.Float("Stock valorisé"             , compute=compute_is_dernier_prix, store=False)
    is_uom_facture_id  = fields.Many2one('uom.uom', 'Unité facture', compute=compute_is_dernier_prix, store=False)


    # v20 : surcharge v14 de _update_reserved_quantity supprimée (verrou « libérer plus que réservé » retiré le 03/11/2023) :
    # la v20 n'a plus ce contrôle (voir § 4.7 de la page de migration)

