from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import F
from .models import BlogPost, BlogCategory


def blog_list(request):
    category = request.GET.get('category', '').strip()
    posts = BlogPost.objects.all()

    if category and category in [c.value for c in BlogCategory]:
        posts = posts.filter(category=category)

    paginator = Paginator(posts, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    featured = BlogPost.objects.filter(is_featured=True).first()
    categories = BlogCategory.choices

    context = {
        'posts': page_obj,
        'page_obj': page_obj,
        'featured': featured,
        'categories': categories,
        'selected_category': category,
    }
    return render(request, 'blog/blog_list.html', context)


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    BlogPost.objects.filter(pk=post.pk).update(views=F('views') + 1)
    related = BlogPost.objects.filter(category=post.category).exclude(pk=post.pk)[:3]
    return render(request, 'blog/blog_detail.html', {'post': post, 'related': related})
