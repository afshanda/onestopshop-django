from django.core.checks import messages
from store.forms import ReviewForm
from django.core import paginator
from django.http import response
from django.http.response import HttpResponse
from carts.models import Cart, CartItem
from django.db.models.aggregates import Count
from django.shortcuts import get_object_or_404, redirect, render
from .import models
from category.models import category
from carts.models import CartItem, Cart
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.contrib import messages
from orders.models import OrderProduct

# Create your views here.
def store(request, category_slug = None):
    categories = None
    products = None
    
    #for selective category to be displayed
    if category_slug != None:
        categories = get_object_or_404(category, slug = category_slug)  
        products = models.Product.objects.filter(category = categories, is_available=True)
        product_count = products.count()

        paginator = Paginator(products, 6)
        page = request.GET.get('page')
        paged_product = paginator.get_page(page)

    #for all products
    else:
        products = models.Product.objects.all().filter(is_available = True).order_by('id')
        product_count = products.count()

        #Pagination Logis Starts here
        paginator = Paginator(products, 3)
        page = request.GET.get('page')
        paged_product = paginator.get_page(page)

    context = {
        'products' : paged_product,
        'product_count' : product_count,
        'page_title' : "Our Store"
    }
    return render(request, 'store/store.html', context)

def _is_cart(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def product_details(request, category_slug = None, product_slug = None):
    try:
        single_product = models.Product.objects.get(category__slug = category_slug, slug = product_slug)
        in_cart = CartItem.objects.filter(product = single_product, cart__cart_id = _is_cart(request)).exists()

    except Exception as e:
        raise e

    if request.user.is_authenticated:
        try:
            orderProduct  = OrderProduct.objects.filter(user = request.user , product = single_product).exists()
        except OrderProduct.DoesNotExist:
            orderProduct = None
    else:
        orderProduct = None
    
    # Review Rating in forms of star
    reviews = models.ReviewRating.objects.filter(product = single_product, status = True)

    # get the product gallery
    product_gallery = models.ProductGallery.objects.filter(product_id = single_product.id)

    context = {
        'single_product' : single_product,
        'in_cart' : in_cart,
        'orderProduct' : orderProduct,
        'reviews' : reviews,
        'product_gallery' : product_gallery,
    }
    return render(request, 'store/product_details.html', context)

def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET.get('keyword')

        if keyword:
            products = models.Product.objects.order_by().filter(Q(description__icontains = keyword) | Q(product_name__icontains = keyword))
            product_count = products.count()
    
    context = {
        'products' : products,
        'product_count' : product_count,
        'page_title' : "Search Result"
    }
    #return HttpResponse(keyword)
    return render(request, 'store/store.html', context)

def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            review = models.ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=review)
            form.save()
            messages.success(request, 'Your review has been updated')
            return redirect(url)

        except models.ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = models.ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.review = form.cleaned_data['review']
                data.rating = form.cleaned_data['rating']
                data.user_id = request.user.id
                data.product_id = product_id
                data.ip = request.META.get('REMOTE_ADDR')
                data.save()
                messages.success(request, 'Your review has been created')
                return redirect(url)