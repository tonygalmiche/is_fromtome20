# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    def send_mail(self, **kwargs):
        context=self._context
        res=super(MailComposer, self).send_mail(**kwargs)

        #** Permet de supprimer les abonnés du document après l'envoi du mail **
        model=context.get('active_model')
        active_id=context.get('active_id')
        if model and active_id:
            obj = self.env[model].browse(active_id)
            if obj:
                obj.sudo().message_follower_ids.unlink()
        #***********************************************************************
        return res
