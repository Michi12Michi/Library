from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils.text import slugify

# Create your models here.
class CustomUserManager(BaseUserManager):
    def _create_user(self, email, password, first_name, last_name, **extra_fields):
        if not email:
            raise ValueError("Email must be provided")
        if not password:
            raise ValueError("Password must be provided")
        
        user = self.model(email=self.normalize_email(email),
                          first_name=first_name,
                          last_name=last_name,
                          **extra_fields)
        
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_user(self, email, password, first_name, last_name, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, first_name, last_name, **extra_fields)
    
    def create_superuser(self, email, password, first_name, last_name, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, first_name, last_name, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(db_index=True, unique=True, max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    mobile = models.CharField(max_length=50)
    city = models.CharField(max_length=100)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)

    objects = CustomUserManager() 

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Author(models.Model):
    first_name = models.CharField(max_length=60, verbose_name="Name", null=False, blank=False)
    last_name = models.CharField(max_length=60, verbose_name="Surname", null=False, blank=False)
    slug = models.SlugField(default="", verbose_name="slug", unique=True, null=False, editable=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(f"{self.first_name}-{self.last_name}")
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.last_name}, {self.first_name}"

    def first_letter(self):
        return self.last_name and self.last_name.upper()[0] or ""

class Section(models.Model):
    name = models.CharField(max_length=100, verbose_name="Library section name", null=False, blank=False)

    def __str__(self):
        return f"{self.name}"

class Category(models.Model):
    name = models.CharField(max_length=20, verbose_name="Category", null=False, blank=False)

    def __str__(self):
        return f"{self.name}"
    
    class Meta:
        verbose_name_plural = "Categories"

class Editor(models.Model):
    name = models.CharField(max_length=100, verbose_name="Editor name", null=False, blank=False)
    city = models.CharField(max_length=50, verbose_name="Editor city", null=True, blank=True)

    def __str__(self):
        return f"{self.name}"

class Book(models.Model):
    # AN INVENTARY NUMBER COULD BE ALSO PROVIDED, BOTH AS PK OR NOT
    title = models.CharField(max_length=250, verbose_name="Title", null=False, blank=False)
    description = models.TextField(max_length=2000, null=True, editable=True)
    physical_description = models.CharField(max_length=100, null=True, blank=True)
    year = models.DateField()
    edition = models.ForeignKey(Editor, on_delete=models.PROTECT, null=True, blank=True)
    isbn = models.CharField(max_length=30, verbose_name="ISBN", null=True, blank=True)
    pages = models.IntegerField(null=True, verbose_name="No. of pages", blank=True)
    authors = models.ManyToManyField(Author)
    category = models.ManyToManyField(Category)
    section = models.ForeignKey(Section, on_delete=models.PROTECT, null=True, blank=True)
    is_hold = models.BooleanField(default=False)
    is_checkout = models.BooleanField(default=False)
    slug = models.SlugField(default="", verbose_name="slug", null=False, editable=True)
    
    def __str__(self):
        if self.edition:
            return f"{self.title} ({self.year}, {self.edition.name})"
        else:
            return f"{self.title} ({self.year})"
        
    def first_letter(self):
        return self.title and self.title[0].upper() or ""

    def save(self, *args, **kwargs):
        # if self.slug need to overwrite the record
        if self.slug != "":
            super().save(*args, **kwargs)
        else:
            self.slug = slugify(f"{self.title}")
            slug_already_used = Book.objects.filter(slug__icontains=self.slug).count()
            if slug_already_used:
                self.slug += f"-{slug_already_used+1}"
            super().save(*args, **kwargs)

class WaitList(models.Model):
    start_time = models.DateTimeField(auto_now_add=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Waitlist no. {self.pk}"

class Hold(models.Model):
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Hold no. {self.pk}"
    
    def save(self, **kwargs):
        if not self.pk:
            self.start_time = datetime.now()
            if not self.end_time:
                self.end_time = self.start_time + timedelta(days=5)
        book = Book.objects.get(pk=self.book.pk)
        book.is_hold = True
        book.save()
        super().save(**kwargs)
        self.generate_new_hold_email()

    def delete(self):
        book = Book.objects.get(pk=self.book.pk)
        book.is_hold = False
        book.save()
        if waiting := WaitList.objects.order_by("start_time").filter(book=book).first():
            user = User.objects.get(pk=waiting.user.pk)
            new_hold = Hold.objects.create(book=book, user=user)
            waiting.delete()
        super().delete()

    def generate_new_hold_email(self):
        message = f'''Dear {self.user.first_name} {self.user.last_name}, we are glad to inform you that a book you required is available! Your hold has been successfully submitted!\nHere's the relevant hold data:\n\nTitle: {self.book.title}\nHold start date: {self.start_time.strftime('%A %d %Y @%H:%M')}\nHold expiration date: {self.end_time.strftime('%A %d %Y @%H:%M')}\n\nYour book is waiting for you at the Random Central Library!\n\nFeel free to contact our staff in case of troubles.\nKind regards, Public Library.'''

        send_mail(subject="Registration complete!", 
                      message=message,
                      from_email=None, 
                      recipient_list=[f"{self.user.email}"],
                      fail_silently=False)

class CheckOut(models.Model):
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_book_returned = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)

    def save(self, **kwargs):
        if not self.pk:
            self.start_time = datetime.now()
            if not self.end_time:
                self.end_time = self.start_time + timedelta(days=30)
            book = Book.objects.get(pk=self.book.pk)
            previous_hold = Hold.objects.get(book=book, user=self.user)
            previous_hold.delete()
            book.is_checkout = True
            book.is_hold = False
            book.save()
        if self.is_book_returned:
            book = Book.objects.get(pk=self.book.pk)
            book.is_checkout = False
            book.save()
            if waiting := WaitList.objects.order_by("start_time").filter(book=book).first():
                user = User.objects.get(pk=waiting.user.pk)
                new_hold = Hold.objects.create(book=book, user=user)
                waiting.delete()
        super().save(**kwargs)