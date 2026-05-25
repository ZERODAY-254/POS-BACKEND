from django.utils import timezone

from salesapp.models import Sale

from .models import PaymentNotification


def confirm_mpesa_transaction(transaction, result_code, result_description='', metadata=None, raw_callback=None):
    metadata = metadata or {}
    raw_callback = raw_callback or {}

    transaction.raw_callback = raw_callback or transaction.raw_callback
    transaction.result_code = str(result_code)
    transaction.result_description = result_description

    if str(result_code) == '0':
        receipt_number = metadata.get('MpesaReceiptNumber', transaction.mpesa_receipt_number)
        transaction.status = 'success'
        transaction.mpesa_receipt_number = receipt_number or ''
        transaction.phone_number = str(metadata.get('PhoneNumber', transaction.phone_number))

        if transaction.payment:
            transaction.payment.status = 'paid'
            transaction.payment.mpesa_receipt = transaction.mpesa_receipt_number
            transaction.payment.paid_at = timezone.now()
            transaction.payment.save(update_fields=['status', 'mpesa_receipt', 'paid_at'])

            Sale.objects.filter(receipt_number=transaction.payment.reference).update(
                payment_status='paid',
                payment_reference=transaction.mpesa_receipt_number,
            )

        title = 'M-Pesa payment received'
        message = f'M-Pesa receipt {transaction.mpesa_receipt_number} confirmed.'
        severity = 'success'
    else:
        transaction.status = 'failed'

        if transaction.payment:
            transaction.payment.status = 'failed'
            transaction.payment.save(update_fields=['status'])
            Sale.objects.filter(receipt_number=transaction.payment.reference).update(payment_status='failed')

        title = 'M-Pesa payment failed'
        message = result_description or 'The M-Pesa payment was not completed.'
        severity = 'error'

    transaction.save()
    PaymentNotification.objects.create(
        channel='mpesa',
        severity=severity,
        title=title,
        message=message,
        payment=transaction.payment,
        mpesa_transaction=transaction,
        action_url='/payments',
    )
    return transaction
