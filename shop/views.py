from django.shortcuts import render
from .models import Product, Contact, Orders, OrderUpdate
from math import ceil
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

import razorpay
from django.conf import settings


# =========================================================
# HOME
# =========================================================

def index(request):

    allProds = []

    catprods = Product.objects.values('category', 'id')

    cats = {item['category'] for item in catprods}

    for cat in cats:

        prod = Product.objects.filter(category=cat)

        n = len(prod)

        nSlides = n // 4 + ceil((n / 4) - (n // 4))

        allProds.append([
            prod,
            range(1, nSlides),
            nSlides
        ])

    params = {
        'allProds': allProds
    }

    return render(
        request,
        'shop/index.html',
        params
    )


# =========================================================
# ABOUT
# =========================================================

def about(request):

    return render(
        request,
        'shop/about.html'
    )


# =========================================================
# CONTACT
# =========================================================

def contact(request):

    thank = False

    if request.method == "POST":

        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        desc = request.POST.get('desc', '')

        contact = Contact(
            name=name,
            email=email,
            phone=phone,
            desc=desc
        )

        contact.save()

        thank = True

    return render(
        request,
        'shop/contact.html',
        {
            'thank': thank
        }
    )


# =========================================================
# TRACKER
# =========================================================


def tracker(request):
    if request.method=="POST":
        orderId = request.POST.get('orderId', '')
        email = request.POST.get('email', '')
        try:
            order = Orders.objects.filter(order_id=orderId, email=email)
            if len(order)>0:
                update = OrderUpdate.objects.filter(order_id=orderId)
                updates = []
                for item in update:
                    updates.append({'text': item.update_desc, 'time': item.timestamp})
                    response = json.dumps({"status":"success", "updates": updates, "itemsJson": order[0].items_json}, default=str)
                return HttpResponse(response)
            else:
                return HttpResponse('{"status":"noitem"}')
        except Exception as e:
            return HttpResponse('{"status":"error"}')

    return render(request, 'shop/tracker.html')

# =========================================================
# SEARCH
# =========================================================
def searchMatch(query, item):
    if query in item.product_name.lower()or query in item.category:
        return True
    else:
        return False
def search(request):
    query= request.GET.get('search')
    allProds = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prodtemp = Product.objects.filter(category=cat)
        prod=[item for item in prodtemp if searchMatch(query, item)]
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        if len(prod)!= 0:
            allProds.append([prod, range(1, nSlides), nSlides])
    params = {'allProds': allProds, "msg":""}
    if len(allProds)==0 or len(query)<4:
        params={'msg':"Please make sure to enter relevant search query"}
    return render(request, 'shop/search.html', params)

# =========================================================
# PRODUCT VIEW
# =========================================================

def productView(request, myid):

    product = Product.objects.filter(
        id=myid
    )

    return render(
        request,
        'shop/prodView.html',
        {
            'product': product[0]
        }
    )


# =========================================================
# CHECKOUT + RAZORPAY
# =========================================================

def checkout(request):

    if request.method == "POST":

        items_json = request.POST.get(
            'itemsJson',
            ''
        )

        name = request.POST.get(
            'name',
            ''
        )

        amount = request.POST.get(
            'amount',
            ''
        )

        email = request.POST.get(
            'email',
            ''
        )

        address = (
            request.POST.get('address1', '')
            + " "
            + request.POST.get('address2', '')
        )

        city = request.POST.get(
            'city',
            ''
        )

        state = request.POST.get(
            'state',
            ''
        )

        zip_code = request.POST.get(
            'zip_code',
            ''
        )

        phone = request.POST.get(
            'phone',
            ''
        )

        # =================================================
        # CREATE ORDER
        # =================================================

        order = Orders(
            items_json=items_json,
            name=name,
            email=email,
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            phone=phone,
            amount=amount
        )

        order.save()

        # =================================================
        # CREATE ORDER UPDATE
        # =================================================

        update = OrderUpdate(
            order_id=order.order_id,
            update_desc="The order has been placed"
        )

        update.save()

        # =================================================
        # RAZORPAY CLIENT
        # =================================================

        client = razorpay.Client(
            auth=(
                settings.RAZORPAY_KEY_ID,
                settings.RAZORPAY_KEY_SECRET
            )
        )

        # =================================================
        # CREATE RAZORPAY ORDER
        # Amount must be in paise
        # =================================================

        payment = client.order.create({
            'amount': int(float(amount) * 100),
            'currency': 'INR',
            'payment_capture': 1
        })

        # =================================================
        # SEND DATA TO PAYMENT PAGE
        # =================================================

        return render(
            request,
            'shop/payment.html',
            {
                'payment': payment,
                'order': order,
                'amount': amount,
                'razorpay_key_id': settings.RAZORPAY_KEY_ID
            }
        )

    return render(
        request,
        'shop/checkout.html'
    )


# =========================================================
# RAZORPAY PAYMENT SUCCESS
# =========================================================

@csrf_exempt
def payment_success(request):

    if request.method == "POST":

        order_id = request.POST.get(
            'order_id',
            ''
        )

        payment_id = request.POST.get(
            'razorpay_payment_id',
            ''
        )

        razorpay_order_id = request.POST.get(
            'razorpay_order_id',
            ''
        )

        razorpay_signature = request.POST.get(
            'razorpay_signature',
            ''
        )

        # =================================================
        # VERIFY PAYMENT
        # =================================================

        client = razorpay.Client(
            auth=(
                settings.RAZORPAY_KEY_ID,
                settings.RAZORPAY_KEY_SECRET
            )
        )

        try:

            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': razorpay_signature
            })

            # =================================================
            # PAYMENT SUCCESS
            # =================================================

            order = Orders.objects.get(
                order_id=order_id
            )

            update = OrderUpdate(
                order_id=order.order_id,
                update_desc="Payment successful"
            )

            update.save()

            return render(
                request,
                'shop/paymentstatus.html',
                {
                    'order': order,
                    'payment_id': payment_id,
                    'status': 'Success'
                }
            )

        except Exception as e:

            return render(
                request,
                'shop/paymentstatus.html',
                {
                    'order_id': order_id,
                    'status': 'Failed',
                    'error': str(e)
                }
            )

    return render(
        request,
        'shop/paymentstatus.html',
        {
            'status': 'Failed'
        }
    )