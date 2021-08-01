from decimal import Context, Overflow
from django.contrib.auth.models import User
from django.db import models
from django.db.models import query
from carts.models import Cart, CartItem
from django.contrib import messages, auth
from django.http.response import HttpResponse
from account.models import Account, UserProfile
from django.shortcuts import redirect, render, get_object_or_404
from .forms import AccountRegistration, UserForm, UserProfileForm
from django.contrib.auth.decorators import login_required

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from carts.views import _cart_id
import requests
from orders.models import Order, OrderProduct

def register(request):
    if request.method == 'POST':
        form = AccountRegistration(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            phone_number = form.cleaned_data['phone_number']
            user_name = email.split('@')[0]
            user = Account.objects.create_user(first_name = first_name, last_name=last_name, email = email, password = password, username = user_name)
            user.phone_number = phone_number
            user.save()

            #Create User Profile
            profile = UserProfile()
            profile.user_id = user.id
            profile.profile_picture = 'default/default-user.jpg'
            profile.save()

            #User Activation
            current_site = get_current_site(request)
            mail_subject = 'Please activate you account'
            message = render_to_string('account/account_verification_email.html',{
                'user' : user,
                'domain' : current_site,
                'uid' : urlsafe_base64_encode(force_bytes(user.pk)),
                'token' : default_token_generator.make_token(user),

            })
            to_email = email
            send_mail = EmailMessage(mail_subject, message, to=[to_email])
            send_mail.send()

            #messages.success(request, 'Account Created Sucessfully')
            #return redirect('register')
            return redirect('/account/login/?command=verification&email=' + email)

    else:
        form = AccountRegistration()

    context = {
        'form' : form
    }
    return render(request, 'account/register.html', context)

def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        
        user = auth.authenticate(email = email, password = password)
        if user is not None:
            if Cart.objects.filter(cart_id = _cart_id(request)).exists():
                cart = Cart.objects.get(cart_id = _cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart = cart).exists()

                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart = cart)

                    #get the cart items when user was not logged in
                    product_variation = []
                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))

                    # get the cart items when user was logged in
                    cart_item = CartItem.objects.filter(user = user)
                    ex_var_list = []
                    id = []
                    for item in cart_item:
                        existing_variation = item.variations.all()
                        ex_var_list.append(list(existing_variation))
                        id.append(item.id)

                    for pr in product_variation:
                        if pr in ex_var_list:
                            index = ex_var_list.index(pr)
                            item_id = id[index]
                            item = CartItem.objects.get(id = item_id)
                            item.qunatity +=1
                            item.user = user
                            item.save()
                        else:
                            cart_item = CartItem.objects.filter(cart = cart)
                            for item in cart_item:
                                item.user = user
                                item.save()
                else:
                    pass
            else:
                pass
            auth.login(request, user)
            messages.success(request, 'You are now logged in')
            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
                params = dict(x.split('=') for x in query.split('&'))

                if 'next' in params:
                    next_page = params['next']
                    return redirect(next_page)
            
            except:
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid Credentials')
            return redirect('login')

    return render(request, 'account/login.html')

@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    messages.success(request, 'You are logged Out')
    return redirect('login')

def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, Overflow, Account.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Congratulations! Your Account is activated')
        return redirect('login')
    else:
        messages.error(request, 'Invalid activation link')
        return redirect('register')

@login_required(login_url= 'login')
def dashboard(request):
    orders = Order.objects.order_by('-created_at').filter(user__id = request.user.id, is_ordered = True)
    order_count = orders.count()

    print('1111111111111111' , request.user.id)
    userProfile = UserProfile.objects.get(user_id = request.user.id)

    context = {
        'order_count' : order_count,
        'userProfile' : userProfile,
    }
    return render(request, 'account/dashboard.html', context)

def forgotpassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email = email).exists():
            user = Account.objects.get(email__iexact = email)

            #Reset Password Email
            current_site = get_current_site(request)
            mail_subject = 'Please activate you account'
            message = render_to_string('account/reset_password_email.html',{
                'user' : user,
                'domain' : current_site,
                'uid' : urlsafe_base64_encode(force_bytes(user.pk)),
                'token' : default_token_generator.make_token(user),

            })
            to_email = email
            send_mail = EmailMessage(mail_subject, message, to=[to_email])
            send_mail.send()

            messages.success(request, 'Reset Password link has been sent to your email address.')
            return redirect('login')
        
        else:
            messages.error(request, 'Account does not exist.')
            return render('forgotpassword')
    return render(request, 'account/forgotpassword.html')

def resetpassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, Overflow, Account.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, '')
        return redirect('resetpassword')
    else:
        messages.error(request, 'Reset Password Link has been expired.')
        return redirect('login')
    
def resetpassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:   
            uid = request.session.get('uid')
            user = Account.objects.get(pk = uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password reset successfully')
            return redirect('login')
        else:
            messages.error(request, 'password do not match')
            return redirect('resetpassword')
    else:
        return render(request, 'account/resetpassword.html')

def my_orders(request):
    orders = Order.objects.filter(user = request.user, is_ordered = True)
    context = {
        'orders' : orders
    }
    return render(request, 'account/my_orders.html', context)

def edit_profile(request):
    userProfile = get_object_or_404(UserProfile, user = request.user)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance = userProfile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your Profile has been updated')
            return redirect('edit_profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userProfile)
    
    context = {
        'user_form' : user_form ,
        'profile_form' : profile_form,
        'userProfile' : userProfile
    }
    return render(request, 'account/edit_profile.html', context)

@login_required(login_url='login')
def edit_password(request):
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        user = Account.objects.get(username__exact = request.user.username)

        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password Updated Successfully')
                return redirect('edit_password')
            else:
                messages.error(request, 'Please enter valid password')
                return redirect('edit_password')

        else:
            messages.error(request, 'Password does not match!')
            return redirect('edit_password')
    return render(request, 'account/edit_password.html')

def order_detail(request, order_id):
    order_detail = OrderProduct.objects.filter(order__order_number = order_id)
    order = Order.objects.get(order_number = order_id)
    sub_total = 0
    
    for i in order_detail:
        sub_total += sub_total + (i.product_price )
    context = {
        'order_detail' : order_detail,
        'order' : order,
        'sub_total' : sub_total,
    }
    return render(request, 'account/order_detail.html', context)
