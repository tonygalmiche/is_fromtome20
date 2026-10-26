# -*- coding: utf-8 -*-
# Tests du calcul des colis (étape 10 du module) : article au poids et article à la pièce
# Lancement : voir Documentation/Odoo/tests-unitaires-odoo.md
from odoo.tests import TransactionCase, tagged  # pyright: ignore[reportMissingImports]


# post_install : lancé après l'installation de tous les modules
@tagged('post_install', '-at_install', 'is_fromtome20')
class TestColisage(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        kg    = cls.env.ref('uom.product_uom_kgm')
        piece = cls.env.ref('uom.product_uom_unit')
        # Comté vendu au kg : colis de 2,5 kg
        cls.article_poids = cls.env['product.template'].create({
            'name'              : 'Test Comté au kg',
            'type'              : 'consu',
            'is_storable'       : True,
            'uom_id'            : kg.id,
            'is_poids_net_colis': 2.5,
        })
        # Crottin vendu à la pièce : colis de 6 pièces
        cls.article_piece = cls.env['product.template'].create({
            'name'                  : 'Test Crottin à la pièce',
            'type'                  : 'consu',
            'is_storable'           : True,
            'uom_id'                : piece.id,
            'is_nb_pieces_par_colis': 6,
        })

    def test_article_poids(self):
        self.assertEqual(self.article_poids.uom_id.is_categorie_unite(), 'Poids')
        self.assertAlmostEqual(self.article_poids.qty2nb_colis(10), 4)     # 10 kg = 4 colis
        self.assertAlmostEqual(self.article_poids.colis2uom(3), 7.5)       # 3 colis = 7,5 kg

    def test_article_piece(self):
        self.assertFalse(self.article_piece.uom_id.is_categorie_unite())
        self.assertAlmostEqual(self.article_piece.qty2nb_colis(18), 3)     # 18 pièces = 3 colis
        self.assertAlmostEqual(self.article_piece.colis2uom(2), 12)        # 2 colis = 12 pièces
