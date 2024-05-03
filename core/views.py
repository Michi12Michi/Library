import random as rnd
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http.response import HttpResponse as HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import DetailView, ListView
from .forms import RegisterForm
from .models import Author, Book, Category, Hold, WaitList

# Create your views here.
def homepage(request):
    return render(request, "core/homepage.html")

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            # SEND AN EMAIL WITH USERNAME AND CREDENTIALS
            send_mail(subject="Registration complete!", 
                      message=generate_welcome_email(form.cleaned_data),
                      from_email=None, 
                      recipient_list=[f"{form.cleaned_data['email']}"],
                      fail_silently=False)
            return redirect(reverse("registration-complete"))
    else:
        form = RegisterForm()
    context = {"form": form}
    return render(request, "registration/registration_form.html", context)

def register_success(request):
    return render(request, "registration/registration_complete.html")

def generate_welcome_email(data):
    return f'''Dear {data['first_name']} {data['last_name']}, we are glad to welcome you to our Public Library.\nHere's a recap about your registration data:\n\nEmail: {data['email']}\nPassword: {data['password1']}\n\nWe strongly encourage you to keep your password secret.\nYou can change your password anytime in the Profile section on our website.\nFeel free to contact our staff in case of troubles.\nKind regards, Public Library.'''

def help_page(request):
    return render(request, "core/help_page.html")

def search(request):
    context = {}
    querystring = request.GET.get('q')
    if not querystring:
        return redirect(reverse("homepage"))
    else:
        context["authors"] = Author.objects.filter(last_name__icontains=querystring)
        context["books"] = Book.objects.filter(title__icontains=querystring)
        context["categories"] = Category.objects.filter(name__icontains=querystring)
        return render(request, "core/search.html", context)    

class BooksPerAuthorListView(ListView):
    template_name = "core/books_per_author_list.html"
    context_object_name = "books"
    paginate_by = 5

    def get_queryset(self):
        self.author = get_object_or_404(Author, slug=self.kwargs["slug"])
        return self.author.book_set.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["author"] = get_object_or_404(Author, slug=self.kwargs["slug"])
        return context

class BookDetailView(DetailView):
    model = Book
    template_name = "core/book_detail.html"
    context_object_name = "book"

def random_book(request):
    books = Book.objects.all()
    r_num = rnd.choice(books).pk
    book_rendering = books.get(pk=r_num)
    return redirect(reverse("book-detail", kwargs={"slug": book_rendering.authors.first().slug, "pk":r_num}))

@login_required
def profile(request):
    context = {}
    context["holds"] = request.user.hold_set.order_by("-pk").all()
    context["checkouts"] = request.user.checkout_set.order_by("-pk").all()
    context["waitinglists"] = request.user.waitlist_set.order_by("-pk").all()
    return render(request, "core/profile_manage.html", context)
        
class AuthorsFullListView(ListView):
    model = Author
    queryset = Author.objects.order_by("last_name").all()
    template_name = "core/all_authors_list.html"
    context_object_name = "authors"
    paginate_by = 50

class BooksFullListView(ListView):
    model = Book
    queryset = Book.objects.order_by("title").all()
    template_name = "core/all_books_list.html"
    context_object_name = "books"
    paginate_by = 50

@login_required
def hold_book(request, pk):
    context = {}
    if not request.user.is_active:
        context["message"] = "Sadly, you cannot hold any book, neither apply to any waiting list.\nThis functionality has been deactived due to an uncorrect behavior on this site.\nPlease, contact our helpdesk."
    else:
        book = get_object_or_404(Book, pk=pk)
        if already_hold := Hold.objects.filter(book=book, user=request.user):
            context["message"] = "Sadly, you cannot hold this book, because... you already did it (LOL).\n"
            return render(request, "core/book_request.html", context)
        elif already_wait := WaitList.objects.filter(book=book, user=request.user):
            context["message"] = "You already joined the waiting list!\n"
            return render(request, "core/book_request.html", context)
        else:
            if book.is_checkout or book.is_hold:
                context["message"] = "Sadly, you cannot hold this book, because it was checked out already.\n"
                new_wait = WaitList.objects.create(book=book, user=request.user)
                context["message"] += "You have been successfully registered to a reserved waiting list. We will email you when the book will be available again!\n"
                context["success"] = True
            else:
                new_hold = Hold.objects.create(book=book, user=request.user)
                context["message"] = f"Good news! You successfully submitted a hold request! Remember, it will expire on {new_hold.end_time.strftime('%A %d %Y @%H:%M')}! Check it out as soon as possible!"
                context["success"] = True
    return render(request, "core/book_request.html", context)

@login_required
def delete_hold_book(request, pk):
    current_hold = get_object_or_404(Hold, pk=pk)
    current_hold.delete()
    return redirect(reverse('profile-view'))

@login_required
def delete_waitlist_book(request, pk):
    current_wait = get_object_or_404(WaitList, pk=pk)
    current_wait.delete()
    return redirect(reverse('profile-view'))
