from django.shortcuts import render,redirect,get_object_or_404
from .models import *
from seller.models import *
from customer.models import *
from django.db.models import Avg, Prefetch,Min
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .decorator import _dashboard_for_user,customer_required,admin_not_required
# Create your views here.

def login_view(request):
    if request.method=="POST":
        username_or_email=request.POST.get("username_or_email")
        password=request.POST.get("password")
        try:
            user_obj=User.objects.get(email=username_or_email)
            username=user_obj.username
        except User.DoesNotExist:
            username=username_or_email
        user = authenticate(request,username=username,password=password)
        if user is not None:
            login(request,user)
            return redirect(_dashboard_for_user(request.user))
        else:
            messages.error(request, "Invalid username or password")
    return render(request,"core/login.html")
def register_view(request):
    if request.method=="POST":
        username=request.POST.get("username")
        email = request.POST.get("email")
        phone_no = request.POST.get("full_phone")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return render(request, "core/register.html")
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
            return render(request, "core/register.html")
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return render(request, "core/register.html")
        if User.objects.filter( phone_number=phone_no).exists():
            messages.error(request, "phone number already registered")
            return render(request, "core/register.html")
        user=User.objects.create_user(
            username=username,
            email=email,
             phone_number=phone_no,
            password=password
        )
        user.is_active=True
        user.save()
        login(request, user)
        messages.success(request, "Registration successful! please login.")
        return redirect("login")
        
    return render(request,"core/register.html")
@admin_not_required
def home_view(request):
    show_all = request.GET.get('show_all', False)
    categories = Category.objects.filter(is_active=True).order_by('display_order', 'name')

    if not show_all:
        categories = categories[:8]

    return render(request,"core/home.html", {
        'categories': categories,
        'show_all': show_all,
        'total_categories': Category.objects.filter(is_active=True).count()
    })
@login_required
def logout_view(request):
    logout(request)
    return redirect("/")


@admin_not_required
def all_products(request):

    categories = Category.objects.filter(is_active=True).order_by("display_order")

    selected_ids = request.GET.getlist("categories")
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    sort_by = request.GET.get("sort", "newest")
    in_stock = request.GET.get("in_stock") == "1"

    products = Product.objects.filter(
        is_active=True,
        approval_status="APPROVED"
    )

  
    if selected_ids:
        products = products.filter(subcategory__category__id__in=selected_ids)

 
    products = products.annotate(
        min_selling_price=Min("variants__selling_price"),
        min_mrp=Min("variants__mrp")
    )

 
    if min_price:
        try:
            products = products.filter(min_selling_price__gte=float(min_price))
        except ValueError:
            pass

    if max_price:
        try:
            products = products.filter(min_selling_price__lte=float(max_price))
        except ValueError:
            pass

  
    if in_stock:
        products = products.filter(variants__stock_quantity__gt=0)

 
    if sort_by == "price_low_high":
        products = products.order_by("min_selling_price")

    elif sort_by == "price_high_low":
        products = products.order_by("-min_selling_price")

    else:
        products = products.order_by("-created_at")

    products = products.select_related(
        "seller",
        "subcategory"
    ).prefetch_related(
        "variants",
        "gallery"
    ).distinct()

 
    for product in products:

        img = product.gallery.filter(is_primary=True).first()
        product.primary_image = img.image if img else None

        variant = product.variants.first()
        product.stock_quantity = variant.stock_quantity if variant else 0

    context = {
        "products": products,
        "categories": categories,
        "selected_categories": selected_ids,
        "sort_by": sort_by,
        "min_price": min_price,
        "max_price": max_price,
        "in_stock": in_stock,
    }

    return render(request, "core/all_products.html", context)

@admin_not_required
def subcategory_view(request, category_slug):

    active_category = get_object_or_404(Category, slug=category_slug, is_active=True)

    all_categories = Category.objects.filter(
        is_active=True
    ).order_by("display_order", "name")

    subcategories_qs = active_category.subcategories.filter(
        is_active=True
    ).order_by("display_order", "name")

    total_subcategories = subcategories_qs.count()

    show_all_subcategories = request.GET.get("show_all") == "1"
    show_all_products = request.GET.get("products") == "1"


    if show_all_subcategories:
        subcategories = subcategories_qs
    else:
        subcategories = subcategories_qs[:6]


    selected_slug = request.GET.get("subcategory")
    selected_subcategory = None

    if selected_slug:
        selected_subcategory = subcategories_qs.filter(slug=selected_slug).first()

    products = Product.objects.filter(
        is_active=True,
        approval_status="APPROVED",
        subcategory__category=active_category
    ).prefetch_related("gallery", "variants", "subcategory")

    if selected_subcategory:
        products = products.filter(subcategory=selected_subcategory)

    products = products.annotate(
        price=Min("variants__selling_price")
    ).order_by("-created_at")

   
    if not show_all_products:
        products = products[:8]

  
    for product in products:
        img = product.gallery.filter(is_primary=True).first()
        product.primary_image = img.image if img else None

    context = {
        "all_categories": all_categories,
        "active_category": active_category,
        "subcategories": subcategories,
        "selected_subcategory": selected_subcategory,
        "products": products,
        "show_all": show_all_subcategories,
        "show_all_products": show_all_products,
        "total_subcategories": total_subcategories,
    }

    return render(request, "core/subcategory.html", context)
@admin_not_required
def product_detail(request, slug):

    product = get_object_or_404(
        Product.objects.select_related(
            "seller",
            "subcategory",
            "subcategory__category"
        ),
        slug=slug,
        is_active=True,
        approval_status="APPROVED"
    )

    variants = ProductVariant.objects.filter(
        product=product,
        is_active=True
    ).prefetch_related(
        Prefetch(
            "images",
            queryset=ProductImage.objects.order_by("-is_primary", "display_order")
        ),
        Prefetch(
            "variant_attributes",
            queryset=VariantAttributeBridge.objects.select_related("option__attribute")
        )
    )

    gallery_images = ProductGallery.objects.filter(product=product)

    default_variant = variants.filter(stock_quantity__gt=0).first()

    if not default_variant:
        default_variant = variants.first()

    reviews = Review.objects.filter(
        product=product
    ).select_related("user").order_by("-created_at")

    rating_data = reviews.aggregate(avg=Avg("rating"))

    average_rating = round(rating_data["avg"] or 0, 1)

    review_count = reviews.count()

    context = {
        "product": product,
        "variants": variants,
        "gallery_images": gallery_images,
        "default_variant": default_variant,
        "reviews": reviews,
        "average_rating": average_rating,
        "review_count": review_count,
    }

    return render(request, "core/product_detail.html", context)