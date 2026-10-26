# -*- coding: utf-8 -*-
# Tests de fumée (§ 4.8 de la page de migration, F1, F2 et F6) : vérifient que rien ne plante, pas le résultat
# À lancer sur la base reprise (sans données, il n'y a rien à lire) ; rien n'est enregistré (transaction annulée)
# Lancement : voir Documentation/Odoo/tests-unitaires-odoo.md
import logging
import time
from lxml import etree
from odoo.tests import TransactionCase, tagged  # pyright: ignore[reportMissingImports]
_logger = logging.getLogger(__name__)

MODULE = 'is_fromtome20'
TYPES_VUES = ('list', 'form', 'kanban', 'search', 'pivot', 'graph', 'calendar')


# fumee : pour les lancer seuls (--test-tags /is_fromtome20:TestFumee)
@tagged('post_install', '-at_install', 'is_fromtome20', 'fumee')
class TestFumee(TransactionCase):

    def _essai(self, fonction, **libelle):
        # Chaque essai dans un savepoint : une erreur est notée (subTest) sans bloquer les essais suivants
        with self.subTest(**libelle):
            with self.env.cr.savepoint():
                fonction()

    def _ids_module(self, model):
        return self.env['ir.model.data'].search([('module', '=', MODULE), ('model', '=', model)]).mapped('res_id')

    def _specification(self, arch):
        # Champs de la vue, comme le client web : hors vues des lignes One2many et hors regroupements <groupby> (champs
        # du modèle regroupé, ex : state de account.move dans la liste des écritures)
        noeud = etree.fromstring(arch)
        return {champ.get('name'): {} for champ in noeud.xpath('//field[not(ancestor::field) and not(ancestor::groupby)]')}

    def _lire_vue(self, Model, view_id, view_type):
        # get_views, puis lecture des données comme le client web : liste / kanban (5 lignes), formulaire (1 fiche)
        # Nom de la vue dans le journal (vue qui bloque) ; avertissement si plus de 5 s (vue à optimiser)
        _logger.info("Vue %s (%s, %s)", view_id, Model._name, view_type)
        debut = time.time()
        res = Model.get_views([(view_id, view_type)])
        if Model._abstract:
            return # modèle sans table (ex : board.board, tableau de bord) : vue seule
        spec = self._specification(res['views'][view_type]['arch'])
        if view_type in ('list', 'kanban'):
            Model.web_search_read([], spec, limit=5)
        if view_type == 'form':
            record = Model.search([], limit=1)
            if record:
                record.web_read(spec)
        duree = time.time() - debut
        if duree > 5:
            _logger.warning("Vue %s (%s, %s) lente : %.1f s", view_id, Model._name, view_type, duree)

    def test_f1_champs_calcules(self):
        # F1 : tous les champs calculés ajoutés par le module, recalculés sur 5 enregistrements de chaque modèle
        champs = self.env['ir.model.fields'].browse(self._ids_module('ir.model.fields'))
        for champ in champs:
            if champ.model not in self.env:
                continue
            Model = self.env[champ.model]
            field = Model._fields.get(champ.name)
            if not field or not field.compute or Model._abstract:
                continue
            # Vue SQL (_auto False) : champs stockés lus dans la vue, jamais recalculés par Odoo
            if field.store and not Model._auto:
                continue
            def calculer(Model=Model, field=field):
                records = Model.search([], limit=5)
                if field.store:
                    self.env.add_to_compute(field, records)
                else:
                    records.invalidate_recordset([field.name])
                records.mapped(field.name)
            self._essai(calculer, modele=champ.model, champ=champ.name)

    def test_f2_vues(self):
        # F2 : chaque vue du module, ou la vue standard qu'elle modifie, ouverte et lue comme par le client web
        vues = self.env['ir.ui.view'].browse(self._ids_module('ir.ui.view'))
        racines = self.env['ir.ui.view']
        for vue in vues:
            racine = vue
            while racine.mode == 'extension' and racine.inherit_id:
                racine = racine.inherit_id
            racines |= racine
        for racine in racines:
            if racine.type not in TYPES_VUES or not racine.active or racine.model not in self.env:
                continue
            self._essai(lambda racine=racine: self._lire_vue(self.env[racine.model], racine.id, racine.type),
                        vue=racine.xml_id or racine.name, type=racine.type)

    def test_f6_menus_par_profil(self):
        # F6 : pour chaque profil (utilisateurs internes actifs avec les mêmes groupes), chaque menu visible ouvert
        # avec ses vues (actions de fenêtre ; actions serveur non lancées, elles peuvent modifier des données)
        profils = {}
        for user in self.env['res.users'].search([('share', '=', False), ('id', '!=', 1)]):
            profils.setdefault(frozenset(user.group_ids.ids), user)
        for user in profils.values():
            # Menus visibles comme dans le client web (search seul ne filtre pas les groupes en v20)
            menus = self.env['ir.ui.menu'].with_user(user).search([('action', '!=', False)])._filter_visible_menus()
            for menu in menus:
                action = menu.sudo().action
                if not action or action._name != 'ir.actions.act_window' or action.res_model not in self.env:
                    continue
                Model = self.env[action.res_model].with_user(user)
                for view_id, view_type in action.views:
                    if view_type in ('list', 'form'):
                        self._essai(lambda Model=Model, view_id=view_id, view_type=view_type: self._lire_vue(Model, view_id, view_type),
                                    utilisateur=user.login, menu=menu.complete_name, type=view_type)
