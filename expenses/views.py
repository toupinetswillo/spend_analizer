from django.shortcuts import render, redirect
from .models import Receipt, Expense
from .forms import ReceiptForm, CSVUploadForm
import pytesseract
import json
from PIL import Image
from django.contrib.auth.decorators import login_required
import csv
from io import TextIOWrapper
from datetime import datetime
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Sum


@login_required
def upload_receipt(request):
    if request.method == 'POST':
        form = ReceiptForm(request.POST, request.FILES)
        if form.is_valid():
            receipt = form.save(commit=False)
            receipt.user = request.user
            receipt.save()

            # OCR processing
            image_path = receipt.image.path
            text = pytesseract.image_to_string(Image.open(image_path))

            # Process the extracted text (basic example)
            # This can be improved to parse text into categories, amounts, etc.
            # For simplicity, we add it as a single "uncategorized" expense
            Expense.objects.create(
                receipt=receipt,
                category='Uncategorized',
                amount=0,  # You'd extract this from OCR in real scenario
                description=text
            )
            return redirect('expenses:index')
    else:
        form = ReceiptForm()

    return render(request, 'expenses/upload.html', {'form': form})

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
    expenses_by_category = expenses.values('category', 'transaction_date__month').annotate(total=Sum('amount')).order_by('transaction_date__month')

    # Prepare data for the chart
    categories = set()
    data_by_month = {month: {} for month in range(1, 13)}

    total_in_year = 0
    # Fill the data_by_month dictionary
    for expense in expenses_by_category:
        month = expense['transaction_date__month']
        category = expense['category']
        total = float(expense['total'])
        if category not in data_by_month[month]:
            data_by_month[month][category] = 0
        data_by_month[month][category] += total
        categories.add(category)
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
            for row in reader:
                try:
                    # Assuming the CSV columns: amount, category, description, date
                    trans_date = datetime.strptime(row[0], '%m/%d/%Y')
                    post_date = datetime.strptime(row[1], '%m/%d/%Y')
                    merchant = row[2]
                    amount = float(row[3])
                    category = row[4]

                    # Create a new expense entry
                    Expense.objects.create(
                        receipt=None,  # Optional - link to a receipt if relevant
                        category=category,
                        amount=amount,
                        merchant=merchant,
                        transaction_date=trans_date,
                        post_date=post_date
                    )
                except Exception as e:
                    print(f"Error processing row {row}: {e}")

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
