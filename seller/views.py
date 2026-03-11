from django.shortcuts import render,redirect,get_object_or_404
from core.models import *
from .models import *
from bnadmin.models import *
from django.contrib import messages
from django.contrib.auth import login
from django.db.models import  Q
from core.decorator import seller_profile_required,verified_seller_required

# Create your views here.
def user_seller_bridge(request):
    return render(request,"seller/user_seller_bridge.html")
def seller_registration(request):
    if request.method == "POST":
         store_name=request.POST.get("store_name")
         gst_number=request.POST.get("gst_number")
         description=request.POST.get("description")
         logo=request.FILES.get("logo")
         if SellerProfile.objects.filter(store_name=store_name).exists():
               messages.error(request, "This store name is already registered. Please choose a unique brand name.")
               return render(request,"seller/seller_registration.html",{"data":request.POST})
         if SellerProfile.objects.filter(gst_number=gst_number).exists():
               messages.error(request, "This GSTIN is already linked to an existing seller account. Please log in to your original account.")
               return render(request,"seller/seller_registration.html",{"data":request.POST})    
         if not  request.user.is_authenticated:
              first_name=request.POST.get("first_name")
              last_name=request.POST.get("last_name")
              username=request.POST.get("username")
              email = request.POST.get("email")
              phone_no = request.POST.get("phone_display")
              password = request.POST.get("password")
              confirm_password = request.POST.get("confirm_password")
              if username:
                   final_username=username
              elif first_name or last_name:
                   final_username =(first_name+last_name).lower()
              elif email:
                   final_username = email.split("@")[0].lower()

              else:
                   final_username = "user"
                 
              if password != confirm_password:
                    messages.error(request, "Passwords do not match")
                    return render(request,"seller/seller_registration.html",{"data":request.POST})
              if User.objects.filter(username=final_username).exists():
                    messages.error(request, "Username already taken")
                    return render(request,"seller/seller_registration.html",{"data":request.POST})
              if User.objects.filter(email=email).exists():
                    messages.error(request, "Email already registered")
                    return render(request,"seller/seller_registration.html",{"data":request.POST})
              if User.objects.filter( phone_number=phone_no).exists():
                    messages.error(request, "phone number already registered")
                    return render(request,"seller/seller_registration.html",{"data":request.POST})
              user=User.objects.create_user(
                    username=final_username,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone_number=phone_no,
                    password=password
                )
              user.is_active=True
              user.save()
              login(request, user)
         else:
              user=request.user
                
         seller_profile = SellerProfile.objects.create(
                user=user,
                store_name=store_name,
                gst_number = gst_number,
                description=description,
                logo=logo,
            )
         seller_profile.save()
         return redirect('seller_profile')
    return render(request,"seller/seller_registration.html",{"data":request.POST})
@verified_seller_required
def seller_dashboard(request):
     return render(request,"seller/dashboard.html")
@verified_seller_required
def seller_products(request):
     seller=request.user.seller_profile
     products = (
    Product.objects.filter(seller=seller).select_related("subcategory").prefetch_related("gallery","variants","variants__images","variants__variant_attributes__option__attribute").order_by("-created_at")
)
     query=request.GET.get("q")
     if query:
          products = products.filter( Q(name__icontains=query) | Q(brand__icontains=query) | Q(variants__sku_code__icontains=query)).distinct()
     status = request.GET.get("status")

     if status == "active":
        products = products.filter(is_active=True)

     elif status == "inactive":
        products = products.filter(is_active=False)
     products_pending_count = products.filter(approval_status="PENDING").count()
     products_approved_count = products.filter(approval_status="APPROVED").count()
     products_rejected_count = products.filter(approval_status="REJECTED").count()
     for product in products:

        variants = product.variants.all()
        product.variant_count = variants.count()
        product.total_stock = sum(v.stock_quantity for v in variants)
        product.stock_percentage = min((product.total_stock / 100) * 100 if product.total_stock else 0,100)
          
     return render(request,"seller/product.html",{"products": products,"products_pending_count": products_pending_count,
        "products_approved_count": products_approved_count,
        "products_rejected_count": products_rejected_count,})
@verified_seller_required
def deactivate_product(request, id):
    product = Product.objects.get(id=id, seller=request.user.seller_profile)
    product.is_active = False
    product.save()
    return redirect("seller_product")
@verified_seller_required
def activate_product(request, id):
    product = Product.objects.get(id=id, seller=request.user.seller_profile)
    product.is_active = True
    product.save()
    return redirect("seller_product")
@verified_seller_required
def deactivate_variant(request, id):
    variant = ProductVariant.objects.get(id=id)
    variant.is_active = False
    variant.save()
    return redirect("seller_product")
@verified_seller_required
def activate_variant(request, id):
    variant = ProductVariant.objects.get(id=id)
    variant.is_active = True
    variant.save()
    return redirect("seller_product")



