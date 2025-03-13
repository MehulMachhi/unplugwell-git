from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.generics import ListAPIView
from rest_framework import generics
from django.utils import timezone
from .models import (
    MasterCategory,
    Category,
    Tag,
    Post,
    Comment,
    PostRevision
)
from .serializers import (
    MasterCategoryListSerializer,
    MasterCategoryDetailSerializer,
    CategoryListSerializer,
    CategoryDetailSerializer,
    TagSerializer,
    PostListSerializer,
    PostDetailSerializer,
    PostCreateUpdateSerializer,
    CommentSerializer,
    CommentCreateSerializer,
    PostRevisionSerializer,
    PostListLatestSerializer,
    PostListPublishedSerializer,
    PostListSlugSerializer,
    CategorySlugSerializer,
    PostSerializer
)
from rest_framework.pagination import PageNumberPagination
from django.contrib.sites.models import Site
from django.shortcuts import get_object_or_404

class MasterCategoryViewSet(viewsets.ModelViewSet):
    # Add explicit queryset
    queryset = MasterCategory.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'order', 'created_at']
    ordering = ['order', 'name']

    def get_queryset(self):
        queryset = MasterCategory.objects.annotate(
            total_posts=Count('categories__posts',
                filter=Q(categories__posts__status='published',
                        categories__posts__is_active=True)),
            active_categories_count=Count('categories',
                filter=Q(categories__is_active=True))
        )
        return queryset

class CategoryViewSet(viewsets.ModelViewSet):
    # Add explicit queryset
    queryset = Category.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['master_category', 'site', 'is_active', 'show_in_menu']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'order', 'created_at']
    ordering = ['order', 'name']

