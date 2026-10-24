# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from datetime import date,timedelta
from calendar import monthrange
 

# OCA 20.0 : account_payment_order (account_payment_batch_oca) non disponible en 20.0 (28/09/2026), à décommenter après son portage
# class AccountPaymentOrder(models.Model):
#     _inherit = 'account.payment.order'
#
#     #Champ créé uniquement pour pouvoir faire un PDF
#     partner_id          = fields.Many2one('res.partner','Partenaire', related='generated_user_id.partner_id')
#     is_export_compta_id = fields.Many2one('is.export.compta', 'Folio', copy=False)


class AccountPaymentTermLine(models.Model):
    _inherit = "account.payment.term.line"

    # Option 'fin_de_decade' ajoutée le 22/03/2024 (option de la v14 => delay_type en v20)
    delay_type = fields.Selection(selection_add=[
        ("fin_de_decade", "Fin de décade"),
    ], ondelete={'fin_de_decade': 'set default'})


    def _get_due_date(self, date_ref):
        if self.delay_type != 'fin_de_decade':
            return super()._get_due_date(date_ref)
        next_date = fields.Date.from_string(date_ref) or fields.Date.context_today(self)
        next_date += timedelta(days=self.nb_days)
        if next_date.day>=1 and next_date.day<=10:
            delta = 10 - next_date.day
            next_date += timedelta(days=delta)

        if next_date.day>=11 and next_date.day<=20:
            delta = 20 - next_date.day
            next_date += timedelta(days=delta)

        if next_date.day>=21 and next_date.day<=31:
            nb_jours_dans_mois = monthrange(next_date.year, next_date.month)[1]
            delta = nb_jours_dans_mois - next_date.day
            next_date += timedelta(days=delta)
        return next_date


