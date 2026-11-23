# -*- coding: utf-8 -*-
from email.utils import formataddr
from odoo import api, fields, models


class IrMailServer(models.Model):
    """Adresses partagées (remplace smtp_by_user v14) : Odoo 20 gère en standard le serveur personnel d'un utilisateur
    (owner_user_id), mais seulement avec sa propre adresse (from_filter = adresse de l'utilisateur). Pour un utilisateur
    qui envoie avec une adresse partagée (odoo@, prepa@...), le serveur n'a pas de propriétaire et l'utilisateur est
    dans is_user_id"""
    _inherit = 'ir.mail_server'

    is_user_id = fields.Many2one(
        'res.users', 'Utilisateur (adresse partagée)', copy=False,
        help="Utilisateur qui envoie ses mails avec l'adresse de ce serveur (adresse partagée, différente de la sienne) : "
             "expéditeur « Nom <adresse du serveur> », réponses à l'adresse de l'utilisateur. Pour un utilisateur qui "
             "envoie avec sa propre adresse : champ Propriétaire (standard)")


class MailMail(models.Model):
    _inherit = 'mail.mail'

    @api.model_create_multi
    def create(self, vals_list):
        "Comme smtp_by_user v14 : serveur, expéditeur et adresse de réponse de l'utilisateur à adresse partagée"
        server = self.env['ir.mail_server'].sudo().search([('is_user_id', '=', self.env.uid)], limit=1)
        if server:
            user = self.env.user
            adresse = server.from_filter or server.smtp_user
            for vals in vals_list:
                vals.update({
                    'mail_server_id': server.id,
                    'email_from'    : formataddr((user.name, adresse)),
                    'reply_to'      : formataddr((user.name, user.email or adresse)),
                })
        return super().create(vals_list)
