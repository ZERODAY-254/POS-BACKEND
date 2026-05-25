import base64
import json
from datetime import datetime
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


def mpesa_base_url():
    if settings.MPESA_ENVIRONMENT == 'production':
        return 'https://api.safaricom.co.ke'
    return 'https://sandbox.safaricom.co.ke'


def callback_url_warning():
    callback_url = settings.MPESA_CALLBACK_URL
    if not callback_url.startswith('https://'):
        return ' Daraja callbacks require a public HTTPS URL.'
    if '127.0.0.1' in callback_url or 'localhost' in callback_url:
        return ' Callback confirmation will not reach localhost; use ngrok or a public HTTPS domain.'
    if 'mydomain.com' in callback_url or 'your-real-domain.com' in callback_url:
        return ' Callback URL is still a placeholder; use your real public HTTPS callback URL.'
    return ''


def get_access_token():
    credentials = f'{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}'
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    request = Request(
        f'{mpesa_base_url()}/oauth/v1/generate?grant_type=client_credentials',
        headers={'Authorization': f'Basic {encoded_credentials}'},
        method='GET',
    )

    with urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode())
        return data['access_token']


def format_phone_number(phone_number):
    clean_number = ''.join(character for character in phone_number if character.isdigit())
    if clean_number.startswith('0'):
        return f'254{clean_number[1:]}'
    if clean_number.startswith('7') and len(clean_number) == 9:
        return f'254{clean_number}'
    return clean_number


def send_stk_push(phone_number, amount, account_reference, transaction_description='POS payment'):
    missing_settings = [
        name for name, value in {
            'MPESA_CONSUMER_KEY': settings.MPESA_CONSUMER_KEY,
            'MPESA_CONSUMER_SECRET': settings.MPESA_CONSUMER_SECRET,
            'MPESA_SHORTCODE': settings.MPESA_SHORTCODE,
            'MPESA_PASSKEY': settings.MPESA_PASSKEY,
            'MPESA_CALLBACK_URL': settings.MPESA_CALLBACK_URL,
        }.items()
        if not value
    ]

    if missing_settings:
        return {
            'success': False,
            'message': f'Missing M-Pesa settings: {", ".join(missing_settings)}',
            'raw': {},
        }

    callback_warning = callback_url_warning()

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password_text = f'{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}'
    password = base64.b64encode(password_text.encode()).decode()
    rounded_amount = int(Decimal(amount))

    payload = {
        'BusinessShortCode': settings.MPESA_SHORTCODE,
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': rounded_amount,
        'PartyA': format_phone_number(phone_number),
        'PartyB': settings.MPESA_SHORTCODE,
        'PhoneNumber': format_phone_number(phone_number),
        'CallBackURL': settings.MPESA_CALLBACK_URL,
        'AccountReference': account_reference,
        'TransactionDesc': transaction_description,
    }

    try:
        access_token = get_access_token()
        request = Request(
            f'{mpesa_base_url()}/mpesa/stkpush/v1/processrequest',
            data=json.dumps(payload).encode(),
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            },
            method='POST',
        )
        with urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode())
    except HTTPError as error:
        data = json.loads(error.read().decode() or '{}')
        return {'success': False, 'message': data.get('errorMessage', str(error)), 'raw': data}
    except (URLError, TimeoutError, KeyError) as error:
        return {'success': False, 'message': str(error), 'raw': {}}

    response_code = str(data.get('ResponseCode', ''))
    return {
        'success': response_code == '0',
        'message': f"{data.get('CustomerMessage') or data.get('ResponseDescription', '')}{callback_warning}",
        'raw': data,
        'merchant_request_id': data.get('MerchantRequestID', ''),
        'checkout_request_id': data.get('CheckoutRequestID', ''),
    }


def query_stk_status(checkout_request_id):
    missing_settings = [
        name for name, value in {
            'MPESA_CONSUMER_KEY': settings.MPESA_CONSUMER_KEY,
            'MPESA_CONSUMER_SECRET': settings.MPESA_CONSUMER_SECRET,
            'MPESA_SHORTCODE': settings.MPESA_SHORTCODE,
            'MPESA_PASSKEY': settings.MPESA_PASSKEY,
        }.items()
        if not value
    ]

    if missing_settings:
        return {
            'success': False,
            'message': f'Missing M-Pesa settings: {", ".join(missing_settings)}',
            'raw': {},
        }

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password_text = f'{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}'
    payload = {
        'BusinessShortCode': settings.MPESA_SHORTCODE,
        'Password': base64.b64encode(password_text.encode()).decode(),
        'Timestamp': timestamp,
        'CheckoutRequestID': checkout_request_id,
    }

    try:
        access_token = get_access_token()
        request = Request(
            f'{mpesa_base_url()}/mpesa/stkpushquery/v1/query',
            data=json.dumps(payload).encode(),
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            },
            method='POST',
        )
        with urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode())
    except HTTPError as error:
        data = json.loads(error.read().decode() or '{}')
        return {'success': False, 'message': data.get('errorMessage', str(error)), 'raw': data}
    except (URLError, TimeoutError, KeyError) as error:
        return {'success': False, 'message': str(error), 'raw': {}}

    result_code = str(data.get('ResultCode', ''))
    return {
        'success': data.get('ResponseCode') == '0',
        'status': 'success' if result_code == '0' else 'failed',
        'result_code': result_code,
        'message': data.get('ResultDesc') or data.get('ResponseDescription', ''),
        'raw': data,
    }
