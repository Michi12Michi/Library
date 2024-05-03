from django.urls import include, path
from . import views

urlpatterns = [
    path('', views.homepage, name="homepage"),
    path('', include("django.contrib.auth.urls")),
    path('random', views.random_book, name="random-book"),
    path('profile', views.profile, name="profile-view"),
    path('search', views.search, name="search"),
    path('authors/all', views.AuthorsFullListView.as_view(), name="authors-list-view"),
    path('books/all', views.BooksFullListView.as_view(), name="books-full-list-view"),
    path('<slug:slug>/list', views.BooksPerAuthorListView.as_view(), name="books-list-view"),
    path('<slug:slug>/detail/<int:pk>', views.BookDetailView.as_view(), name="book-detail"),
    path('hold/<int:pk>', views.hold_book, name="hold-book-view"),
    path('hold/delete/<int:pk>', views.delete_hold_book, name="delete-hold-book-view"),
    path('waitlist/delete/<int:pk>', views.delete_waitlist_book, name="delete-waitlist-book-view"),
    path('help', views.help_page, name="help-page"),
    path('register', views.register, name="register"),
    path('register/success', views.register_success, name="registration-complete"),
    path('request/<int:pk>/checkout', views.hold_book, name="book-checkout"),
]