from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from .models import BlogPost, Newsletter, Subscriber, Notification
from django.core.paginator import Paginator
# BLOG

def blog_list(request):
    """Affiche la liste paginée des articles de blog."""
    articles_list = BlogPost.objects.filter(statut='publie').order_by('-date_publication')

    paginator = Paginator(articles_list, 6)  # 6 articles = 3 lignes de 2 colonnes
    page_number = request.GET.get('page')
    articles = paginator.get_page(page_number)

    return render(request, 'blog/blog_list.html', {
        'articles': articles,
        'page_obj': articles,  # utile pour les templates de pagination Django
    })

def blog_detail(request, slug):
    article = get_object_or_404(BlogPost, slug=slug, statut='publie')
    article.incrementer_vues()
    return render(request, 'blog/blog_detail.html', {'article': article})


# NEWSLETTER
def newsletter_list(request):
    newsletters = Newsletter.objects.all()
    return render(request, 'newsletter/newsletter_list.html', {'newsletters': newsletters})

def newsletter_detail(request, pk):
    newsletter = get_object_or_404(Newsletter, pk=pk)
    return render(request, 'newsletter/newsletter_detail.html', {'newsletter': newsletter})


# SUBSCRIPTION
def subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        nom = request.POST.get('nom')
        if email:
            sub, created = Subscriber.objects.get_or_create(email=email)
            if not created:
                sub.actif = True
                sub.save()
            return render(request, 'newsletter/success.html', {'email': email})
    return render(request, 'newsletter/subscribe.html')


# NOTIFICATIONS UTILISATEUR
def mes_notifications(request):
    if not request.user.is_authenticated:
        return redirect('login')
    notifications = request.user.notifications.all()
    return render(request, 'notifications/list.html', {'notifications': notifications})

def lire_notification(request, pk):
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.marquer_comme_lue()
    if notif.url_action:
        return redirect(notif.url_action)
    return render(request, 'notifications/detail.html', {'notif': notif})
