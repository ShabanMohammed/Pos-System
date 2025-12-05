from decimal import Decimal
import random
import string
from django.utils import timezone
from django.db import models
from django.core.validators import MinValueValidator
# Create your models here.
class Category(models.Model):
    """ نموذج فئة المنتج في نظام نقاط البيع """
    name = models.CharField(max_length=100,verbose_name="اسم الفئة")
    description = models.TextField(blank=True, null=True,verbose_name="الوصف")
    created_at = models.DateTimeField(auto_now_add=True,verbose_name="تاريخ الإنشاء")
    class Meta:
        verbose_name = "فئة"
        verbose_name_plural = "الفئات"
        ordering = ['name']
    def __str__(self):
        return self.name

class Product(models.Model):
    """ نموذج المنتج في نظام نقاط البيع """
    name = models.CharField(max_length=100,verbose_name="اسم المنتج")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, 
                                 related_name='products',verbose_name="الفئة")
    price = models.DecimalField(max_digits=10, decimal_places=2,
                                verbose_name="سعر البيع")
    cost = models.DecimalField(max_digits=10, decimal_places=2,
                               verbose_name="سعر التكلفة")
    stock = models.IntegerField( default=0,verbose_name="المخزون")
    barcode = models.CharField(max_length=50, unique=True,blank=True,
                                verbose_name="الباركود")
    image= models.ImageField(upload_to='products/', blank=True, null=True,
                             verbose_name="صورة المنتج")
    description = models.TextField(blank=True, null=True,verbose_name="الوصف")
    created_at = models.DateTimeField(auto_now_add=True,verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True,verbose_name="اخر تحديث")
    class Meta:
        verbose_name = "منتج"
        verbose_name_plural = "المنتجات"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.price} جنية" 
    """ توليد باركود تلقائي اذا لم يكون موجود """
   
    def save(self, *args, **kwargs):
        if not self.barcode:
            self.barcode = ''.join(random.choices(string.digits, k=13))
        super().save(*args, **kwargs)

    def get_profit(self):
        """حماية من حالات None، إرجاع فرق السعر مع ضمان Decimal."""
        price = self.price if self.price is not None else Decimal('0.00')
        cost = self.cost if self.cost is not None else Decimal('0.00')
        return price - cost
    
    def is_low_stock(self):
        """ تحقق اذا كان كمية المنتج في المخزون منخفضة """
        LOW_STOCK_THRESHOLD = 10
        return self.stock < LOW_STOCK_THRESHOLD
    

class Customer(models.Model):
    """ نموذج العميل في نظام نقاط البيع """
    name = models.CharField(max_length=200,verbose_name="اسم العميل")
    phone = models.CharField(max_length=20,verbose_name="رقم الهاتف")
    email = models.EmailField(unique=True,verbose_name="البريد الإلكتروني")
    address= models.TextField(blank=True, null=True,verbose_name="العنوان")
    created_at = models.DateTimeField(auto_now_add=True,verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True,verbose_name="اخر تحديث")
    class Meta:
        verbose_name = "عميل"
        verbose_name_plural = "العملاء"
        ordering = ['name']
    def __str__(self):
        return f"{self.name} - {self.phone}"
    
    def total_spent(self):
        """ حساب إجمالي المبلغ الذي أنفقه العميل """
        total = self.invoces.filter(status='paid').aggregate(
           total = models.Sum('total_amount')
        )['total'] or 0
        return total if total else 0
    
class Invoice(models.Model):
    """ نموذج الفاتورة في نظام نقاط البيع """
    PAYMENT_METHODS = [
        ('cash', 'نقدي'),
        ('credit_card', 'بطاقة ائتمان'),
        ('bank_transfer', 'تحويل بنكي'),
        ('check', 'شيك'),
    ]
    STATUS_CHOICES = [
         ('draft', 'مسودة'),
        ('pending', 'قيد الانتظار'),
        ('paid', 'مدفوع'),
        ('cancelled', 'ملغى'),
        ('refunded', 'مرتجع'),
    ]
    invoice_number = models.CharField(max_length=20, unique=True,
                                      verbose_name="رقم الفاتورة")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE,
                                 related_name='invoces',verbose_name="العميل")
    date= models.DateTimeField(default=timezone.now,verbose_name="تاريخ الفاتورة")
    subtotal= models.DecimalField(max_digits=12, decimal_places=2,default=0,
                                     verbose_name="المجموع الفرعي")
    discount= models.DecimalField(max_digits=10, decimal_places=2,default=0,
                                     verbose_name="الخصم")
    tax= models.DecimalField(max_digits=10, decimal_places=2,default=0,
                                     verbose_name="الضريبة")
    tax_rate= models.DecimalField(max_digits=5, decimal_places=2,default=0,
                                     verbose_name="نسبة الضريبة")
    grand_total= models.DecimalField(max_digits=12, decimal_places=2,default=0,
                                     verbose_name="الاجمالى المنهائى")
    notes= models.TextField(blank=True, null=True,verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True,verbose_name="تاريخ الإنشاء")

    class Meta:
        verbose_name = "فاتورة"
        verbose_name_plural = "الفواتير"
        ordering = ['-date']
    def __str__(self):
        return f"فاتورة {self.invoice_number} - {self.customer.name if self.customer else 'زائر'}"
    def save(self, *args, **kwargs):
        """توليد رقم فاتورة تلقائيًا وحساب المجاميع"""
        if not self.invoice_number:
            data_str=timezone.now().strftime("%Y%m%d")
            last_invoice = Invoice.objects.filter(invoice_number__startswith=f'INV-{data_str}'
            ).order_by('-invoice_number').first ()
            if last_invoice:
                last_number = int(last_invoice.invoice_number.split('-')[-1])
                new_number = f'{last_number + 1:03d}'
            else:
                new_number = '001'
            self.invoice_number = f'INV-{data_str}-{new_number}'
        
        self.subtotal= sum(item.total for item in self.items.all())
        self.tax= (self.subtotal - self.discount) * (self.tax_rate / 100)
        self.grand_total= self.subtotal - self.discount + self.tax

        super().save(*args, **kwargs)

class InvoiceItem(models.Model):
    """ نموذج عنصر الفاتورة في نظام نقاط البيع """
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE,
                                related_name='items',verbose_name="الفاتورة")
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                               verbose_name="المنتج")
    quantity = models.IntegerField(default=1,validators=[MinValueValidator(1)],
                                   verbose_name="الكمية")
    price = models.DecimalField(max_digits=10, decimal_places=2,
                                     verbose_name=" الوحدةالسعر")
    total = models.DecimalField(max_digits=10, decimal_places=2,
                                verbose_name="المجحموع")
    class Meta:
        verbose_name = "صنف فى الفاتورة"
        verbose_name_plural = "اصناف الفاتورة"
    def __str__(self):
        return f"{self.product.name} x {self.quantity} "
    
    def save(self, *args, **kwargs):
        """ حساب الإجمالي للعنصر """
        self.total = self.quantity * self.price
        super().save(*args, **kwargs)

        if self.invoice.status=='paid':
           self.product.stock -= self.quantity
           self.product.save()