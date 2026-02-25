from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.urls import reverse_lazy


# ==============================================================================
# SELLER DECORATOR
# ==============================================================================

def seller_required(view_func=None, skip_verification=False, login_url=None):
    """
    Allows only users who have a SellerProfile.

    Checks in order:
    1. user.is_authenticated
    2. user.is_active
    3. user.is_seller
    4. user.is_verified_seller (unless skip_verification=True)

    Usage:
        @seller_required
        def seller_dashboard(request): ...

        @seller_required(skip_verification=True)
        def seller_pending(request): ...
    """

    login_url = login_url or reverse_lazy("login")
    apply_url = reverse_lazy("seller_apply")
    pending_url = reverse_lazy("seller_pending")

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.user

            # 1️⃣ Not logged in
            if not user.is_authenticated:
                return redirect(
                    f"{login_url}?{REDIRECT_FIELD_NAME}={request.get_full_path()}"
                )

            # 2️⃣ Account deactivated
            if not user.is_active:
                messages.error(request, "Your account has been deactivated.")
                return redirect(login_url)

            # 3️⃣ Not a seller
            if not user.is_seller:
                messages.info(request, "You need a seller account to access this page.")
                return redirect(apply_url)

            # 4️⃣ Seller exists but not verified
            if not skip_verification and not user.is_verified_seller:
                messages.warning(
                    request,
                    "Your seller account is pending admin verification."
                )
                return redirect(pending_url)

            return view_func(request, *args, **kwargs)

        return wrapper

    if view_func:
        return decorator(view_func)
    return decorator


# ==============================================================================
# ADMIN DECORATOR
# ==============================================================================

def admin_required(view_func=None, login_url=None):
    """
    Allows only staff/superuser accounts (is_staff=True).

    Checks:
    1. user.is_authenticated
    2. user.is_active
    3. user.is_staff

    Usage:
        @admin_required
        def admin_dashboard(request): ...
    """

    login_url = login_url or reverse_lazy("login")

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.user

            # 1️⃣ Not logged in
            if not user.is_authenticated:
                return redirect(
                    f"{login_url}?{REDIRECT_FIELD_NAME}={request.get_full_path()}"
                )

            # 2️⃣ Account deactivated
            if not user.is_active:
                messages.error(request, "Your account has been deactivated.")
                return redirect(login_url)

            # 3️⃣ Not admin
            if not user.is_staff:
                messages.error(request, "You do not have permission to access this page.")
                return redirect(_dashboard_for_user(user))

            return view_func(request, *args, **kwargs)

        return wrapper

    if view_func:
        return decorator(view_func)
    return decorator


# ==============================================================================
# INTERNAL HELPER
# ==============================================================================

def _dashboard_for_user(user):
    """
    Returns the correct dashboard based on role.

    Priority:
    admin > verified seller > pending seller > customer
    """

    if user.is_staff:
        return reverse_lazy("admin_dashboard")

    if user.is_verified_seller:
        return reverse_lazy("seller_dashboard")

    if user.is_seller:
        return reverse_lazy("seller_pending")

    return reverse_lazy("customer_dashboard")