@verified_seller_required
def add_products(request):
     subcategory =SubCategory.objects.all
     if request.method == "POST":
        name = request.POST.get("name")
        brand = request.POST.get("brand")
        description = request.POST.get("description")
        model_number = request.POST.get("model_number")
        subcategory_id = request.POST.get("subcategory")
        is_cancellable = request.POST.get("is_cancellable") == "on"
        is_returnable = request.POST.get("is_returnable") == "on"
        return_days = request.POST.get("return_days") or 0
        status = request.POST.get("status")
        if status == "draft":
            approval_status = "DRAFT"
        else:
            approval_status = "PENDING"

        product = Product.objects.create(
            seller=request.user.seller_profile,
            name=name,
            brand=brand,
            description=description,
            model_number=model_number,
            subcategory_id=subcategory_id,
            is_cancellable=is_cancellable,
            is_returnable=is_returnable,
            return_days=return_days,
            approval_status=approval_status
        )
        images = request.FILES.getlist("product_images[]")

        primary_index = int(request.POST.get("primary_image_index", 0))

        for index, image in enumerate(images):

         ProductGallery.objects.create(
        product=product,
        image=image,
        is_primary=(index == primary_index),
        display_order=index
    )
         return redirect("product_status")
     return render(request,"seller/addproduct.html",{"subcategories":subcategory})
@verified_seller_required
def edit_product(request, product_id):

    product = Product.objects.get(
        id=product_id,
        seller=request.user.seller_profile
    )

    subcategories = SubCategory.objects.all()

    if request.method == "POST":

        product.name = request.POST.get("name")
        product.brand = request.POST.get("brand")
        product.description = request.POST.get("description")
        product.model_number = request.POST.get("model_number")
        product.subcategory_id = request.POST.get("subcategory")

        product.is_cancellable = request.POST.get("is_cancellable") == "on"
        product.is_returnable = request.POST.get("is_returnable") == "on"
        product.return_days = request.POST.get("return_days") or 0
        status = request.POST.get("status")
        if status == "draft":
            approval_status = "DRAFT"
        else:
            approval_status = "PENDING"


        product.approval_status = approval_status

        product.save()


        images = request.FILES.getlist("product_images[]")

        if images:


            ProductGallery.objects.filter(product=product).delete()

            primary_index = int(request.POST.get("primary_image_index", 0))

            for index, image in enumerate(images):

                ProductGallery.objects.create(
                    product=product,
                    image=image,
                    is_primary=(index == primary_index),
                    display_order=index
                )

        return redirect("product_status")

    return render(request, "seller/addproduct.html", {
        "product": product,
        "subcategories": subcategories
    })
@verified_seller_required
def add_variant(request,product_id):
     product =get_object_or_404(Product,id=product_id,seller=request.user.seller_profile)
     attributes=Attribute.objects.filter(subcategories=product.subcategory).prefetch_related("options").order_by("display_order")

     if request.method == "POST":
        mrp = request.POST.get("MRP") or 0
        selling_price = request.POST.get("selling_price")
        cost_price = request.POST.get("cost_price") or 0
        stock = request.POST.get("stock") or 0
        low_stock_threshold = request.POST.get("low_stock_threshold") or 5
        if not selling_price:
            messages.error(request, "Selling price is required.")
            return redirect("add_variant", product_id=product.id)

        variant=ProductVariant.objects.create(
            product=product,
            selling_price=selling_price,
            mrp=mrp,  
            cost_price=cost_price,
            stock_quantity=stock,
            low_stock_threshold=low_stock_threshold

        )
        for attribute in attributes:
             option_id=request.POST.get(f"attribute_{attribute.id}")
             if option_id:
                  option=AttributeOption.objects.get(id=option_id)
                  VariantAttributeBridge.objects.create(
                       variant=variant,
                       option=option
                  )
        images = request.FILES.getlist("variant_images")
        for index,img in enumerate(images):
              ProductImage.objects.create(
                variant=variant,
                image=img,
                is_primary=(index == 0),
                display_order=index
            )
        messages.success(request, "Variant created successfully.")
        if request.POST.get("_add_another") == "true":
            return redirect("add_variant", product_id=product.id)
        return redirect("seller_product")
          
     return render(request,"seller/addvariant.html",{"product":product,"attributes":attributes})
@verified_seller_required
def product_status(request):
     products = Product.objects.filter(seller=request.user.seller_profile)
     return render(request,"seller/product_status.html",{"products":products})
@verified_seller_required
def seller_inventory(request):
     return render(request,"seller/inventory.html")
@verified_seller_required
def seller_order(request):
     return render(request,"seller/seller_order.html")
@verified_seller_required
def seller_earnings(request):
     return render(request,"seller/earnings.html")
@verified_seller_required
def offer_discount(request):
     return render(request,"seller/offeranddiscount.html")
@verified_seller_required
def seller_reviews(request):
     return render(request,"seller/sellerreviews.html")
@seller_profile_required
def seller_profile(request):
    profile = request.user.seller_profile

    if request.method == "POST":
        profile.store_name = request.POST.get("store_name")
        profile.description = request.POST.get("description")

        if request.FILES.get("logo"):
            if profile.logo:
                   profile.logo.delete(save=False)
            profile.logo = request.FILES.get("logo")

        if request.FILES.get("banner"):
            if profile.banner:
                  profile.banner.delete(save=False)
            profile.banner = request.FILES.get("banner")

        profile.save()

    return render(request, "seller/sellerprofile.html", {
        "profile": profile
    })
@verified_seller_required
def seller_settings(request):
     return render(request,"seller/seller_settings.html")
