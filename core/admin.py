from django.contrib import admin
from .models import Author, Book, Category, CheckOut, Editor, Hold, Section, User, WaitList

class UserAdmin(admin.ModelAdmin):
    list_per_page = 25
    list_display = ["first_name", "last_name", "email", "is_active", "is_staff", "is_superuser"]
    list_filter = ["last_name", "is_active"]

class AuthorAdmin(admin.ModelAdmin):
    list_per_page = 25
    list_display = ["last_name", "first_name",]
    ordering = ["last_name"]
    readonly_fields = ("slug",)

class BookAdmin(admin.ModelAdmin):
    list_per_page = 25
    list_display = ["title", "year", "slug", "is_hold", "is_checkout"]
    ordering = ["title"]
    readonly_fields = ("slug",)

class HoldAdmin(admin.ModelAdmin):
    list_per_page = 25
    list_display = ["pk", "start_time", "end_time", "book", "user"]
    fields = ["start_time", "end_time", "book", "user"]
    ordering = ["pk"]
    readonly_fields = ("start_time", "end_time",)

class CheckOutAdmin(admin.ModelAdmin):
    list_per_page = 25
    list_display = ["pk", "start_time", "end_time", "book", "user", "email_sent", "is_book_returned"]
    fields = ["start_time", "end_time", "book", "user", "is_book_returned"]
    ordering = ["pk"]
    readonly_fields = ("start_time", "end_time", )

class WaitListAdmin(admin.ModelAdmin):
    list_per_page = 25
    list_display = ["pk", "start_time", "book", "user"]
    ordering = ["pk"]

# Register your models here.
admin.site.register(Author, AuthorAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(Category)
admin.site.register(CheckOut, CheckOutAdmin)
admin.site.register(Editor)
admin.site.register(Hold, HoldAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Section)
admin.site.register(WaitList, WaitListAdmin)