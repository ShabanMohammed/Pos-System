from django.contrib import admin
from django.utils.html import format_html
from django.contrib.admin import DateFieldListFilter
from .models import Category, Product, Customer, Invoice, InvoiceItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'product_count']
    list_display_links = ['id', 'name']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    def product_count(self, obj):
        count = obj.products.count()
        return str(count) if count else "0"
    product_count.short_description = 'عدد المنتجات'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'category', 'price_display', 'cost_display', 'stock',
        'profit_per_item', 'image_preview'
    ]
    list_display_links = ['id', 'name']
    list_filter = ['category']
    search_fields = ['name', 'barcode', 'description']
    readonly_fields = [
        'barcode', 'created_at', 'updated_at',
        'profit_display', 'stock_status', 'get_image_preview'
    ]
    
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('name', 'category', 'description', 'barcode')
        }),
        ('الأسعار والمخزون', {
            'fields': ('price', 'cost', 'stock', 'profit_display')
        }),
        ('الصورة', {
            'fields': ('image', 'get_image_preview'),
            'classes': ('collapse',)
        }),
        ('معلومات إضافية', {
            'fields': ('stock_status', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def price_display(self, obj):
        if obj.price:
            return f'{float(obj.price):.2f} ريال'
        return "0.00 ريال"
    price_display.short_description = 'سعر البيع'
    
    def cost_display(self, obj):
        if obj.cost:
            return f'{float(obj.cost):.2f} ريال'
        return "0.00 ريال"
    cost_display.short_description = 'سعر التكلفة'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 5px;" />',
                obj.image.url
            )
        return "لا توجد صورة"
    image_preview.short_description = 'صورة'
    
    def get_image_preview(self, obj):
        if obj.image:
            return format_html(
                '<div style="margin-top: 10px;">'
                '<strong>الصورة الحالية:</strong><br>'
                '<img src="{}" width="200" style="margin-top: 5px;" />'
                '</div>',
                obj.image.url
            )
        return "لا توجد صورة حالياً"
    get_image_preview.short_description = 'معاينة الصورة'
    
    def profit_per_item(self, obj):
        try:
            if obj.price and obj.cost:
                profit = float(obj.price) - float(obj.cost)
                color = 'green' if profit > 0 else 'red'
                return format_html(
                    '<span style="color: {};">{:.2f} ريال</span>',
                    color,
                    profit
                )
        except (ValueError, TypeError):
            pass
        return "0.00 ريال"
    profit_per_item.short_description = 'الربح'
    
    def profit_display(self, obj):
        try:
            if obj.price and obj.cost:
                profit = float(obj.price) - float(obj.cost)
                margin = (profit / float(obj.cost) * 100) if float(obj.cost) > 0 else 0
                return format_html(
                    '<div style="background: #f5f5f5; padding: 10px; border-radius: 5px;">'
                    '<strong>الربح:</strong> {:.2f} ريال<br>'
                    '<strong>هامش الربح:</strong> {:.1f}%'
                    '</div>',
                    profit,
                    margin
                )
        except (ValueError, TypeError):
            pass
        return "غير محسوب"
    profit_display.short_description = 'معلومات الربحية'
    
    def stock_status(self, obj):
        if not obj.stock:
            return 'لا يوجد مخزون'
        elif obj.stock <= 0:
            status = 'نفذ'
        elif obj.stock < 10:
            status = 'منخفض'
        else:
            status = 'جيد'
        return f'الحالة: {status} ({obj.stock} وحدة)'
    stock_status.short_description = 'حالة المخزون'
    
    actions = ['increase_stock', 'decrease_stock']
    
    def increase_stock(self, request, queryset):
        for product in queryset:
            product.stock = (product.stock or 0) + 10
            product.save()
        self.message_user(request, f"تم زيادة المخزون لـ {queryset.count()} منتج")
    
    def decrease_stock(self, request, queryset):
        for product in queryset:
            current_stock = product.stock or 0
            if current_stock >= 10:
                product.stock = current_stock - 10
                product.save()
        self.message_user(request, f"تم تخفيض المخزون لـ {queryset.count()} منتج")


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'phone', 'email', 'invoice_count']
    list_display_links = ['id', 'name']
    search_fields = ['name', 'phone', 'email', 'address']
    readonly_fields = ['created_at', 'customer_summary']
    
    def invoice_count(self, obj):
        count = obj.invoices.count()
        return str(count) if count else "0"
    invoice_count.short_description = 'عدد الفواتير'
    
    def customer_summary(self, obj):
        count = obj.invoices.count()
        return format_html(
            '<div style="background: #e8f4fc; padding: 15px; border-radius: 8px;">'
            '<h4>ملخص العميل</h4>'
            '<p>عدد الفواتير: {}</p>'
            '</div>',
            count
        )
    customer_summary.short_description = 'الملخص'


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    readonly_fields = ['total']
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "product":
            kwargs["queryset"] = Product.objects.all().order_by('name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        'invoice_number', 'customer_display', 'date',
        'grand_total_display', 'status_display'
    ]
    list_display_links = ['invoice_number']
    search_fields = ['invoice_number', 'customer__name']
    readonly_fields = ['invoice_number', 'created_at', 'get_invoice_summary']
    inlines = [InvoiceItemInline]
    
    fieldsets = (
        ('معلومات الفاتورة', {
            'fields': ('invoice_number', 'customer', 'date', 'notes')
        }),
        ('المبالغ', {
            'fields': ('subtotal', 'discount', 'tax', 'grand_total')
        }),
        ('حالة الفاتورة', {
            'fields': ('payment_method', 'status')
        }),
        ('ملخص الفاتورة', {
            'fields': ('get_invoice_summary',),
            'classes': ('wide',)
        }),
    )
    
    def customer_display(self, obj):
        if obj.customer:
            return obj.customer.name
        return "زائر"
    customer_display.short_description = 'العميل'
    
    def grand_total_display(self, obj):
        try:
            if obj.grand_total:
                return f'{float(obj.grand_total):.2f} ريال'
        except (ValueError, TypeError):
            pass
        return "0.00 ريال"
    grand_total_display.short_description = 'الإجمالي'
    
    def status_display(self, obj):
        statuses = {
            'draft': 'مسودة',
            'pending': 'قيد الانتظار',
            'paid': 'مدفوع',
            'cancelled': 'ملغى',
            'refunded': 'مرتجع'
        }
        status_text = statuses.get(obj.status, obj.status)
        
        colors = {
            'draft': '#9E9E9E',
            'pending': '#FFC107',
            'paid': '#4CAF50',
            'cancelled': '#F44336',
            'refunded': '#9C27B0'
        }
        color = colors.get(obj.status, '#000')
        
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            color,
            status_text
        )
    status_display.short_description = 'الحالة'
    
    def get_invoice_summary(self, obj):
        items = obj.items.all()
        if not items:
            return "لا توجد أصناف"
            
        items_html = ""
        for item in items:
            items_html += f'''
            <tr>
                <td>{item.product.name if item.product else 'غير معروف'}</td>
                <td>{item.quantity}</td>
                <td>{float(item.price):.2f} ريال</td>
                <td>{float(item.total):.2f} ريال</td>
            </tr>
            '''
        
        return format_html(
            '<div style="background: #f9f9f9; padding: 15px; border-radius: 8px; margin: 10px 0;">'
            '<h4 style="margin-top: 0;">تفاصيل الفاتورة</h4>'
            '<table style="width: 100%; border-collapse: collapse;">'
            '<thead>'
            '<tr style="background: #e0e0e0;">'
            '<th style="padding: 8px;">المنتج</th>'
            '<th style="padding: 8px;">الكمية</th>'
            '<th style="padding: 8px;">السعر</th>'
            '<th style="padding: 8px;">المجموع</th>'
            '</tr>'
            '</thead>'
            '<tbody>'
            '{}'
            '</tbody>'
            '</table>'
            '</div>',
            items_html
        )
    get_invoice_summary.short_description = 'ملخص الفاتورة'


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'invoice', 'product', 'quantity', 'price_display', 'total_display']
    search_fields = ['product__name', 'invoice__invoice_number']
    
    def price_display(self, obj):
        if obj.price:
            return f'{float(obj.price):.2f} ريال'
        return "0.00 ريال"
    price_display.short_description = 'السعر'
    
    def total_display(self, obj):
        if obj.total:
            return f'{float(obj.total):.2f} ريال'
        return "0.00 ريال"
    total_display.short_description = 'المجموع'