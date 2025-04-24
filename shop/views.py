from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from .models import Product, Category, Cart, Order, OrderItem
import random

def home(request):
    categories = Category.objects.all()
    products = Product.objects.all()[:8]
    return render(request, 'shop/home.html', {
        'products': products,
        'categories': categories
    })

def product_list(request, category_id=None):
    if category_id:
        category = get_object_or_404(Category, id=category_id)
        products = Product.objects.filter(category=category)
    else:
        products = Product.objects.all()
        category = None
    return render(request, 'shop/product_list.html', {
        'products': products,
        'category': category
    })

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    action = request.GET.get('action')
    next_url = request.GET.get('next', request.META.get('HTTP_REFERER', reverse('home')))

    if action == 'remove':
        Cart.objects.filter(user=request.user, product=product).delete()
        messages.success(request, f'"{product.name}" removed from cart!')
    else:
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': 1}
        )
        
        if not created:
            if action == 'increase':
                cart_item.quantity += 1
                messages.success(request, f'Increased quantity of "{product.name}"!')
            elif action == 'decrease':
                if cart_item.quantity > 1:
                    cart_item.quantity -= 1
                    messages.success(request, f'Decreased quantity of "{product.name}"!')
                else:
                    cart_item.delete()
                    messages.success(request, f'"{product.name}" removed from cart!')
                cart_item.save()
            else:
                cart_item.quantity += 1
                messages.success(request, f'"{product.name}" added to cart!')
            cart_item.save()
        else:
            messages.success(request, f'"{product.name}" added to cart!')

    return redirect(next_url)

@login_required
def cart(request):
    cart_items = Cart.objects.filter(user=request.user)
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'shop/cart.html', {
        'cart_items': cart_items,
        'total': total
    })




@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    if request.method == 'POST':
        delivery_address = request.POST.get('delivery_address', '').strip()
        
        if not delivery_address:
            messages.error(request, "Please enter a delivery address")
            return redirect('checkout')
        
        if not cart_items.exists():
            messages.warning(request, "Your cart is empty")
            return redirect('cart')
        
        # Create the order
        order = Order.objects.create(
            user=request.user,
            delivery_address=delivery_address,
            delivery_time=f"{random.randint(10, 30)} minutes",
            total_amount=total  # Add this line to store the total
        )
        
        # Add all cart items to order
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
        
        # Clear the cart
        cart_items.delete()
        return redirect('order_confirmation', order_id=order.id)
    
    return render(request, 'shop/checkout.html', {
        'cart_items': cart_items,
        'total': total  # Pass the total to template
    })

@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'shop/order_confirmation.html', {'order': order})

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-ordered_date')
    return render(request, 'shop/orders.html', {'orders': orders})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'shop/register.html', {'form': form})
def categories_view(request):
    categories = Category.objects.all()
    default_category = Category.objects.first()  # or get a 'Trending' category
    default_products = Product.objects.filter(category=default_category)[:8]  # show top 8
    return render(request, 'shop/categories.html', {
        'categories': categories,
        'default_products': default_products,
        'default_category': default_category,
    })


def products_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)
    categories = Category.objects.all()  # for the second navbar
    return render(request, 'shop/category_products.html', {
        'selected_category': category,
        'products': products,
        'categories': categories
    })
def about(request):
    return render(request, 'shop/about.html')

def contact(request):
    return render(request, 'shop/contact.html')