class TagViewSet(viewsets.ModelViewSet):
    # Add explicit queryset
    queryset = Tag.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['site', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class PostPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = 'page_size' 
    max_page_size = 50

# class PostViewSet(viewsets.ModelViewSet):
#     # Add explicit queryset
#     queryset = Post.objects.all()
#     permission_classes = [IsAuthenticatedOrReadOnly]
#     lookup_field = 'slug'
#     filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
#     filterset_fields = {
#         'category': ['exact'],
#         'tags': ['exact'],
#         'status': ['exact'],
#         'visibility': ['exact'],
#         'is_featured': ['exact'],
#         'published_at': ['gte', 'lte'],
#         'created_at': ['gte', 'lte'],
#     }
#     search_fields = ['title', 'subtitle', 'content', 'excerpt']
#     ordering_fields = ['published_at', 'created_at', 'title', 'view_count']
#     ordering = ['-published_at']

#     def get_serializer_class(self):
#         if self.action in ['create', 'update', 'partial_update']:
#             return PostCreateUpdateSerializer
#         if self.action == 'list':
#             return PostListSerializer
#         return PostDetailSerializer

#     @action(detail=False)
#     def featured(self, request):
#         """Get featured blog posts"""
#         posts = self.get_queryset().filter(
#             status='published',
#             is_featured=True
#         )[:5]
#         serializer = PostListSerializer(posts, many=True)
#         return Response(serializer.data)

class CommentViewSet(viewsets.ModelViewSet):
    # Add explicit queryset
    queryset = Comment.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['post', 'is_approved']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CommentCreateSerializer
        return CommentSerializer

class PostViewFilter(ListAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'category': ['exact'],
        'tags': ['exact'],
        'visibility': ['exact'],
        'is_featured': ['exact'],
        'published_at': ['gte', 'lte'],
        'created_at': ['gte', 'lte'],
    }
    search_fields = ['title', 'subtitle', 'content', 'excerpt']
    ordering_fields = ['published_at', 'created_at', 'title', 'view_count']
    ordering = ['-published_at']

    def get_serializer_class(self):
        """Return the appropriate serializer for the request"""
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return PostCreateUpdateSerializer
        return PostListSerializer  

    def get_queryset(self):
        """Automatically filter posts to return only published posts"""
        queryset = Post.objects.filter(
            status='published', 
            site__domain="unplugwell.com"
        )
        
        # Apply filters dynamically
        return self.filter_queryset(queryset)

    def featured(self, request):
        """Get featured blog posts (without pagination)"""
        posts = self.get_queryset().filter(is_featured=True)[:5]
        serializer = PostListSerializer(posts, many=True)
        return Response(serializer.data)

    def latest(self, request):
        """New API to get the latest published blog posts (with pagination)"""
        posts = self.get_queryset().order_by('-published_at')
        page = self.paginate_queryset(posts)  

        if page is not None:
            serializer = PostListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PostListSerializer(posts, many=True)
        return Response(serializer.data)

class CustomPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'page_size'
    max_page_size = 100

class UnplugPublishedPostsView(ListAPIView):
    serializer_class = PostListPublishedSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        site_domain_param = self.request.query_params.get('site_domain', None)
        queryset = Post.objects.filter(status='published')  

        if site_domain_param:
            queryset = queryset.filter(site__domain=site_domain_param)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response(
                {"message": "No Available Data"},
                status=status.HTTP_404_NOT_FOUND
            )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
class PostDetailView(RetrieveAPIView):
    queryset = Post.objects.all()
    serializer_class = PostListSlugSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'

class PostsLatestDataView(ListAPIView):
    serializer_class = PostListLatestSerializer

    def get_queryset(self):
        site_domain_param = self.request.query_params.get('site_domain', None)
        queryset = Post.objects.filter(status='published').order_by('-published_at')  

        if site_domain_param:
            queryset = queryset.filter(site__domain=site_domain_param)

        return queryset[:4]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response(
                {"message": "No Available Data"},
                status=status.HTTP_404_NOT_FOUND
            )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
class PostsPopularDataView(ListAPIView):
    serializer_class = PostListLatestSerializer
    
    def get_queryset(self):
        site_domain_param = self.request.query_params.get('site_domain', None)
        queryset = Post.objects.filter(status='published').order_by('-view_count')

        if site_domain_param:
            queryset = queryset.filter(site__domain=site_domain_param)

        return queryset[:3]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response(
                {"message": "No Available Data"},
                status=status.HTTP_404_NOT_FOUND
            )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    

# Category-Name wise Data get

class PostCategoryDataView(ListAPIView):
    serializer_class = PostListLatestSerializer
    
    def get_queryset(self):
        site_domain_param = self.request.query_params.get('site_domain', None)
        category_slug_param = self.request.query_params.get('category_slug', None)

        queryset = Post.objects.filter(status='published')

        if site_domain_param and category_slug_param:
            queryset = queryset.filter(
                site__domain=site_domain_param, category__slug__iexact=category_slug_param
            )
        elif site_domain_param:
            queryset = queryset.filter(site__domain=site_domain_param)
        elif category_slug_param:
            queryset = queryset.filter(category__slug__iexact=category_slug_param)

        return queryset.order_by('-view_count')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response(
                {"message": "No Available Data"},
                status=status.HTTP_404_NOT_FOUND
            )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
class CategorySlugDataView(ListAPIView):
    serializer_class = CategorySlugSerializer
    
    def get_queryset(self):
        site_domain_param = self.request.query_params.get('site_domain', None)
        category_slug_param = self.request.query_params.get('category_slug', None)

        queryset = Category.objects.all()

        if site_domain_param and category_slug_param:
            queryset = queryset.filter(
                site__domain=site_domain_param, slug__iexact=category_slug_param
            )
        elif site_domain_param:
            queryset = queryset.filter(site__domain=site_domain_param)
        elif category_slug_param:
            queryset = queryset.filter(slug__iexact=category_slug_param)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response(
                {"message": "No Available Data"},
                status=status.HTTP_404_NOT_FOUND
            )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
class UnplugPublishedPostsWPView(ListAPIView):
    serializer_class = PostListPublishedSerializer

    def get_queryset(self):
        site_domain_param = self.request.query_params.get('site_domain', None)
        queryset = Post.objects.filter(status='published')  

        if site_domain_param:
            queryset = queryset.filter(site__domain=site_domain_param)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response(
                {"message": "No Available Data"},
                status=status.HTTP_404_NOT_FOUND
            )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
class PostCreateView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    queryset = Post.objects.all()
    serializer_class = PostSerializer