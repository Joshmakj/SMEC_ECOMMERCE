from django.shortcuts import render
from core.models import User
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def user_profile_view(request):
    user_obj =request.user
    if request.method=="POST":
        user_obj.first_name=request.POST.get("firstname")
        user_obj.last_name=request.POST.get("lastname")
        pro_image=request.FILES.get("profile_image")

        if pro_image:
            if user_obj.profile_image:
                user_obj.profile_image.delete(save=False)
            user_obj.profile_image=pro_image
        user_obj.save()
    return render(request,"customer/profile.html",{"user":user_obj})




