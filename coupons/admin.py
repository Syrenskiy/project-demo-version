from django.contrib import admin

from coupons.models import Coupon


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'display_discount', 'remaining_uses', 'valid_to', 'active')
    list_filter = ('active', 'valid_from', 'valid_to')
    search_fields = ['code']

    @admin.display(description='Discount')
    def display_discount(self, coupon: Coupon) -> str:
        return f'{coupon.discount}%'

