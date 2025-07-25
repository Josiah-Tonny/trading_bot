from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import stripe
import os
import json
from app.models.models import User, Subscription, Payment

class PaymentService:
    def __init__(self, db: Session):
        self.db = db
        self.stripe = stripe
        self.stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        
        # Subscription pricing
        self.pricing = {
            'pro': {
                'monthly': 29.99,
                'setup_fee': 0.0
            },
            'premium': {
                'monthly': 99.99,
                'setup_fee': 0.0
            }
        }
        
        # Signal change fees
        self.signal_fees = {
            'free': 3.0,
            'pro': 1.50,
            'premium': 0.0
        }
        
    async def process_subscription_payment(self,
                                        user_id: int,
                                        tier: str,
                                        payment_method_id: str) -> Dict[str, Any]:
        """Process a subscription payment"""
        user = self.db.query(User).get(user_id)
        if not user:
            return {
                'success': False,
                'error': 'User not found'
            }
            
        try:
            amount = int(self.pricing[tier]['monthly'] * 100)  # Convert to cents
            
            # Create Stripe payment intent
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency='usd',
                payment_method=payment_method_id,
                customer=user.stripe_customer_id,
                confirm=True,
                description=f"{tier.title()} Subscription - {user.email or user.telegram_username}"
            )
            
            # Record payment
            payment = Payment(
                user_id=user_id,
                amount=amount / 100,  # Convert back to dollars
                type='subscription',
                status='completed' if intent.status == 'succeeded' else 'failed',
                payment_method='stripe',
                transaction_id=intent.id,
                provider_response=json.dumps(intent)
            )
            self.db.add(payment)
            
            if intent.status == 'succeeded':
                # Update user's subscription
                subscription = self.db.query(Subscription)\
                    .filter(Subscription.user_id == user_id)\
                    .first()
                    
                if subscription:
                    subscription.payment_status = 'completed'
                    subscription.features = json.dumps(self._get_tier_features(tier))
                    
                self.db.commit()
                
                return {
                    'success': True,
                    'payment_id': payment.id,
                    'subscription_updated': True
                }
            else:
                self.db.commit()
                return {
                    'success': False,
                    'error': 'Payment failed',
                    'payment_id': payment.id
                }
                
        except stripe.error.StripeError as e:
            # Handle Stripe errors
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            self.db.rollback()
            return {
                'success': False,
                'error': f'Payment processing failed: {str(e)}'
            }
            
    async def process_signal_change_payment(self,
                                         user_id: int,
                                         payment_method_id: str) -> Dict[str, Any]:
        """Process payment for signal change"""
        user = self.db.query(User).get(user_id)
        if not user:
            return {
                'success': False,
                'error': 'User not found'
            }
            
        # Get user's subscription tier
        subscription = self.db.query(Subscription)\
            .filter(Subscription.user_id == user_id)\
            .filter(Subscription.end_date > datetime.now(timezone.utc))\
            .first()
            
        if not subscription:
            return {
                'success': False,
                'error': 'No active subscription found'
            }
            
        fee = self.signal_fees.get(subscription.tier, 3.0)
        if fee == 0:
            return {
                'success': True,
                'fee_required': False
            }
            
        try:
            amount = int(fee * 100)  # Convert to cents
            
            # Create Stripe payment intent
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency='usd',
                payment_method=payment_method_id,
                customer=user.stripe_customer_id,
                confirm=True,
                description=f"Signal Change - {user.email or user.telegram_username}"
            )
            
            # Record payment
            payment = Payment(
                user_id=user_id,
                amount=fee,
                type='signal_change',
                status='completed' if intent.status == 'succeeded' else 'failed',
                payment_method='stripe',
                transaction_id=intent.id,
                provider_response=json.dumps(intent)
            )
            self.db.add(payment)
            self.db.commit()
            
            return {
                'success': intent.status == 'succeeded',
                'payment_id': payment.id
            }
            
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            self.db.rollback()
            return {
                'success': False,
                'error': f'Payment processing failed: {str(e)}'
            }
            
    def setup_customer(self, user: User) -> Optional[str]:
        """Create or retrieve Stripe customer for user"""
        if user.stripe_customer_id:
            return user.stripe_customer_id
            
        try:
            # Create new customer
            customer = stripe.Customer.create(
                email=user.email,
                name=user.full_name,
                metadata={
                    'user_id': user.id,
                    'telegram_id': user.telegram_user_id
                }
            )
            
            user.stripe_customer_id = customer.id
            self.db.commit()
            
            return customer.id
            
        except Exception as e:
            print(f"Failed to create Stripe customer: {e}")
            return None
            
    def _get_tier_features(self, tier: str) -> Dict[str, bool]:
        """Get features enabled for a subscription tier"""
        features = {
            'free': {
                'basic_signals': True,
                'ai_consultation': True,
                'sentiment_analysis': True
            },
            'pro': {
                'basic_signals': True,
                'advanced_signals': True,
                'ai_consultation': True,
                'sentiment_analysis': True,
                'risk_analysis': True,
                'educational_resources': True
            },
            'premium': {
                'basic_signals': True,
                'advanced_signals': True,
                'ai_consultation': True,
                'sentiment_analysis': True,
                'risk_analysis': True,
                'educational_resources': True,
                'portfolio_optimization': True,
                'custom_strategy': True,
                'priority_alerts': True
            }
        }
        
        return features.get(tier, features['free'])
