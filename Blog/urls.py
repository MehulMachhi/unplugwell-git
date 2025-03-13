from django.urls import path , include
from rest_framework.routers import DefaultRouter
from .api_views import (
    MasterCategoryViewSet ,
    CategoryViewSet ,
    TagViewSet ,
    CommentViewSet,
    PostViewFilter,
    UnplugPublishedPostsView,
    PostDetailView,
    PostsLatestDataView,
    PostsPopularDataView,
    PostCategoryDataView,
    CategorySlugDataView,
    UnplugPublishedPostsWPView,
    PostCreateView
    
)
from .views import (
    PostList ,
    generate_content ,
    preview_generated_content ,
    regenerate_section,
    CategoryListView
)

# API Router
router = DefaultRouter()
router.register(r'master-categories' , MasterCategoryViewSet , basename='master-category')
# router.register(r'categories' , CategoryViewSet , basename='category')
router.register(r'tags' , TagViewSet , basename='tag')
# router.register(r'posts' , PostViewSet , basename='post')
router.register(r'comments' , CommentViewSet , basename='comment')
app_name = 'blog'
urlpatterns = [
    path('api/' , include(router.urls)) ,
    path('posts-list/' , PostList.as_view() , name='post_list') ,
    path('generate-content/' , generate_content , name='generate_content') ,
    path('preview-content/' , preview_generated_content , name='preview_content') ,
    path('regenerate-section/' , regenerate_section , name='regenerate_section') ,
    path('get-categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/', PostViewFilter.as_view(), name='post-filter'),
    path('posts/', UnplugPublishedPostsView.as_view(), name='published-posts-list'),
    path('post/<slug:slug>/', PostDetailView.as_view(), name='post-slug'),
    path('posts-latest/', PostsLatestDataView.as_view(), name='latest-posts-list'),
    path('posts-popular/', PostsPopularDataView.as_view(), name='popular-posts-list'),
    path('posts-category/', PostCategoryDataView.as_view(), name='category-posts-list'),
    path('category-slug/', CategorySlugDataView.as_view(), name='category-posts-slug'),
    path('all-posts/', UnplugPublishedPostsWPView.as_view(), name='published-posts-list'),
    path('posts/create/', PostCreateView.as_view(), name='post-create'),
]