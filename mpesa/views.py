from payments.views import (
    MpesaTransactionViewSet,
    mpesa_callback,
    mpesa_callback_config,
    mpesa_health,
)


class MpesaViewSet(MpesaTransactionViewSet):
    pass
