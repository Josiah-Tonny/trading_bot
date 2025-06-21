from telegram import LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
import os
from dotenv import load_dotenv
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN")
SUBSCRIPTION_PRICE_USD = 10.00  # $10.00 in USD
SYMBOL_CHANGE_PRICE_USD = 1.00  # $1.00 in USD
CURRENCY_DEFAULT = "USD"

MPESA_NUMBER = os.getenv("MPESA_NUMBER")
PAYPAL_LINK = os.getenv("PAYPAL_LINK")
BANK_DETAILS = os.getenv("BANK_DETAILS")

# Map Telegram language/country codes to currency codes
COUNTRY_TO_CURRENCY = {
    "AF": "AFN",  # Afghanistan
    "AL": "ALL",  # Albania
    "DZ": "DZD",  # Algeria
    "AS": "USD",  # American Samoa
    "AD": "EUR",  # Andorra
    "AO": "AOA",  # Angola
    "AI": "XCD",  # Anguilla
    # Antarctica: No universal currency
    "AG": "XCD",  # Antigua and Barbuda
    "AR": "ARS",  # Argentina
    "AM": "AMD",  # Armenia
    "AW": "AWG",  # Aruba
    "AU": "AUD",  # Australia
    "AT": "EUR",  # Austria
    "AZ": "AZN",  # Azerbaijan
    "BS": "BSD",  # Bahamas
    "BH": "BHD",  # Bahrain
    "BD": "BDT",  # Bangladesh
    "BB": "BBD",  # Barbados
    "BY": "BYN",  # Belarus
    "BE": "EUR",  # Belgium
    "BZ": "BZD",  # Belize
    "BJ": "XOF",  # Benin
    "BM": "BMD",  # Bermuda
    "BT": "BTN",  # Bhutan
    # Bhutan also uses INR
    "BO": "BOB",  # Bolivia
    # Bolivia also uses BOV
    "BQ": "USD",  # Bonaire, Sint Eustatius and Saba
    "BA": "BAM",  # Bosnia and Herzegovina
    "BW": "BWP",  # Botswana
    "BV": "NOK",  # Bouvet Island
    "BR": "BRL",  # Brazil
    "IO": "USD",  # British Indian Ocean Territory
    "BN": "BND",  # Brunei Darussalam
    "BG": "BGN",  # Bulgaria
    "BF": "XOF",  # Burkina Faso
    "BI": "BIF",  # Burundi
    "CV": "CVE",  # Cabo Verde
    "KH": "KHR",  # Cambodia
    "CM": "XAF",  # Cameroon
    "CA": "CAD",  # Canada
    "KY": "KYD",  # Cayman Islands
    "CF": "XAF",  # Central African Republic
    "TD": "XAF",  # Chad
    "CL": "CLP",  # Chile
    # Chile also uses CLF
    "CN": "CNY",  # China
    "CX": "AUD",  # Christmas Island
    "CC": "AUD",  # Cocos (Keeling) Islands
    "CO": "COP",  # Colombia
    # Colombia also uses COU
    "KM": "KMF",  # Comoros
    "CD": "CDF",  # Congo (Democratic Republic)
    "CG": "XAF",  # Congo
    "CK": "NZD",  # Cook Islands
    "CR": "CRC",  # Costa Rica
    "HR": "EUR",  # Croatia
    "CU": "CUP",  # Cuba
    # Cuba also uses CUC
    "CW": "ANG",  # Curaçao (ANG: Netherlands Antillean Guilder)
    "CY": "EUR",  # Cyprus
    "CZ": "CZK",  # Czech Republic
    "CI": "XOF",  # Côte d'Ivoire
    "DK": "DKK",  # Denmark
    "DJ": "DJF",  # Djibouti
    "DM": "XCD",  # Dominica
    "DO": "DOP",  # Dominican Republic
    "EC": "USD",  # Ecuador
    "EG": "EGP",  # Egypt
    "SV": "USD",  # El Salvador
    # El Salvador also uses SVC
    "GQ": "XAF",  # Equatorial Guinea
    "ER": "ERN",  # Eritrea
    "EE": "EUR",  # Estonia
    "ET": "ETB",  # Ethiopia
    "FK": "FKP",  # Falkland Islands
    "FO": "DKK",  # Faroe Islands
    "FJ": "FJD",  # Fiji
    "FI": "EUR",  # Finland
    "FR": "EUR",  # France
    "GF": "EUR",  # French Guiana
    "PF": "XPF",  # French Polynesia
    "TF": "EUR",  # French Southern Territories
    "GA": "XAF",  # Gabon
    "GM": "GMD",  # Gambia
    "GE": "GEL",  # Georgia
    "DE": "EUR",  # Germany
    "GH": "GHS",  # Ghana
    "GI": "GIP",  # Gibraltar
    "GR": "EUR",  # Greece
    "GL": "DKK",  # Greenland
    "GD": "XCD",  # Grenada
    "GP": "EUR",  # Guadeloupe
    "GU": "USD",  # Guam
    "GT": "GTQ",  # Guatemala
    "GG": "GBP",  # Guernsey
    "GN": "GNF",  # Guinea
    "GW": "XOF",  # Guinea-Bissau
    "GY": "GYD",  # Guyana
    "HT": "HTG",  # Haiti
    # Haiti also uses USD
    "HM": "AUD",  # Heard Island and McDonald Islands
    "VA": "EUR",  # Holy See
    "HN": "HNL",  # Honduras
    "HK": "HKD",  # Hong Kong
    "HU": "HUF",  # Hungary
    "IS": "ISK",  # Iceland
    "IN": "INR",  # India
    "ID": "IDR",  # Indonesia
    # IMF: XDR (Special Drawing Right)
    "IR": "IRR",  # Iran
    "IQ": "IQD",  # Iraq
    "IE": "EUR",  # Ireland
    "IM": "GBP",  # Isle of Man
    "IL": "ILS",  # Israel
    "IT": "EUR",  # Italy
    "JM": "JMD",  # Jamaica
    "JP": "JPY",  # Japan
    "JE": "GBP",  # Jersey
    "JO": "JOD",  # Jordan
    "KZ": "KZT",  # Kazakhstan
    "KE": "KES",  # Kenya
    "KI": "AUD",  # Kiribati
    "KP": "KPW",  # North Korea
    "KR": "KRW",  # South Korea
    "KW": "KWD",  # Kuwait
    "KG": "KGS",  # Kyrgyzstan
    "LA": "LAK",  # Laos
    "LV": "EUR",  # Latvia
    "LB": "LBP",  # Lebanon
    "LS": "LSL",  # Lesotho
    # Lesotho also uses ZAR
    "LR": "LRD",  # Liberia
    "LY": "LYD",  # Libya
    "LI": "CHF",  # Liechtenstein
    "LT": "EUR",  # Lithuania
    "LU": "EUR",  # Luxembourg
    "MO": "MOP",  # Macao
    "MG": "MGA",  # Madagascar
    "MW": "MWK",  # Malawi
    "MY": "MYR",  # Malaysia
    "MV": "MVR",  # Maldives
    "ML": "XOF",  # Mali
    "MT": "EUR",  # Malta
    "MH": "USD",  # Marshall Islands
    "MQ": "EUR",  # Martinique
    "MR": "MRU",  # Mauritania
    "MU": "MUR",  # Mauritius
    "YT": "EUR",  # Mayotte
    # African Development Bank: XUA
    "MX": "MXN",  # Mexico
    # Mexico also uses MXV
    "FM": "USD",  # Micronesia
    "MD": "MDL",  # Moldova
    "MC": "EUR",  # Monaco
    "MN": "MNT",  # Mongolia
    "ME": "EUR",  # Montenegro
    "MS": "XCD",  # Montserrat
    "MA": "MAD",  # Morocco
    "MZ": "MZN",  # Mozambique
    "MM": "MMK",  # Myanmar
    "NA": "NAD",  # Namibia
    # Namibia also uses ZAR
    "NR": "AUD",  # Nauru
    "NP": "NPR",  # Nepal
    "NL": "EUR",  # Netherlands
    "NC": "XPF",  # New Caledonia
    "NZ": "NZD",  # New Zealand
    "NI": "NIO",  # Nicaragua
    "NE": "XOF",  # Niger
    "NG": "NGN",  # Nigeria
    "NU": "NZD",  # Niue
    "NF": "AUD",  # Norfolk Island
    "MP": "USD",  # Northern Mariana Islands
    "NO": "NOK",  # Norway
    "OM": "OMR",  # Oman
    "PK": "PKR",  # Pakistan
    "PW": "USD",  # Palau
    # Palestine: No universal currency
    "PA": "PAB",  # Panama
    # Panama also uses USD
    "PG": "PGK",  # Papua New Guinea
    "PY": "PYG",  # Paraguay
    "PE": "PEN",  # Peru
    "PH": "PHP",  # Philippines
    "PN": "NZD",  # Pitcairn
    "PL": "PLN",  # Poland
    "PT": "EUR",  # Portugal
    "PR": "USD",  # Puerto Rico
    "QA": "QAR",  # Qatar
    "MK": "MKD",  # North Macedonia
    "RO": "RON",  # Romania
    "RU": "RUB",  # Russia
    "RW": "RWF",  # Rwanda
    "RE": "EUR",  # Réunion
    "BL": "EUR",  # Saint Barthélemy
    "SH": "SHP",  # Saint Helena
    "KN": "XCD",  # Saint Kitts and Nevis
    "LC": "XCD",  # Saint Lucia
    "MF": "EUR",  # Saint Martin (French part)
    "PM": "EUR",  # Saint Pierre and Miquelon
    "VC": "XCD",  # Saint Vincent and the Grenadines
    "WS": "WST",  # Samoa
    "SM": "EUR",  # San Marino
    "ST": "STN",  # Sao Tome and Principe
    "SA": "SAR",  # Saudi Arabia
    "SN": "XOF",  # Senegal
    "RS": "RSD",  # Serbia
    "SC": "SCR",  # Seychelles
    "SL": "SLE",  # Sierra Leone
    "SG": "SGD",  # Singapore
    # Sint Maarten: XCG (Caribbean guilder)
    # SUCRE: XSU
    "SK": "EUR",  # Slovakia
    "SI": "EUR",  # Slovenia
    "SB": "SBD",  # Solomon Islands
    "SO": "SOS",  # Somalia
    "ZA": "ZAR",  # South Africa
    # South Georgia and the South Sandwich Islands: No universal currency
    "SS": "SSP",  # South Sudan
    "ES": "EUR",  # Spain
    "LK": "LKR",  # Sri Lanka
    "SD": "SDG",  # Sudan
    "SR": "SRD",  # Suriname
    "SJ": "NOK",  # Svalbard and Jan Mayen
    "SZ": "SZL",  # Swaziland
    "SE": "SEK",  # Sweden
    "CH": "CHF",  # Switzerland
    "SY": "SYP",  # Syria
    "TW": "TWD",  # Taiwan
    "TJ": "TJS",  # Tajikistan
    "TZ": "TZS",  # Tanzania
    "TH": "THB",  # Thailand
    "TL": "USD",  # Timor-Leste
    "TG": "XOF",  # Togo
    "TK": "NZD",  # Tokelau
    "TO": "TOP",  # Tonga
    "TT": "TTD",  # Trinidad and Tobago
    "TN": "TND",  # Tunisia
    "TR": "TRY",  # Turkey
    "TM": "TMT",  # Turkmenistan
    "TC": "USD",  # Turks and Caicos Islands
    "TV": "AUD",  # Tuvalu
    "UG": "UGX",  # Uganda
    "UA": "UAH",  # Ukraine
    "AE": "AED",  # United Arab Emirates
    "GB": "GBP",  # United Kingdom
    "US": "USD",  # United States
    # USN: US Dollar (Next day)
    "UY": "UYU",  # Uruguay
    # Uruguay also uses UYI
    "UZ": "UZS",  # Uzbekistan
    "VU": "VUV",  # Vanuatu
    "VE": "VED",  # Venezuela (Bolivarian Republic of)
    # Venezuela also uses VEF
    "VN": "VND",  # Viet Nam
    "VG": "USD",  # Virgin Islands (British)
    "VI": "USD",  # Virgin Islands (U.S.)
    "WF": "XPF",  # Wallis and Futuna
    "EH": "MAD",  # Western Sahara
    "YE": "YER",  # Yemen
    "ZM": "ZMW",  # Zambia
    "ZW": "ZWL",  # Zimbabwe
    "AX": "EUR",  # Åland Islands
}


