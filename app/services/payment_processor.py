import os
from datetime import datetime, timezone
from typing import Dict, Optional, Any, Union, Literal, TypedDict, cast
from decimal import Decimal
import stripe
from sqlalchemy.orm import Session
from app.models.models import User, Payment, Subscription
from app.services.subscription_pricing import SubscriptionPricing
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Configure stripe
stripe.api_version = "2022-11-15"  # Use a specific API version

# Type definitions
StripePaymentIntent = Dict[str, Any]  # Type for Stripe payment intent
PaymentMethodType = Literal['stripe', 'mpesa', 'paypal', 'bank_transfer']
PaymentStatus = Literal['pending', 'completed', 'failed', 'refunded']

class PaymentResult(TypedDict, total=False):
    success: bool
    message: str
    fee: float
    transaction_id: str

class StripeError(Exception):
    pass

PaymentDetails = Dict[str, str]

class PaymentProcessor:
    def __init__(self, db: Session):
        self.db = db
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        if not stripe.api_key:
            logger.warning("Stripe API key not configured")
        
    async def process_signal_change_payment(
        self, 
        user_id: int, 
        payment_method: PaymentMethodType,
        payment_details: Dict[str, Any]
    ) -> PaymentResult:
        """Process payment for signal change"""
        try:
            # Get user's subscription and fee amount
            subscription = self.db.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.end_date > datetime.now(timezone.utc)
            ).first()
            
            if not subscription:
                return {"success": False, "message": "No active subscription"}
                
            fee = SubscriptionPricing.calculate_signal_change_fee(subscription.tier)
            
            if fee == 0:
                return {"success": True, "message": "No payment required"}
                
            # Process payment based on method
            payment_result = await self._process_payment(
                amount=fee,
                payment_method=payment_method,
                payment_details=payment_details
            )
            
            if payment_result["success"]:
                # Record payment
                payment = Payment(
                    user_id=user_id,
                    amount=float(fee),
                    type="signal_change",
                    status="completed",
                    timestamp=datetime.now(timezone.utc)
                )
                self.db.add(payment)
                self.db.commit()
                
                # Update subscription
                subscription.signal_change_count = subscription.signal_change_count + 1
                self.db.commit()
                
            return payment_result
            
        except Exception as e:
            logger.error(f"Payment processing error: {str(e)}")
            self.db.rollback()
            return {"success": False, "message": str(e)}
            
    async def _process_payment(
        self,
        amount: Decimal,
        payment_method: PaymentMethodType,
        payment_details: Dict[str, Any]
    ) -> PaymentResult:
        """Process payment through various payment methods"""
        try:
            if payment_method == "stripe":
                return await self._process_stripe_payment(amount, payment_details)
            elif payment_method == "mpesa":
                return await self._process_mpesa_payment(amount, payment_details)
            else:
                raise ValueError(f"Unsupported payment method: {payment_method}")
                
        except Exception as e:
            logger.error(f"Payment method processing error: {str(e)}")
            return {"success": False, "message": str(e)}
            
    async def _process_stripe_payment(
        self, 
        amount: Decimal, 
        payment_details: Dict[str, Any]
    ) -> PaymentResult:
        """Process payment through Stripe"""
        try:
            payment_intent = await stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency="usd",
                payment_method=payment_details.get("payment_method_id"),
                confirm=True
            )
            
            return {
                "success": True,
                "message": "Payment processed successfully",
                "transaction_id": payment_intent.id
            }
            
        except stripe.error.CardError as e:
            logger.error(f"Stripe card error: {str(e)}")
            return {"success": False, "message": f"Card error: {str(e)}"}
        except Exception as e:
            logger.error(f"Stripe payment error: {str(e)}")
            return {"success": False, "message": str(e)}
            
    async def _process_mpesa_payment(
        self, 
        amount: Decimal, 
        payment_details: Dict[str, Any]
    ) -> PaymentResult:
        """Process payment through M-Pesa"""
        # Implement M-Pesa payment logic here
        try:
            # TODO: Implement actual M-Pesa integration
            return {
                "success": True,
                "message": "M-Pesa payment processed",
                "transaction_id": "MPESA" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            }
        except Exception as e:
            logger.error(f"M-Pesa payment error: {str(e)}")
            return {"success": False, "message": str(e)}
        
    async def process_signal_change_payment(
        self, 
        user_id: int, 
        payment_method: str,
        payment_details: Dict
    ) -> Dict[str, bool | str | float]:
        """Process payment for signal change"""
        try:
            # Get user's subscription and fee amount
            subscription = self.db.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.end_date > datetime.utcnow()
            ).first()
            
            if not subscription:
                return {"success": False, "message": "No active subscription"}
                
            fee = SubscriptionPricing.calculate_signal_change_fee(subscription.tier)
            
            if fee == 0:
                return {"success": True, "message": "No payment required"}
                
            # Process payment based on method
            payment_result = await self._process_payment(
                amount=fee,
                payment_method=payment_method,
                payment_details=payment_details
            )
            
            if payment_result["success"]:
                # Record payment
                payment = Payment(
                    user_id=user_id,
                    amount=float(fee),
                    type="signal_change",
                    status="completed",
                    timestamp=datetime.utcnow()
                )
                self.db.add(payment)
                self.db.commit()
                
            return payment_result
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "message": str(e)}
            
    async def _process_payment(
        self,
        amount: Decimal,
        payment_method: str,
        payment_details: Dict
    ) -> Dict[str, bool | str]:
        """Process payment through various payment methods"""
        try:
            if payment_method == "stripe":
                return await self._process_stripe_payment(amount, payment_details)
            elif payment_method == "mpesa":
                return await self._process_mpesa_payment(amount, payment_details)
            else:
                return {"success": False, "message": "Unsupported payment method"}
                
        except Exception as e:
            return {"success": False, "message": str(e)}
            
    async def _process_stripe_payment(self, amount: Decimal, payment_details: Dict) -> Dict[str, bool | str]:
        """Process payment through Stripe"""
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency="usd",
                payment_method=payment_details.get("payment_method_id"),
                confirm=True
            )
            
            return {
                "success": True,
                "message": "Payment processed successfully",
                "transaction_id": payment_intent.id
            }
            
        except stripe.error.CardError as e:
            return {"success": False, "message": f"Card error: {str(e)}"}
        except Exception as e:
            return {"success": False, "message": str(e)}
            
    async def _process_mpesa_payment(self, amount: Decimal, payment_details: Dict) -> Dict[str, bool | str]:
        """Process payment through M-Pesa"""
        # Implement M-Pesa payment logic here
        # This is a placeholder for the actual implementation
        return {
            "success": True,
            "message": "M-Pesa payment processed",
            "transaction_id": "MPESA123456789"
        }
