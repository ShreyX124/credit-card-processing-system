from app import db
from app.models.transaction import Transaction
from config.settings import Config
import pandas as pd
from sklearn.ensemble import IsolationForest
import numpy as np
from datetime import datetime, timedelta

class FraudDetectionService:
    @staticmethod
    def analyze_transaction(transaction, user_id):
        """
        Analyze a transaction for potential fraud
        Returns a fraud score (0-100) where higher is more likely to be fraud
        """
        # Get user's transaction history
        user_history = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.created_at.desc()).limit(20).all()
        
        # If this is the first transaction, use simple rules
        if not user_history:
            return FraudDetectionService._simple_fraud_check(transaction)
        
        # Combine rule-based and anomaly detection
        rule_score = FraudDetectionService._simple_fraud_check(transaction)
        anomaly_score = FraudDetectionService._anomaly_detection(transaction, user_history)
        
        # Combine scores (60% anomaly, 40% rule-based)
        combined_score = (anomaly_score * 0.6) + (rule_score * 0.4)
        
        return min(combined_score, 100)  # Cap at 100
    
    @staticmethod
    def _simple_fraud_check(transaction):
        """
        Simple rule-based fraud detection
        """
        score = 0
        
        # Check amount thresholds
        if transaction.amount > 1000:
            score += 15
        elif transaction.amount > 500:
            score += 10
        elif transaction.amount > 200:
            score += 5
        
        # Check transaction time (unusual hours)
        hour = datetime.utcnow().hour
        if 0 <= hour < 5:  # Transactions between midnight and 5am
            score += 10
        
        # Check for round amounts (often fraudulent)
        if transaction.amount == int(transaction.amount):
            score += 5
        
        return score
    
    @staticmethod
    def _anomaly_detection(transaction, history):
        """
        Use anomaly detection to identify unusual transactions
        """
        # Convert history to dataframe
        data = []
        for t in history:
            data.append({
                'amount': t.amount,
                'hour': t.created_at.hour,
                'day_of_week': t.created_at.weekday(),
                'days_since': (datetime.utcnow() - t.created_at).days
            })
        
        if not data:
            return 0
            
        # Add current transaction
        data.append({
            'amount': transaction.amount,
            'hour': datetime.utcnow().hour,
            'day_of_week': datetime.utcnow().weekday(),
            'days_since': 0
        })
        
        df = pd.DataFrame(data)
        
        try:
            # Use Isolation Forest for anomaly detection
            model = IsolationForest(contamination=0.1, random_state=42)
            df['scores'] = model.fit_predict(df[['amount', 'hour', 'day_of_week']])
            
            # Get anomaly score for current transaction (last row)
            anomaly_score = 1 if df['scores'].iloc[-1] == -1 else 0
            
            # Convert to 0-100 scale
            return anomaly_score * 100
        except Exception as e:
            print(f"Anomaly detection error: {e}")
            return 0

    @staticmethod
    def is_transaction_fraudulent(transaction, user_id):
        """
        Determine if a transaction is fraudulent based on the fraud score
        """
        fraud_score = FraudDetectionService.analyze_transaction(transaction, user_id)
        transaction.fraud_score = fraud_score
        
        # Mark as fraudulent if above threshold
        if fraud_score >= Config.FRAUD_DETECTION_THRESHOLD:
            transaction.is_fraudulent = True
            transaction.status = 'blocked'
            return True
        
        return False