def get_currency_for_user(update: Update) -> str:
    # Try to get country code from Telegram user or fallback to USD
    country_code = None
    if update.effective_user and update.effective_user.language_code:
        # Optionally, use a mapping from language_code to country_code
        lang = update.effective_user.language_code.lower()
        if lang == "en":
            country_code = "US"
        elif lang == "sw":
            country_code = "KE"
        # Add more mappings as needed

    # Optionally, use IP geolocation here for more accuracy

    return COUNTRY_TO_CURRENCY.get(country_code, CURRENCY_DEFAULT)

def convert_price(amount_usd: float, target_currency: str) -> (int, str):
    """Convert USD price to target currency using exchangerate-api.com (or similar)."""
    if target_currency == "USD":
        return int(amount_usd * 100), "USD"
    try:
        # Example using exchangerate-api.com (replace with your API key)
        API_KEY = os.getenv("EXCHANGE_RATE_API_KEY")
        url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/pair/USD/{target_currency}/{amount_usd}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            converted = data.get("conversion_result", amount_usd)
            return int(round(converted * 100)), target_currency
    except Exception:
        pass
    # Fallback to USD if conversion fails
    return int(amount_usd * 100), "USD"

async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_currency = get_currency_for_user(update)
    price_cents, currency = convert_price(SUBSCRIPTION_PRICE_USD, user_currency)
    keyboard = [
        [InlineKeyboardButton(f"Pay with Card ({currency})", callback_data=f"pay_card_{currency}")],
        [InlineKeyboardButton("Pay with Mpesa", callback_data="pay_mpesa")],
        [InlineKeyboardButton("Pay with PayPal", url=PAYPAL_LINK)],
        [InlineKeyboardButton("Direct Bank Deposit", callback_data="pay_bank")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text(
            f"Choose your payment method for subscription:\n"
            f"Subscription price: {price_cents/100:.2f} {currency}",
            reply_markup=reply_markup
        )

def send_invoice_email(to_email: str, amount: float, currency: str):
    smtp_server = os.getenv("MAIL_SERVER")
    smtp_port = int(os.getenv("MAIL_PORT", 587))
    smtp_user = os.getenv("MAIL_USERNAME")
    smtp_pass = os.getenv("MAIL_PASSWORD")
    sender = os.getenv("MAIL_DEFAULT_SENDER", smtp_user)

    subject = "Your Trading Bot Subscription Invoice"
    body = (
        f"Thank you for subscribing!\n\n"
        f"Invoice Details:\n"
        f"Amount: {amount:.2f} {currency}\n"
        f"If you have any questions, reply to this email."
    )

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if os.getenv("MAIL_USE_TLS", "True").lower() == "true":
                server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(sender, to_email, msg.as_string())
    except Exception as e:
        print(f"Failed to send invoice email: {e}")

async def subscribe_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("pay_card"):
        # Extract currency from callback_data
        parts = data.split("_")
        currency = parts[-1] if len(parts) > 2 else "USD"
        price_cents, currency = convert_price(SUBSCRIPTION_PRICE_USD, currency)
        prices = [LabeledPrice(f"Monthly Subscription ({currency})", price_cents)]
        await query.message.reply_invoice(
            title="Trading Bot Subscription",
            description=f"Access premium trading signals for 1 month. ({currency})",
            payload="subscription_payload",
            provider_token=PROVIDER_TOKEN,
            currency=currency,
            prices=prices,
            need_name=True,
            need_email=True,
        )
        # Send invoice email if user email is available
        user_email = None
        if update.effective_user and update.effective_user.email:
            user_email = update.effective_user.email
        # If you collect email elsewhere, update this logic accordingly
        if user_email:
            send_invoice_email(user_email, price_cents / 100, currency)
    elif data == "pay_mpesa":
        await query.message.reply_text(
            f"Send payment via Mpesa to {MPESA_NUMBER}.\n"
            "After payment, send your transaction code here for manual verification."
        )
    elif data == "pay_bank":
        await query.message.reply_text(
            f"Deposit to:\n{BANK_DETAILS}\n"
            "After payment, send your transaction reference here for manual verification."
        )

async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    email = None
    if payment.order_info and payment.order_info.email:
        email = payment.order_info.email
        # Store securely (example: in-memory for session)
        context.user_data['user_email'] = email
        # Or save to your database here