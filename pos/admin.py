from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, Customer,Invoice, InvoiceItem

# Register your models here.
#تسحيل نموذج الفئة في لوحة الإدارة
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """ إعدادات عرض نموذج الفئة في لوحة الإدارة """
    list_display = ['id', 'name', 'description', 'createsd_at']
    list_display_links = ['id', 'name']
    search_fields = ['name', 'description']
    ordering = ['name']

    def product_count(self, obj):
        """ حساب عدد المنتجات في كل فئة """
        return obj.products.count()
    product_count.short_description = 'عدد المنتجات'

#تسحيل نموذج المنتج في لوحة الإدارة
@admin.register(Product) 
class ProductAdmin(admin.ModelAdmin):
    """ إعدادات عرض نموذج المنتج في لوحة الإدارة """
    list_display = [
        'id', 
        'name',
        'category',
        'price',
        'cost',
        'stock',
        'profit_per_item',
        'total_stock_value',
        'is_low_stock_display',
        'barcode',
        'image_preview',
    ]
    list_display_links = ['id', 'name']
    list_filter = ['category', 'created_at', 'updated_at']
    search_fields = ['name', 'barcode', 'description']
    readonly_fields = ['barcode', 'created_at', 'updated_at',
                       'profit_display','stock_status','image_preview']
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('name', 'category', 'description', 'barcode')
            }),
        ('الأسعار والمخزون', {
            'fields': ('price', 'cost', 'stock', 'profit_display')
            }),
        ('الصور', {
            'fields': ('image','image_preview'),
            'classes': ('collapse',)
            }),

        ('المعلومات اضافية', {
            'fields': ('stock_status','created_at', 'updated_at'),
            'classes': ('collapse',)
            })
    )
    def image_preview(self, obj):
        """ عرض معاينة صورة المنتج في لوحة الإدارة """
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%;" />',
                                obj.image.url)
        return "لا توجد صورة"
    image_preview.short_description = 'صورة مصغرة'

    #دالة حشاب الربح لكل منتج
    def profit_per_item(self, obj):
        """ حساب هامش الربح من المنتج """
        profit = obj.get_profit()
        color = 'green' if profit > 0 else 'red'
        return format_html('<span style="color: {};">{}</span>', color, profit)
    profit_per_item.short_description = 'هامش الربح'
    
    #دالة حشاب القيمة الإجمالية للمخزون
    def total_stock_value(self, obj):
        value= obj.price * obj.stock
        return f"{value:.2f} جنية"
    total_stock_value.short_description = 'قيمة المخزون'
    
    #عرض حالة المخزون
    def is_low_stock_display(self, obj):
        """ عرض حالة المخزون """
        if obj.is_low_stock():
            return format_html('<span style="color: red; font-weight: bold;">منخفض *</span>')
        return format_html('<span style="color: green; font-weight: bold;">جيد *</span>')
    is_low_stock_display.short_description = 'حالة المخزون'

    #حقول للعرض فى اللفحة التفصيلية
    def profit_display(self, obj):
       from decimal import Decimal
       profit = obj.get_profit()
       cost = obj.cost if obj.cost is not None else Decimal('0.00')
       margin = (profit / cost * Decimal('100')) if cost > Decimal('0.00') else Decimal('0.00')
       return format_html('''
        <div style="background: #f5f5f5; padding: 10px; border-radius: 5px;">
            <strong>الربح:</strong> {:.2f} جنية<br>
            <strong>هامش الربح:</strong> {:.1f}%
        </div>
        ''', profit, margin)
                           
    profit_display.short_description = 'تفاصيل الربح'
    
    def stock_status(self, obj):
        """ عرض حالة المخزون بالتفصيل """
        if obj.stock <=0:
            status ='<span style="color: white; background: red; padding: 3px 8px; border-radius: 3px;">نفذ من المخزون</span>'
        elif obj.stock<10:
            status = '<span style="color: white; background: orange; padding: 3px 8px; border-radius: 3px;">منخفض</span>'
        else:
            status = '<span style="color: white; background: green; padding: 3px 8px; border-radius: 3px;">جيد</span>'
        return format_html('''
            <div style="margin-top: 10px;">
                <strong>الحالة:</strong> {}<br>
                <strong>الكمية:</strong> {} وحدة
            </div>
        ''', status, obj.stock)
    stock_status.short_description = 'حالة المخزون'

    #احراءات اضافية
    actions = ['increase_stock', 'decrease_stock']
    def increase_stock(self, request, queryset):
        for product in queryset:
            product.stock += 10
            product.save()
        self.message_user(request, f"تم زيادة المخزون لـ {queryset.count()} منتج بمقدار 10 وحدات لكل منتج")
    increase_stock.short_description = "زيادة المخزون 10 وحدات"

    def decrease_stock(self, request, queryset):
        for product in queryset:
            if product.stock >= 10:
                product.stock -= 10
                product.save()
        self.message_user(request, f"تم تخفيض المخزون لـ {queryset.count()} منتج بمقدار 10 وحدات لكل منتج")
    decrease_stock.short_description = "تخفيض المخزون 10 وحدات"
