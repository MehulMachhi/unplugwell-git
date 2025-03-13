from django.views.generic import ListView , DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView , UpdateView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.http import condition
import json

from .models import Post , Category , Tag
from .seo import generate_schema_markup
from .services import BlogGenerator
from .serializers import CategoryListSerializer
from django.contrib.sites.models import Site
from rest_framework.generics import ListAPIView
from rest_framework.filters import SearchFilter
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import status

class PostList(ListView):
    model = Post
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        queryset = Post.objects.filter(status='published')
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(excerpt__icontains=search_query)
            )
        return queryset


# class PostDetail(DetailView):
#     model = Post
#     context_object_name = 'post'

#     def get_queryset(self):
#         return Post.objects.filter(status='published')

#     def get_context_data(self , **kwargs):
#         context = super().get_context_data(**kwargs)
#         post = self.get_object()

#         # Add SEO context
#         context['meta'] = {
#             'title': post.meta_title or post.title ,
#             'description': post.meta_description or post.excerpt ,
#             'keywords': post.focus_keywords ,
#             'canonical_url': post.canonical_url or self.request.build_absolute_uri() ,
#             'robots': post.robots ,
#         }

#         # Add Schema.org markup
#         context['schema_markup'] = generate_schema_markup(post)

#         return context


@staff_member_required
@csrf_protect
def generate_content(request):
    """API endpoint for generating blog content"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            topic = data.get('topic')

            if not topic:
                return JsonResponse({
                    'success': False ,
                    'error': 'Topic is required'
                })

            generator = BlogGenerator()
            blog_data = generator.generate_blog_content(topic)

            # Return generated content
            return JsonResponse({
                'success': True ,
                'content': blog_data['content'] ,
                'excerpt': blog_data['excerpt'] ,
                'meta_title': blog_data['meta_title'] ,
                'meta_description': blog_data['meta_description'] ,
                'focus_keywords': blog_data['focus_keywords'] ,
                'suggested_tags': blog_data.get('suggested_tags' , []) ,
                'estimated_reading_time': blog_data.get('estimated_reading_time' , 5)
            })

        except Exception as e:
            return JsonResponse({
                'success': False ,
                'error': str(e)
            })

    return JsonResponse({
        'success': False ,
        'error': 'Invalid request method'
    })


@staff_member_required
def preview_generated_content(request):
    """Preview generated content before saving"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            content = data.get('content')

            if not content:
                return JsonResponse({
                    'success': False ,
                    'error': 'Content is required'
                })

            # Format content for preview
            preview_html = f"""
            <div class="preview-content">
                <div class="preview-body">
                    {content}
                </div>
            </div>
            """

            return JsonResponse({
                'success': True ,
                'preview_html': preview_html
            })

        except Exception as e:
            return JsonResponse({
                'success': False ,
                'error': str(e)
            })

    return JsonResponse({
        'success': False ,
        'error': 'Invalid request method'
    })


@staff_member_required
@csrf_protect
def regenerate_section(request):
    """Regenerate specific section of the content"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            topic = data.get('topic')
            section = data.get('section')

            if not topic or not section:
                return JsonResponse({
                    'success': False ,
                    'error': 'Topic and section are required'
                })

            generator = BlogGenerator()
            new_section = generator.generate_section(topic , section)

            return JsonResponse({
                'success': True ,
                'content': new_section
            })

        except Exception as e:
            return JsonResponse({
                'success': False ,
                'error': str(e)
            })

    return JsonResponse({
        'success': False ,
        'error': 'Invalid request method'
    })

class CategoryListView(ListAPIView):
    serializer_class = CategoryListSerializer
    filter_backends = [SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        site_param = self.request.query_params.get('site')
        queryset = Category.objects.all()

        if site_param:
            site = get_object_or_404(Site, domain=site_param)  
            queryset = queryset.filter(site=site)
        if site_param:
            try:
                site = get_object_or_404(Site, domain=site_param)
                queryset = queryset.filter(site=site)
            except Http404:
                raise ValidationError({
                    'site': f'Site with domain "{site_param}" does not exist.'
                })
        else:
            raise ValidationError({
                'site': 'please provide a site parameter in the query string'
            })
        return queryset
    
# class CategoryViewSet(ListAPIView):
#     queryset = Category.objects.all()
#     serializer_class = CategoryListSerializer  

#     def get_queryset(self):
#         site_id = self.request.query_params.get('site')
#         if site_id:
#             return Category.objects.filter(site_id=site_id)
#         return Category.objects.all()