from django.contrib import admin
from django.urls import path , include
from django.contrib.sitemaps.views import sitemap
from Blog.seo import BlogSitemap
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from Blog.views import (PostList, generate_content, preview_generated_content, regenerate_section, CategoryListView)
from Blog.api_views import (PostViewFilter, UnplugPublishedPostsView, PostDetailView, PostsLatestDataView, PostsPopularDataView)

# Swagger documentation setup
schema_view = get_schema_view(
    openapi.Info(
        title="Blog API" ,
        default_version='v1' ,
        description="API for Blog application" ,
        terms_of_service="https://www.yourapp.com/terms/" ,
        contact=openapi.Contact(email="contact@yourapp.com") ,
        license=openapi.License(name="Your License") ,
    ) ,
    public=True ,
    permission_classes=(permissions.AllowAny ,) ,
)

sitemaps = {
    'blog': BlogSitemap ,
}

urlpatterns = [
                  path('admin/' , admin.site.urls) ,
                  path('ckeditor/' , include('ckeditor_uploader.urls')) ,

                  # API URLs
                  path('api/' , include('Blog.urls')) ,
                  path('api/subscription/' , include('subscription.urls')) , 
                  path('api/message/' , include('message.urls')) , 
                      # This will include your API endpoints
                  path('api-auth/' , include('rest_framework.urls')) ,  # DRF authentication URLs

                  # Swagger documentation URLs
                  path('swagger/' , schema_view.with_ui('swagger' , cache_timeout=0) , name='schema-swagger-ui') ,
                  path('redoc/' , schema_view.with_ui('redoc' , cache_timeout=0) , name='schema-redoc') ,

                  # Original URLs
                  path('' , include('Blog.urls')) ,  # Your regular blog URLs
                  path('sitemap.xml' , sitemap , {'sitemaps': sitemaps} ,
                       name='django.contrib.sitemaps.views.sitemap') ,
                  path('robots.txt' , include('robots.urls')) ,

                #     path('posts-list/' , PostList.as_view() , name='post_list') ,
                # # path('post/<slug:slug>/' , PostDetail.as_view() , name='post_detail') ,
                # # Content Generation URLs
                #     path('generate-content/' , generate_content , name='generate_content') ,
                #     path('preview-content/' , preview_generated_content , name='preview_content') ,
                #     path('regenerate-section/' , regenerate_section , name='regenerate_section') ,
                #     path('get-categories/', CategoryListView.as_view(), name='category-list'),
                #     path('categories/', PostViewFilter.as_view(), name='post-filter'),
                #     path('posts/', UnplugPublishedPostsView.as_view(), name='published-posts-list'),
                #     path('post/<slug:slug>/', PostDetailView.as_view(), name='post-slug'),
                #     path('posts-latest/', PostsLatestDataView.as_view(), name='latest-posts-list'),
                #     path('posts-popular/', PostsPopularDataView.as_view(), name='popular-posts-list'),
              ] + static(settings.MEDIA_URL , document_root=settings.MEDIA_ROOT)