from django.contrib import admin
from django.shortcuts import render
from django.utils.html import format_html
from django.template.response import TemplateResponse
from django.urls import reverse, path
from django.utils.safestring import mark_safe
from django.db.models import Count
from django.contrib.admin import SimpleListFilter
from django.db.models import Q
from .models import (
    MasterCategory,
    Category,
    Tag,
    Post,
    Comment,
    PostRevision
)
from django import forms
from django.contrib import messages

class BlogGeneratorForm(forms.Form):
    topic = forms.CharField(max_length=200)
    keywords = forms.CharField(max_length=500, required=False,
                             help_text="Comma-separated keywords")
    category = forms.ModelChoiceField(queryset=Category.objects.all())

class PublishedPostsFilter(SimpleListFilter):
    title = 'published posts'
    parameter_name = 'has_posts'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Has published posts'),
            ('no', 'No published posts'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(posts__status='published').distinct()
        if self.value() == 'no':
            return queryset.exclude(posts__status='published').distinct()

class CategoryInline(admin.TabularInline):
    model = Category
    extra = 1
    fields = ('name', 'site', 'order', 'is_active')
    show_change_link = True

@admin.register(MasterCategory)
class MasterCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'total_posts', 'active_categories_count', 'order', 'is_active', 'created_at')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active', 'created_at', PublishedPostsFilter)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at', 'display_featured_image')
    inlines = [CategoryInline]

    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'order', 'is_active')
        }),
        ('Media', {
            'fields': ('featured_image', 'display_featured_image'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def display_featured_image(self, obj):
        if obj.featured_image:
            return format_html('<img src="{}" width="300" />', obj.featured_image.url)
        return "-"
    display_featured_image.short_description = 'Featured Image Preview'

    def active_categories_count(self, obj):
        return obj.categories.filter(is_active=True).count()
    active_categories_count.short_description = 'Active Categories'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _total_posts=Count('categories__posts', 
                filter=Q(categories__posts__status='published'))
        )
        return queryset

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'master_category', 'site', 'parent', 'post_count', 'order', 'show_in_menu', 'is_active')
    list_editable = ('order', 'show_in_menu', 'is_active')
    list_filter = ('site', 'master_category', 'is_active', 'show_in_menu', PublishedPostsFilter)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at', 'display_featured_image')
    autocomplete_fields = ['parent', 'master_category']

    fieldsets = (
        (None, {
            'fields': (
                'name', 'slug', 'description', 'site', 'master_category',
                'parent', 'order', 'show_in_menu', 'is_active'
            )
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'focus_keywords',
                      'canonical_url', 'robots'),
            'classes': ('collapse',)
        }),
        ('Media', {
            'fields': ('featured_image', 'display_featured_image'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def display_featured_image(self, obj):
        if obj.featured_image:
            return format_html('<img src="{}" width="300" />', obj.featured_image.url)
        return "-"
    display_featured_image.short_description = 'Featured Image Preview'

    def post_count(self, obj):
        return obj.posts.filter(status='published').count()
    post_count.short_description = 'Published Posts'

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'site', 'post_count', 'is_active', 'created_at')
    list_filter = ('site', 'is_active', PublishedPostsFilter)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at', 'display_featured_image')

    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'site', 'is_active')
        }),
        ('Media', {
            'fields': ('featured_image', 'display_featured_image'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def display_featured_image(self, obj):
        if obj.featured_image:
            return format_html('<img src="{}" width="300" />', obj.featured_image.url)
        return "-"
    display_featured_image.short_description = 'Featured Image Preview'

    def post_count(self, obj):
        return obj.posts.filter(status='published').count()
    post_count.short_description = 'Published Posts'

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('author_name', 'author_email', 'content', 'is_approved', 'created_at')

class PostRevisionInline(admin.TabularInline):
    model = PostRevision
    extra = 0
    readonly_fields = ('created_at', 'author')
    fields = ('title', 'excerpt', 'content', 'revision_note', 'author', 'created_at')
    max_num = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title' , 'site' , 'category' , 'author' , 'status' , 'seo_health_score' , 'visibility' ,
                    'is_featured' , 'view_count' , 'get_comment_count' ,
                    'published_at')  # Changed comment_count to get_comment_count
    list_filter = ('site' , 'status' , 'visibility' , 'is_featured' , 'category' ,
                   'author' , 'created_at' , 'published_at')
    search_fields = ('title' , 'content' , 'excerpt')
    prepopulated_fields = {'slug': ('title' ,)}
    readonly_fields = ('created_at' , 'updated_at',
                       'estimated_reading_time' , 'seo_health_display' ,
                       'get_featured_image')  # Changed display_featured_image to get_featured_image
    filter_horizontal = ('tags' , 'related_posts')
    autocomplete_fields = ['category']
    inlines = [CommentInline , PostRevisionInline]

    fieldsets = (
        (None , {
            'fields': (
                'title' , 'slug' , 'subtitle' , 'content' , 'excerpt' ,
                'site' , 'author' , 'category' , 'tags'
            )
        }) ,
        ('SEO Health' , {
            'fields': ('seo_health_display' ,) ,
            'classes': ('collapse' ,) ,
            'description': 'SEO analysis and recommendations'
        }) ,
        ('Media' , {
            'fields': (
                'featured_image' , 'get_featured_image' ,  # Changed display_featured_image to get_featured_image
                'image_alt' , 'featured_video'
            ) ,
            'classes': ('collapse' ,)
        }) ,
        ('Publishing' , {
            'fields': (
                'status' , 'visibility' , 'password' ,
                'published_at' , 'is_featured'
            )
        }) ,
        ('SEO' , {
            'fields': (
                'meta_title' , 'meta_description' , 'focus_keywords' ,
                'canonical_url' , 'robots'
            ) ,
            'classes': ('collapse' ,)
        }) ,
        ('Additional Options' , {
            'fields': (
                'allow_comments' , 'show_in_feed' ,
                'estimated_reading_time' , 'view_count'
            ) ,
            'classes': ('collapse' ,)
        }) ,
        ('Related Content' , {
            'fields': ('related_posts' ,) ,
            'classes': ('collapse' ,)
        }) ,
        ('Timestamps' , {
            'fields': ('created_at' , 'updated_at') ,
            'classes': ('collapse' ,)
        }) ,
    )


    def get_comment_count(self , obj):
        return obj.comments.count()

    get_comment_count.short_description = 'Comments'

    def get_featured_image(self , obj):
        if obj.featured_image:
            return format_html('<img src="{}" width="300" />' , obj.featured_image.url)
        return "-"

    get_featured_image.short_description = 'Featured Image Preview'

    def seo_health_score(self , obj):
        health = obj.get_seo_health()
        return format_html(
            '<span style="color: {};">{}/100 ({})</span>' ,
            {
                'Excellent': '#28a745' ,
                'Good': '#17a2b8' ,
                'Fair': '#ffc107' ,
                'Poor': '#dc3545'
            }[health['status']] ,
            health['score'] ,
            health['status']
        )

    seo_health_score.short_description = 'SEO Health'

    def seo_health_display(self , obj):
        health = obj.get_seo_health()
        html = f'<div style="margin-bottom: 20px;"><h3>SEO Score: {health["score"]}/100 ({health["status"]})</h3></div>'

        # Checks section
        html += '<div style="margin-bottom: 20px;"><h4>SEO Checks:</h4><ul style="list-style-type: none; padding-left: 0;">'
        for check , status , points in health['checks']:
            color = {
                'Excellent': '#28a745' ,
                'Good': '#17a2b8' ,
                'Fair': '#ffc107' ,
                'Poor': '#dc3545'
            }.get(status , '#666')
            html += f'<li style="margin-bottom: 10px;"><strong>{check}:</strong> <span style="color: {color};">{status} ({points} points)</span></li>'
        html += '</ul></div>'

        # Recommendations section
        if health['recommendations']:
            html += '<div><h4>Recommendations:</h4><ul style="color: #dc3545;">'
            for rec in health['recommendations']:
                html += f'<li style="margin-bottom: 5px;">{rec}</li>'
            html += '</ul></div>'
        else:
            html += '<div style="color: #28a745;"><h4>No recommendations needed - SEO is well optimized!</h4></div>'

        return mark_safe(html)

    seo_health_display.short_description = 'SEO Health Analysis'

    def save_model(self , request , obj , form , change):
        if not change:  # If creating new post
            obj.author = request.user
        super().save_model(request , obj , form , change)

        # Create revision
        if change:  # Only create revision when editing
            PostRevision.objects.create(
                post=obj ,
                title=obj.title ,
                content=obj.content ,
                excerpt=obj.excerpt ,
                author=request.user ,
                revision_note=f"Updated by {request.user}"
            )

    def get_queryset(self , request):
        return super().get_queryset(request).select_related(
            'site' , 'category' , 'author'
        ).prefetch_related('tags')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('generate/' ,
                 self.admin_site.admin_view(self.generate_blog_view) ,
                 name='blog_post_generate') ,
        ]
        return custom_urls + urls

    def changelist_view(self , request , extra_context=None):
        extra_context = extra_context or {}
        extra_context['generate_blog_button'] = format_html(
            '<a href="{}" class="button">Generate Blog Post</a>' ,
            'generate/'
        )
        return super().changelist_view(request , extra_context)

    def generate_blog_view(self , request):
        if request.method == 'POST':
            form = BlogGeneratorForm(request.POST)
            if form.is_valid():
                return self.generate_blog(
                    request ,
                    form.cleaned_data['topic'] ,
                    form.cleaned_data['keywords'] ,
                    form.cleaned_data['category']
                )
        else:
            form = BlogGeneratorForm()

        context = {
            'form': form ,
            'title': 'Generate Blog Post' ,
            'media': self.media ,
        }
        return TemplateResponse(request , 'admin/blog/post/generate_blog.html' , context)

    def add_view(self , request , form_url='' , extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_generate'] = True
        return super().add_view(request , form_url , extra_context)

    def change_view(self , request , object_id , form_url='' , extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_generate'] = True
        return super().change_view(request , object_id , form_url , extra_context)

    def response_change(self , request , obj):
        if "_generate-content" in request.POST:
            topic = request.POST.get('topic')
            keywords = request.POST.get('keywords')

            if not topic:
                self.message_user(request , "Please provide a topic" , level='error')
                return self.response_post_save_change(request , obj)

            post , error = Post.create_with_ai(
                topic=topic ,
                author=request.user ,
                site=request.site ,
                category=obj.category ,
                keywords=keywords.split(',') if keywords else None
            )

            if error:
                self.message_user(request , f"Error generating content: {error}" , level='error')
            else:
                self.message_user(request , "Content generated successfully!")
                return self.response_post_save_change(request , obj)

        return super().response_change(request , obj)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author_name', 'post', 'is_reply', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at', 'post__site')
    search_fields = ('author_name', 'author_email', 'content', 'post__title')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': (
                'post', 'parent', 'author_name', 'author_email',
                'author_url', 'content', 'is_approved'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def is_reply(self, obj):
        return obj.parent is not None
    is_reply.boolean = True
    is_reply.short_description = 'Is Reply'

@admin.register(PostRevision)
class PostRevisionAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'created_at')
    list_filter = ('post__site', 'author', 'created_at')
    search_fields = ('post__title', 'revision_note')
    readonly_fields = ('post', 'title', 'content', 'excerpt', 'author',
                      'created_at', 'updated_at')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False