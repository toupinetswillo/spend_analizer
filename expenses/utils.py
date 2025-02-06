import re
import cv2
import pytesseract
from PIL import Image
import numpy as np

# Path to Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'  # Update this path as needed

def parse_receipt(text):
    # Initialize the receipt data dictionary
    receipt_data = {
        'total': None,
        'items': [],
        'date': None
    }

    # Split the text into lines for easier processing
    lines = text.splitlines()

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

def preprocess_image(image_path):
    """
    Preprocess the image before passing to Tesseract for better OCR accuracy.
    Includes resizing, grayscaling, thresholding, denoising, and skew correction.
    """
    # Read the image using OpenCV
    image = cv2.imread(image_path)

    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Resize the image (scale it up for clearer text)
    resized = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)


    # Apply thresholding (Binarization using Otsu's thresholding)
    _, binary_image = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Remove noise
    denoised_image = cv2.fastNlMeansDenoising(binary_image, None, 30, 7, 21)

    # Skew correction
    corrected_image = skew_correction(denoised_image)

    return corrected_image

def skew_correction(image):
    """
    Corrects skew in the image.
    """
    coords = np.column_stack(np.where(image > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    return rotated

def extract_text(image):
    """
    Extract text from the preprocessed image using Tesseract OCR.
    """
    # Tesseract configuration
    config = '--oem 1 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,!?'

    # Convert the OpenCV image to PIL format (Tesseract works better with PIL)
    pil_image = Image.fromarray(image)

    # Extract text from the image using Tesseract
    text = pytesseract.image_to_string(pil_image, config=config, lang='eng')

    return text

def main():
    # Path to the image file
    image_path = 'receipt.jpg'  # Update with your image path

    # Preprocess the image
    processed_image = preprocess_image(image_path)

    # Extract text from the processed image
    text = extract_text(processed_image)

    # Print the extracted text
    print("Extracted Text:")
    print(text)

if __name__ == "__main__":
    main()


# Apply skew correction (example using OpenCV)
def skew_correction(image):
    coords = np.column_stack(np.where(image > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated
