from payments.models import MpesaTransaction as BaseMpesaTransaction


class MpesaTransaction(BaseMpesaTransaction):
    class Meta:
        proxy = True
        verbose_name = 'M-Pesa transaction'
        verbose_name_plural = 'M-Pesa transactions'
