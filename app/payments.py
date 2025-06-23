from app.models.user import activate_user_subscription, User

# In-memory payment code store for demo
_used_codes: set = set()

def process_payment_code(user: User, code: str) -> dict:
    if code in _used_codes or not user:
        return {"success": False, "error": "Code already used or user not found"}
    # TODO: Add real payment verification logic here
    _used_codes.add(code)
    activate_user_subscription(user.telegram_id or user.email)
    return {"success": True}

def process_stripe_webhook(payload, sig_header):
    # ...verify Stripe signature, parse event...
    # Return event dict or None
    pass

def process_paypal_webhook(data):
    # ...verify PayPal webhook, parse event...
    # Return event dict or None
    pass
