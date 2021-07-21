from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, render, get_object_or_404
from store.models import Product, Variation
from .models import Cart, CartItem
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

# Create your views here.
def cart(request, total = 0, quantity = 0, cart_items = None):
    tax =0
    grand_total = 0
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user = request.user, is_active = True)
        else:
            cart = Cart.objects.get(cart_id = _cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active = True)

        for cart_item in cart_items:
            total += (cart_item.qunatity * cart_item.product.price)
            quantity += cart_item.qunatity
        tax = (2 * total)/100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass

    context = {
        'total' :  total,
        'quantity' : quantity,
        'cart_items' : cart_items,
        'tax' : tax,
        'grand_total' : grand_total
    }

    return render(request, 'store/cart.html', context)

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    
    return cart

def add_cart(request, product_id):
    product = Product.objects.get(id = product_id)
    product_variations = []
    current_user = request.user

    #If user is authenticated
    if current_user.is_authenticated:
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]
                try:
                    variation = Variation.objects.get(variation_category__iexact = key, variation_value__iexact = value)
                    product_variations.append(variation)
                except:
                    pass


        is_cart_item_exsists = CartItem.objects.filter(product = product, user = current_user).exists
        if is_cart_item_exsists:
            cart_item = CartItem.objects.filter(product = product, user = current_user)

            exsisting_var_list = []
            id= []
            for item in cart_item:
                existing_variation = item.variations.all()
                exsisting_var_list.append(list(existing_variation))
                id.append(item.id)

            #print(exsisting_var_list)
            if product_variations in exsisting_var_list:
                index = exsisting_var_list.index(product_variations)
                print('index....' ,index)
                item_id = id[index]
                cart_item = CartItem.objects.get(product = product, user = current_user, id = item_id)
                cart_item.qunatity += 1
                cart_item.save()
            else:
                cart_item = CartItem.objects.create(product = product, user = current_user, qunatity = 1)
                if len(product_variations) > 0:
                    cart_item.variations.clear()
                    cart_item.variations.add(*product_variations)
                cart_item.save()
                
        else:
            cart_item = CartItem.objects.create(
                product = product,
                user = current_user,
                qunatity = 1
            )
            if len(product_variations) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variations)
            cart_item.save()
        return redirect('cart')

    #If user is not authenticated
    else:
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]
                try:
                    variation = Variation.objects.get(variation_category__iexact = key, variation_value__iexact = value)
                    product_variations.append(variation)
                except:
                    pass

        try:
            cart = Cart.objects.get(cart_id = _cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(
                cart_id = _cart_id(request)
            )
        cart.save()

        is_cart_item_exsists = CartItem.objects.filter(product = product, cart = cart).exists
        if is_cart_item_exsists:
            cart_item = CartItem.objects.filter(product = product, cart = cart)

            exsisting_var_list = []
            id= []
            for item in cart_item:
                existing_variation = item.variations.all()
                exsisting_var_list.append(list(existing_variation))
                id.append(item.id)

            #print(exsisting_var_list)
            if product_variations in exsisting_var_list:
                index = exsisting_var_list.index(product_variations)
                print('index....' ,index)
                item_id = id[index]
                cart_item = CartItem.objects.get(product = product, cart = cart, id = item_id)
                cart_item.qunatity += 1
                cart_item.save()
            else:
                cart_item = CartItem.objects.create(product = product, cart = cart, qunatity = 1)
                if len(product_variations) > 0:
                    cart_item.variations.clear()
                    cart_item.variations.add(*product_variations)
                cart_item.save()
                
        else:
            cart_item = CartItem.objects.create(
                product = product,
                cart = cart,
                qunatity = 1
            )
            if len(product_variations) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variations)
            cart_item.save()
        return redirect('cart')

def remove_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id = product_id)

    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user = request.user, id = cart_item_id)
    else:
        cart = Cart.objects.get(cart_id = _cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart, id = cart_item_id)

    if cart_item.qunatity > 1:
        cart_item.qunatity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    
    return redirect('cart')

def remove_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id = product_id)

    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(user = request.user, product=product, id = cart_item_id)
    else:
        cart = Cart.objects.get(cart_id = _cart_id(request))
        cart_item = CartItem.objects.get(cart=cart, product=product, id = cart_item_id)

    cart_item.delete()

    return redirect('cart')


@login_required(login_url='login')
def checkout(request, total = 0, quantity = 0, cart_items = None):
    tax =0
    grand_total = 0
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user = request.user, is_active = True)
        else:
            cart = Cart.objects.get(cart_id = _cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active = True)


        for cart_item in cart_items:
            total += (cart_item.qunatity * cart_item.product.price)
            quantity += cart_item.qunatity
        tax = (2 * total)/100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass

    context = {
        'total' :  total,
        'quantity' : quantity,
        'cart_items' : cart_items,
        'tax' : tax,
        'grand_total' : grand_total
    }

    return render(request, 'store/checkout.html', context)
