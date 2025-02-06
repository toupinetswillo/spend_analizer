from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.files.storage import default_storage
from .models import Receipt, Expense, ExpenseItem
from .forms import ReceiptForm, CSVUploadForm
import pytesseract
import json
from PIL import Image
from django.contrib.auth.decorators import login_required
import csv
from io import TextIOWrapper
from datetime import datetime
from django.db.models import Sum
from .utils import parse_receipt, preprocess_image, skew_correction, show_image
import cv2
import boto3
from django.conf import settings
import numpy as np

s3 = boto3.client('s3')
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
@login_required
def upload_receipt(request):
  if request.method == 'POST':
    images = []
    receipts = []
    receipt_urls = []
    s3_bucket = settings.AWS_STORAGE_BUCKET_NAME
    for upload_file in request.FILES.getlist('files'):
      rimage = Receipt.objects.create(image=upload_file)
      receipts.append(rimage)
      receipt_urls.append(rimage.image.url)
      s3_key = rimage.image.name
      s3_object = s3.get_object(Bucket=s3_bucket, Key=s3_key)
      image_data = s3_object['Body'].read()

      image_np = np.asarray(bytearray(image_data), dtype="uint8")

      image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
      images.append(image)

    items = []
    total = 0
    date = None
    for image in images:
      if image is not None:
        resized = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        # show_image('Gray Image', gray)
        # binary_image = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        # show_image('Binary Image', binary_image)
        denoised_image = cv2.GaussianBlur(gray, (5, 5), 0)
        # show_image('Denoised Image', denoised_image)
        # Use a morphological operation to remove noise
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        morph_image = cv2.morphologyEx(denoised_image, cv2.MORPH_CLOSE, kernel)
        # show_image('Morph Image', morph_image)
        # Set tesseract configuration for OCR
        config = '--oem 3 --psm 6'
        text = pytesseract.image_to_string(morph_image, config=config, lang='eng')
        data = parse_receipt(text)
        total = data['total'] if data['total'] else total
        date = data['date'] if data['date'] else date
        items.extend(data['items'])
      else:
        print("Failed to load image.")



    formatted_date = None
    if date:
      try:
          # Try parsing with four-digit year first
          formatted_date = datetime.strptime(date, '%m/%d/%Y').strftime("%Y-%m-%d")
      except ValueError:
          # If parsing fails, try with two-digit year
          formatted_date = datetime.strptime(date, '%m/%d/%y').strftime("%Y-%m-%d")
    print(data)
    expense, created = Expense.objects.get_or_create(
      amount=total,
      post_date=formatted_date if date else None,
      category='Supermarket',
      defaults={
          "merchant": 'Not specified',
          "category": 'Supermarket',
          "transaction_date": formatted_date if date else datetime.now(),
          "post_date": formatted_date if formatted_date else datetime.now(),
      }
    )

    if created:
      for receipt in receipts:
          expense.receipts.add(receipt)
      expense.save()
    elif expense.receipts.count() == 0:
      for receipt in receipts:
          expense.receipts.add(receipt)
      expense.save()



    ommit_items = ['total', 'amount', 'tax', 'subtotal', 'reg', 'SALES', 'CHANGE', 'are Di scover', 'Discover', 'DISCOVER', 'BALANCE']
    records = []
    for item in items:
      omit = False
      for ommit_item in ommit_items:
          if ommit_item.lower() in item['description'].lower():
              omit = True
              break
      if omit:
          continue

      record = ExpenseItem.objects.create(
          description=item['description'],
          total=item['total'],
          price=item['price'],
          expense=expense
      )
      records.append(record)
    return render(request, 'expenses/upload.html', {'records': records, 'expense': expense, 'uploaded_file_urls': receipt_urls})
  else:
    return render(request, 'expenses/upload.html')

