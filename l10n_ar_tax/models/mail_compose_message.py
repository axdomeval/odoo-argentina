from odoo import models
from odoo.tools import safe_eval
import base64


class MailComposeMessage(models.TransientModel):
    _inherit = "mail.compose.message"

    # TODO falta adaptar
    def _onchange_template_id(self, template_id, composition_mode, model, res_id):
        values = super()._onchange_template_id(
            template_id, composition_mode, model, res_id)
        if template_id and model == 'account.payment':
            payment = self.env[model].browse(res_id)
            if payment.partner_type != 'supplier':
                return values
            report = self.env.ref('l10n_ar_tax.action_report_withholding_certificate', raise_if_not_found=False)
            if not report:
                return values
            attachment_ids = []
            for payment in payment.payment_ids.filtered(lambda p: p.payment_method_code == 'withholding'):
                report_name = safe_eval.safe_eval(report.print_report_name, {'object': payment})
                result, format = self.env['ir.actions.report']._render(report.report_name, payment.ids)
                file = base64.b64encode(result)
                data_attach = {
                    'name': report_name,
                    'datas': file,
                    'res_model': 'mail.compose.message',
                    'res_id': 0,
                    'type': 'binary',
                }
                attachment_ids.append(self.env['ir.attachment'].create(data_attach).id)
            if values.get('value', False) and values['value'].get('attachment_ids', []) or attachment_ids:
                values_attachment_ids = values['value'].get('attachment_ids', False) and \
                    values['value']['attachment_ids'][0][2] or []
                values['value']['attachment_ids'] = [(6, 0, values_attachment_ids + attachment_ids)]

        return values
