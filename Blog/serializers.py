from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from .models import (
    MasterCategory ,
    Category ,
    Tag ,
    Post ,
    Comment ,
    PostRevision
)


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ['id' , 'name' , 'domain']


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id' , 'username' , 'email' , 'first_name' , 'last_name' , 'full_name']

    def get_full_name(self , obj):
        return obj.get_full_name() or obj.username


class MasterCategoryListSerializer(serializers.ModelSerializer):
    total_posts = serializers.IntegerField(read_only=True)
    active_categories_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = MasterCategory
        fields = [
            'id' , 'name' , 'slug' , 'description' , 'order' ,
            'icon' , 'featured_image' , 'is_active' ,
            'total_posts' , 'active_categories_count' ,
            'created_at' , 'updated_at'
        ]


class MasterCategoryDetailSerializer(MasterCategoryListSerializer):
    categories = serializers.SerializerMethodField()

    class Meta(MasterCategoryListSerializer.Meta):
        fields = MasterCategoryListSerializer.Meta.fields + ['categories']

    def get_categories(self , obj):
        categories = obj.categories.filter(is_active=True , site=self.context['site'])
        return CategoryListSerializer(categories , many=True).data


class CategoryListSerializer(serializers.ModelSerializer):
    master_category = MasterCategoryListSerializer(read_only=True)
    post_count = serializers.IntegerField(read_only=True)
    site = SiteSerializer(read_only=True)

    class Meta:
        model = Category
        fields = [
            'id' , 'name' , 'slug' , 'description' , 'master_category' ,
            'site' , 'order' , 'icon' , 'featured_image' , 'show_in_menu' ,
            'is_active' , 'post_count' , 'created_at' , 'updated_at' ,
            'meta_title' , 'meta_description' , 'focus_keywords' ,
            'canonical_url' , 'robots'
        ]


class CategoryDetailSerializer(CategoryListSerializer):
    parent = CategoryListSerializer(read_only=True)
    children = serializers.SerializerMethodField()
    recent_posts = serializers.SerializerMethodField()
    breadcrumbs = serializers.SerializerMethodField()

    class Meta(CategoryListSerializer.Meta):
        fields = CategoryListSerializer.Meta.fields + [
            'parent' , 'children' , 'recent_posts' , 'breadcrumbs'
        ]

    def get_children(self , obj):
        children = obj.children.filter(is_active=True)
        return CategoryListSerializer(children , many=True).data

    def get_recent_posts(self , obj):
        posts = obj.posts.filter(
            status='published' ,
            is_active=True
        ).order_by('-published_at')[:5]
        return PostListSerializer(posts , many=True).data

    def get_breadcrumbs(self , obj):
        breadcrumbs = []
        current = obj
        while current:
            breadcrumbs.append({
                'id': current.id ,
                'name': current.name ,
                'slug': current.slug
            })
            current = current.parent
        return list(reversed(breadcrumbs))


class TagSerializer(serializers.ModelSerializer):
    post_count = serializers.IntegerField(read_only=True)
    site = SiteSerializer(read_only=True)

    class Meta:
        model = Tag
        fields = [
            'id' , 'name' , 'slug' , 'description' , 'site' ,
            'featured_image' , 'is_active' , 'post_count' ,
            'created_at' , 'updated_at'
        ]


class CommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id' , 'post' , 'author_name' , 'author_email' ,
            'author_url' , 'content' , 'parent' , 'is_approved' ,
            'created_at' , 'updated_at' , 'replies'
        ]
        read_only_fields = ['is_approved' , 'created_at' , 'updated_at']

    def get_replies(self , obj):
        if obj.is_reply:
            return []
        replies = obj.replies.filter(is_approved=True)
        return CommentSerializer(replies , many=True).data


class PostRevisionSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = PostRevision
        fields = [
            'id' , 'title' , 'content' , 'excerpt' ,
            'author' , 'revision_note' , 'created_at'
        ]


class PostListSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    category = CategoryListSerializer(read_only=True)
    tags = TagSerializer(many=True , read_only=True)
    site = SiteSerializer(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = [
            'id' , 'title' , 'slug' , 'subtitle' , 'content', 'excerpt' ,
            'featured_image' , 'image_alt' , 'featured_video' ,
            'author' , 'category' , 'tags' , 'site' ,
            'status' , 'visibility' , 'is_featured' ,
            'published_at' , 'estimated_reading_time' ,
            'view_count' , 'comment_count' , 'created_at' ,
            'meta_title' , 'meta_description' , 'focus_keywords' ,
            'canonical_url' , 'robots'
        ]


class PostDetailSerializer(PostListSerializer):
    content = serializers.CharField()
    comments = serializers.SerializerMethodField()
    related_posts = serializers.SerializerMethodField()
    next_post = serializers.SerializerMethodField()
    previous_post = serializers.SerializerMethodField()
    revisions = serializers.SerializerMethodField()
    breadcrumbs = serializers.SerializerMethodField()

    class Meta(PostListSerializer.Meta):
        fields = PostListSerializer.Meta.fields + [
            'content' , 'comments' , 'related_posts' ,
            'next_post' , 'previous_post' , 'revisions' ,
            'breadcrumbs' , 'allow_comments' , 'show_in_feed'
        ]

    def get_comments(self , obj):
        comments = obj.comments.filter(
            parent=None ,
            is_approved=True
        ).select_related('parent')
        return CommentSerializer(comments , many=True).data

    def get_related_posts(self , obj):
        related_posts = obj.get_related_posts()
        return PostListSerializer(related_posts , many=True).data

    def get_next_post(self , obj):
        next_post = obj.next_post
        if next_post:
            return {
                'id': next_post.id ,
                'title': next_post.title ,
                'slug': next_post.slug
            }
        return None

    def get_previous_post(self , obj):
        previous_post = obj.previous_post
        if previous_post:
            return {
                'id': previous_post.id ,
                'title': previous_post.title ,
                'slug': previous_post.slug
            }
        return None

    def get_revisions(self , obj):
        user = self.context.get('request').user
        if user and user.is_staff:
            revisions = obj.revisions.all()
            return PostRevisionSerializer(revisions , many=True).data
        return []

    def get_breadcrumbs(self , obj):
        breadcrumbs = [{
            'name': obj.category.master_category.name ,
            'slug': obj.category.master_category.slug ,
            'type': 'master_category'
        }]

        category = obj.category
        while category:
            breadcrumbs.append({
                'name': category.name ,
                'slug': category.slug ,
                'type': 'category'
            })
            category = category.parent

        breadcrumbs.append({
            'name': obj.title ,
            'slug': obj.slug ,
            'type': 'post'
        })

        return breadcrumbs


class PostCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = [
            'title' , 'subtitle' , 'content' , 'excerpt' ,
            'featured_image' , 'image_alt' , 'featured_video' ,
            'category' , 'tags' , 'status' , 'visibility' ,
            'password' , 'is_featured' , 'allow_comments' ,
            'show_in_feed' , 'meta_title' , 'meta_description' ,
            'focus_keywords' , 'canonical_url' , 'robots'
        ]

    def create(self , validated_data):
        request = self.context.get('request')
        validated_data['author'] = request.user
        validated_data['site'] = request.site
        return super().create(validated_data)


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = [
            'post' , 'parent' , 'author_name' , 'author_email' ,
            'author_url' , 'content'
        ]

    def validate_parent(self , value):
        if value and value.post_id != self.initial_data.get('post'):
            raise serializers.ValidationError(
                "Parent comment must belong to the same post"
            )
        return value
    
class CategoryListLatestSerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = [
            'id' , 'slug', 'name'
        ]

class UserLatestSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'full_name']

    def get_full_name(self , obj):
        return obj.get_full_name() or obj.username
    
class PostListLatestSerializer(serializers.ModelSerializer):
    author = UserLatestSerializer(read_only=True)
    category = CategoryListLatestSerializer(read_only=True)

    class Meta:
        model = Post
        fields = [
            'id' , 'featured_image', 'image_alt' , 'slug' , 'title','excerpt','published_at', 'author', 'category', 'estimated_reading_time', 'view_count'
        ]

# For Published Filter wise UnplugPublishedPostsView API Serializer

class CategoryListPublishedSerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = [
            'id' , 'name' 
        ]

class UserPublishedSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'full_name']

    def get_full_name(self , obj):
        return obj.get_full_name() or obj.username
    
class TagPublishedSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = [
            'id' , 'name'
        ]
    
class PostListPublishedSerializer(serializers.ModelSerializer):
    author = UserPublishedSerializer(read_only=True)
    category = CategoryListPublishedSerializer(read_only=True)
    tags = TagPublishedSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = [
            'id' , 'featured_image', 'image_alt' , 'slug' , 'title','excerpt','published_at', 'author', 'category', 'tags', 'estimated_reading_time', 'view_count'
        ]

# For Slug API Serializer

class CategoryListSlugSerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = [
            'id' , 'name' 
        ]

class UserSlugSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'full_name']

    def get_full_name(self , obj):
        return obj.get_full_name() or obj.username
    
class TagSlugSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = [
            'id' , 'name'
        ]
    
class PostListSlugSerializer(serializers.ModelSerializer):
    author = UserSlugSerializer(read_only=True)
    category = CategoryListSlugSerializer(read_only=True)
    tags = TagSlugSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = [
            'id' , 'featured_image', 'image_alt' , 'slug' , 'title','excerpt','published_at', 'author', 'category', 'tags', 'content', 'estimated_reading_time', 'view_count',
            'meta_title', 'meta_description']
        
# CategorySlugSerializer 
class CategorySlugSerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = [
            'id' , 'name', 'slug', 'description', 'meta_title', 'meta_description' 
        ]

# Post Create Serializer
class PostSerializer(serializers.ModelSerializer):
    featured_image = serializers.ImageField(required=False) 

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'subtitle', 'content', 'excerpt',
            'featured_image', 'image_alt', 'featured_video',
            'site', 'author', 'category', 'tags', 'status',
            'visibility', 'password', 'published_at', 'is_featured',
            'allow_comments', 'show_in_feed', 'estimated_reading_time',
            'view_count', 'related_posts'
        ]

    # def create(self, validated_data):
    #     """Create a new Post with the uploaded image."""
    #     tags = validated_data.pop('tags', [])  # Handle ManyToManyField
    #     related_posts = validated_data.pop('related_posts', [])  # Handle self-relation

    #     post = Post.objects.create(**validated_data)  # Create post
    #     post.tags.set(tags)  # Assign tags
    #     post.related_posts.set(related_posts)  # Assign related posts
        
    #     return post