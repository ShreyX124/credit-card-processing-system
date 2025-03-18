import uuid
import random
from datetime import datetime
from app import db
from app.models.transaction import Transaction
from app.services.fraud_detection import FraudDetectionService

class PaymentGateway:
    @staticmethod
    def process_payment(user_id, merchant_id, card_id, amount, currency='USD', description=None):
        """
        Process a payment transaction
        """
        try:
            # Generate reference number
            reference = PaymentGateway._generate_reference()
            
            # Create transaction record
            transaction = Transaction(
                user_id=user_id,
                merchant_id=merchant_id,
                card_id=card_id,
                amount=amount,
                currency=currency,
                description=description,
                reference_number=reference,
                status='pending'
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            # Run fraud detection
            is_fraudulent = FraudDetectionService.is_transaction_fraudulent(transaction, user_id)
            
            if is_fraudulent:
                db.session.commit()
                return {
                    'success': False,
                    'message': 'Transaction was flagged for potential fraud',
                    'reference': reference,
                    'status': 'blocked'
                }
            
            # Simulate payment processing
            success = PaymentGateway._simulate_payment_processing()
            
            if success:
                transaction.status = 'completed'
                db.session.commit()
                return {
                    'success': True,
                    'message': 'Payment processed successfully',
                    'reference': reference,
                    'status': 'completed'
                }
            else:
                transaction.status = 'failed'
                db.session.commit()
                return {
                    'success': False,
                    'message': 'Payment processing failed',
                    'reference': reference,
                    'status': 'failed'
                }
                
        except Exception as e:
            db.session.rollback()
            print(f"Payment processing error: {e}")
            return {
                'success': False,
                'message': f'An error occurred: {str(e)}',
                'status': 'error'
            }
    
    @staticmethod
    def refund_transaction(transaction_id, amount=None, reason=None):
        """
        Process a refund for a transaction
        """
        try:
            # Find the original transaction
            transaction = Transaction.query.get(transaction_id)
            
            if not transaction:
                return {
                    'success': False,
                    'message': 'Transaction not found'
                }
            
            if transaction.status != 'completed':
                return {
                    'success': False,
                    'message': f'Cannot refund a transaction with status: {transaction.status}'
                }
            
            # If no amount is specified, refund the full amount
            refund_amount = amount if amount else transaction.amount
            
            if refund_amount > transaction.amount:
                return {
                    'success': False,
                    'message': 'Refund amount cannot exceed the original transaction amount'
                }
            
            # Create refund transaction
            refund = Transaction(
                user_id=transaction.user_id,
                merchant_id=transaction.merchant_id,
                card_id=transaction.card_id,
                amount=refund_amount,
                currency=transaction.currency,
                description=f"Refund for transaction {transaction.reference_number}: {reason}" if reason else f"Refund for transaction {transaction.reference_number}",
                reference_number=PaymentGateway._generate_reference(),
                transaction_type='refund',
                status='pending'
            )
            
            db.session.add(refund)
            
            # Process the refund
            success = PaymentGateway._simulate_payment_processing(success_rate=95)
            
            if success:
                refund.status = 'completed'
                db.session.commit()
                return {
                    'success': True,
                    'message': 'Refund processed successfully',
                    'reference': refund.reference_number,
                    'status': 'completed'
                }
            else:
                refund.status = 'failed'
                db.session.commit()
                return {
                    'success': False,
                    'message': 'Refund processing failed',
                    'reference': refund.reference_number,
                    'status': 'failed'
                }
                
        except Exception as e:
            db.session.rollback()
            print(f"Refund processing error: {e}")
            return {
                'success': False,
                'message': f'An error occurred: {str(e)}',
                'status': 'error'
            }
    
    @staticmethod
    def _generate_reference():
        """
        Generate a unique reference number for transactions
        """
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M')
        random_part = str(random.randint(1000, 9999))
        return f"TX-{timestamp}-{random_part}"
    
    @staticmethod
    def _simulate_payment_processing(success_rate=90):
        """
        Simulate payment processing with a given success rate
        """
        return random.randint(1, 100) <= success_rate