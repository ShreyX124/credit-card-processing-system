import re
from datetime import datetime

# Credit card validation functions
def validate_card_number(card_number):
    """
    Validate credit card number using Luhn algorithm
    """
    # Remove spaces and dashes
    card_number = card_number.replace(' ', '').replace('-', '')
    
    # Check if the number contains only digits
    if not card_number.isdigit():
        return False
    
    # Check for valid length (most cards are 13-19 digits)
    if not 13 <= len(card_number) <= 19:
        return False
    
    # Luhn algorithm
    digits = [int(d) for d in card_number]
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(divmod(d * 2, 10))
    return checksum % 10 == 0

def validate_expiry_date(month, year):
    """
    Validate that the expiry date is in the future
    """
    now = datetime.now()
    expiry_date = datetime(year=year, month=month, day=1)
    
    # Add a month to get the end of the month
    if month == 12:
        expiry_date = datetime(year=year + 1, month=1, day=1)
    else:
        expiry_date = datetime(year=year, month=month + 1, day=1)
    
    return expiry_date > now

def validate_cvv(cvv, card_type=None):
    """
    Validate CVV based on card type
    """
    if not cvv.isdigit():
        return False
    
    # AMEX has 4 digit CVV, others have 3
    if card_type and card_type.lower() == 'amex':
        return len(cvv) == 4
    return len(cvv) == 3

def get_card_type(card_number):
    """
    Identify the card type based on the card number
    """
    card_number = card_number.replace(' ', '').replace('-', '')
    
    # Define regex patterns for different card types
    patterns = {
        'amex': r'^3[47][0-9]{13}$',
        'visa': r'^4[0-9]{12}(?:[0-9]{3})?$',
        'mastercard': r'^5[1-5][0-9]{14}$',
        'discover': r'^6(?:011|5[0-9]{2})[0-9]{12}$',
    }
    
    # Check against each pattern
    for card_type, pattern in patterns.items():
        if re.match(pattern, card_number):
            return card_type
    
    return 'unknown'