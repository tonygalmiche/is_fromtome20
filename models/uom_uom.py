# -*- coding: utf-8 -*-
from odoo import models


class UomUom(models.Model):
    _inherit = 'uom.uom'

    def is_categorie_unite(self):
        """v20 : plus de catégorie d'unité (uom.category, category_id) : renvoie « Poids » si l'unité
        a la même unité de référence que le kg, comme category_id.name en v14 (seule catégorie testée)"""
        kg = self.env.ref('uom.product_uom_kgm', raise_if_not_found=False)
        if len(self) == 1 and kg and self._has_common_reference(kg):
            return "Poids"
        return False
