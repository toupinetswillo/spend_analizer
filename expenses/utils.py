import re

def parse_receipt(text):
    # Initialize the receipt data dictionary
    receipt_data = {
        'vendor': None,
        'date': None,
        'total': None,
        'items': []
    }

    # Split the text into lines for easier processing
    lines = text.splitlines()

    # Extract the vendor (usually appears at the top, so we can take the first non-empty line)
    for line in lines:
        if line.strip():  # Find the first non-empty line
            receipt_data['vendor'] = line.strip()
            break

    # Extract the date using a regular expression (matches formats like "01/25/2025" or "2025-01-25")
    date_pattern = r'\b(\d{2}/\d{2}/\d{4})\b|\b(\d{4}-\d{2}-\d{2})\b'
    for line in lines:
        date_match = re.search(date_pattern, line)
        if date_match:
            receipt_data['date'] = date_match.group(0)
            break

    # Extract line items and prices (looks for lines with a description followed by a price)
    item_pattern = r'(.+?)\s+(\$?\d+\.\d{2})'
    for line in lines:
        item_match = re.search(item_pattern, line)
        if item_match:
            description = item_match.group(1).strip()
            price = float(item_match.group(2).replace('$', '').strip())
            receipt_data['items'].append({
                'description': description,
                'price': price,
                'quantity': 1,  # Default quantity is 1; modify as necessary
                'total': price
            })

    # Extract the total (typically a line that starts with "Total")
    total_pattern = r'Total\s*[:]\s*\$?(\d+\.\d{2})'
    for line in lines:
        total_match = re.search(total_pattern, line)
        if total_match:
            receipt_data['total'] = float(total_match.group(1).strip())
            break

    return receipt_data