@login_required
def list(request):
    # Get selected year for filtering
    selected_year = request.GET.get('year')

    # Fetch all expenses or filter by the selected year
    if selected_year:
        expenses = Expense.objects.filter(transaction_date__year=selected_year).exclude(merchant="INTERNET PAYMENT - THANK YOU")
    else:
        expenses = Expense.objects.all().exclude(merchant="INTERNET PAYMENT - THANK YOU")

    # Group expenses by category and month, summing the amounts
    expenses_by_category = expenses.exclude(transaction_date=None).values('category', 'transaction_date__month').annotate(total=Sum('amount')).order_by('transaction_date__month')

    # Prepare data for the chart
    categories = set()
    data_by_month = {month: {} for month in range(1, 13)}

    total_in_year = 0
    # Fill the data_by_month dictionary
    for expense in expenses_by_category:
        month = expense['transaction_date__month']
        category = expense['category']
        total = float(expense['total']) if expense['total'] else 0
        if category not in data_by_month[month]:
            data_by_month[month][category] = 0
        data_by_month[month][category] += total
        categories.add(category)
        if total > 0:
          total_in_year += total

    # Sort categories to maintain consistent order in chart
    categories = sorted(categories)

    # Prepare datasets for the chart
    chart_data = {
        'categories': categories,
        'data_by_month': data_by_month,
    }

    # Get distinct years for filtering dropdown
    years = Expense.objects.dates('transaction_date', 'year', order='DESC')

    return render(request, 'expenses/list.html', {
        'chart_data': json.dumps(chart_data),
        'years': years,
        'selected_year': selected_year,
        'total': total_in_year
    })


@login_required
def index(request):
    return redirect('expenses:list')

@login_required
def upload_csv(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Read the uploaded file
            csv_file = TextIOWrapper(request.FILES['csv_file'].file, encoding='utf-8')
            reader = csv.reader(csv_file)

            # Skip header row (if necessary)
            next(reader, None)

            # Process each row in the CSV
            created_records_number = 0
            for row in reader:
                try:
                    # Assuming the CSV columns: amount, category, description, date
                    trans_date = datetime.strptime(row[0], '%m/%d/%Y')
                    post_date = datetime.strptime(row[1], '%m/%d/%Y')
                    merchant = row[2]
                    amount = float(row[3])
                    category = row[4]

                    # Create a new expense entry
                    _, created = Expense.objects.get_or_create(
                        category=category,
                        amount=amount,
                        merchant=merchant,
                        transaction_date=trans_date,
                        post_date=post_date,
                        defaults={
                            'receipt': None,  # Optional - link to a receipt if relevant
                            'description': ''  # Optional - add a description if needed
                        }
                    )
                    if created:
                        created_records_number += 1
                except Exception as e:
                    print(f"Error processing row {row}: {e}")
            print(f"Created {created_records_number} records")
            return redirect('expenses:index')
    else:
        form = CSVUploadForm()

    return render(request, 'expenses/upload_csv.html', {'form': form})


@login_required
def expense_details(request):
    month = request.GET.get('month')
    category = request.GET.get('category')
    year = request.GET.get('year')

    # Fetch the expenses filtered by the selected month and category
    expenses = Expense.objects.filter(
        transaction_date__month=month,
        transaction_date__year=year,
        category=category
      )

    return render(request, 'expenses/expense_details.html', {
        'expenses': expenses,
        'month': month,
        'category': category,
        'year': year
    })


def update_expenses_items(request):
   if request.method == 'POST':
      data = json.loads(request.body)
      for item in data:
         expense_item = ExpenseItem.objects.get(id=item['id'])
         expense_item.description = item['description']
         expense_item.price = item['price']
         expense_item.save()
      return JsonResponse({'message': 'Items updated successfully!'}, status=200)


def update_expense_info(request):
   if request.method == 'POST':
      data = json.loads(request.body)
      expense = Expense.objects.get(id=data['id'])
      expense.category = data['category']
      expense.merchant = data['merchant']
      expense.save()
      return JsonResponse({'message': 'Expense updated successfully!'}, status=200)

def remove_receipt(request, receipt_id):
  receipt = Expense.objects.get(id=receipt_id)
  receipt.delete()
  return JsonResponse({'message': 'Receipt removed successfully!'}, status=200)
