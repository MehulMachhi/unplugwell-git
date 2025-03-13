from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse
from django.utils import timezone
from django.contrib.sites.models import Site
from ckeditor_uploader.fields import RichTextUploadingField
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .seo import SEOHealthMixin
from .services import BlogGenerator


class BaseModel(models.Model):
    """Base model with common fields"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class SeoMixin(models.Model):
    """Mixin for SEO fields"""
    meta_title = models.CharField(max_length=70 , blank=True , help_text="SEO Meta Title")
    meta_description = models.TextField(blank=True , help_text="SEO Meta Description")
    focus_keywords = models.CharField(max_length=200 , blank=True , help_text="Comma-separated keywords")
    canonical_url = models.URLField(blank=True , help_text="Canonical URL if different from current URL")
    robots = models.CharField(
        max_length=50 ,
        default="index,follow" ,
        help_text="Robot meta tag values (e.g., index,follow)"
    )

    class Meta:
        abstract = True


class MasterCategory(BaseModel):
    """Master category for organizing subcategories"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    icon = models.ImageField(upload_to='categories/icons/' , blank=True)
    featured_image = models.ImageField(upload_to='categories/images/' , blank=True)

    class Meta:
        verbose_name_plural = "Master Categories"
        ordering = ['order' , 'name']

    def __str__(self):
        return self.name

    def save(self , *args , **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args , **kwargs)

    def get_absolute_url(self):
        return reverse('blog:master_category_detail' , kwargs={'slug': self.slug})

    @property
    def active_categories(self):
        return self.categories.filter(is_active=True)

    @property
    def total_posts(self):
        return Post.objects.filter(category__master_category=self , status='published').count()


class Category(BaseModel , SeoMixin):
    """Category model with site-specific settings"""
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    master_category = models.ForeignKey(MasterCategory , on_delete=models.CASCADE , related_name='categories')
    site = models.ForeignKey(Site , on_delete=models.CASCADE , related_name='categories')
    order = models.IntegerField(default=0)
    icon = models.ImageField(upload_to='categories/icons/' , blank=True)
    featured_image = models.ImageField(upload_to='categories/images/' , blank=True)
    show_in_menu = models.BooleanField(default=True)
    parent = models.ForeignKey(
        'self' ,
        null=True ,
        blank=True ,
        related_name='children' ,
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name_plural = "categories"
        ordering = ['site' , 'master_category' , 'order' , 'name']
        unique_together = ['slug' , 'site']

    def __str__(self):
        return f"{self.site.name} - {self.master_category.name} - {self.name}"

    def clean(self):
        if self.parent and self.parent.site != self.site:
            raise ValidationError({'parent': _('Parent category must belong to the same site.')})

    def save(self , *args , **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.meta_title:
            self.meta_title = self.name
        if not self.meta_description:
            self.meta_description = self.description[:160] if self.description else self.name
        super().save(*args , **kwargs)

    def get_absolute_url(self):
        return reverse('blog:category_detail' , kwargs={'slug': self.slug})

    @property
    def active_posts(self):
        return self.posts.filter(status='published' , is_active=True)

    @property
    def recent_posts(self):
        return self.active_posts.order_by('-published_at')[:5]

    @property
    def has_children(self):
        return self.children.exists()

    def get_ancestors(self):
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors[::-1]


class Tag(BaseModel):
    """Tag model with site-specific settings"""
    name = models.CharField(max_length=50)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    site = models.ForeignKey(Site , on_delete=models.CASCADE , related_name='tags')
    featured_image = models.ImageField(upload_to='tags/images/' , blank=True)

    class Meta:
        ordering = ['site' , 'name']
        unique_together = ['name' , 'site']

    def __str__(self):
        return f"{self.site.name} - {self.name}"

    def save(self , *args , **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args , **kwargs)

    def get_absolute_url(self):
        return reverse('blog:tag_detail' , kwargs={'slug': self.slug})

    @property
    def active_posts(self):
        return self.posts.filter(status='published' , is_active=True)

    @property
    def post_count(self):
        return self.active_posts.count()


class Post(BaseModel, SeoMixin, SEOHealthMixin):
    """Post model with complete feature set"""
    STATUS_CHOICES = (
        ('draft' , 'Draft') ,
        ('review' , 'In Review') ,
        ('scheduled' , 'Scheduled') ,
        ('published' , 'Published') ,
        ('archived' , 'Archived') ,
    )

    VISIBILITY_CHOICES = (
        ('public' , 'Public') ,
        ('private' , 'Private') ,
        ('password_protected' , 'Password Protected') ,
    )

    # Basic Fields
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=255)
    subtitle = models.CharField(max_length=200 , blank=True)
    content = RichTextUploadingField()
    excerpt = models.TextField(help_text="SEO-friendly description")

    # Media Fields
    featured_image = models.ImageField(upload_to='blog/images/')
    image_alt = models.CharField(max_length=200 , help_text="SEO-friendly image description")
    featured_video = models.URLField(blank=True , help_text="YouTube or Vimeo URL")

    # Relationships
    site = models.ForeignKey(Site , on_delete=models.CASCADE , related_name='posts')
    author = models.ForeignKey(User , on_delete=models.CASCADE , related_name='blog_posts')
    category = models.ForeignKey(Category , on_delete=models.CASCADE , related_name='posts')
    tags = models.ManyToManyField(Tag , blank=True , related_name='posts')

    # Publishing Fields
    status = models.CharField(max_length=10 , choices=STATUS_CHOICES , default='draft')
    visibility = models.CharField(max_length=20 , choices=VISIBILITY_CHOICES , default='public')
    password = models.CharField(max_length=128 , blank=True , help_text="Required if visibility is password protected")
    published_at = models.DateTimeField(null=True , blank=True)

    # Additional Features
    is_featured = models.BooleanField(default=False)
    allow_comments = models.BooleanField(default=True)
    show_in_feed = models.BooleanField(default=True)
    estimated_reading_time = models.PositiveIntegerField(null=True , blank=True)
    view_count =models.CharField(max_length=200 , blank=True)

    # Related Posts
    related_posts = models.ManyToManyField(
        'self' ,
        blank=True ,
        symmetrical=False ,
        related_name='related_to'
    )

    class Meta:
        ordering = ['-published_at']
        indexes = [
            models.Index(fields=['-published_at']) ,
            models.Index(fields=['slug']) ,
            models.Index(fields=['status']) ,
            models.Index(fields=['visibility']) ,
        ]
        unique_together = ['slug' , 'site']

    def __str__(self):
        return f"{self.site.name} - {self.title}"

    def clean(self):
        if self.visibility == 'password_protected' and not self.password:
            raise ValidationError({'password': _('Password is required for password protected posts.')})
        if self.status == 'published' and not self.category:
            raise ValidationError({'category': _('Category is required for published posts.')})

    def save(self , *args , **kwargs):
        # Generate slug if not provided
        if not self.slug:
            self.slug = slugify(self.title)

        # Auto-fill SEO fields if not provided
        if not self.meta_title:
            self.meta_title = self.title[:70]
        if not self.meta_description:
            self.meta_description = self.excerpt[:160]

        # Set published_at when status changes to published
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()

        # Calculate reading time
        if self.content and not self.estimated_reading_time:
            word_count = len(self.content.split())
            self.estimated_reading_time = round(word_count / 200) 

        super().save(*args , **kwargs)

    def get_absolute_url(self):
        return reverse('blog:post_detail' , kwargs={'slug': self.slug})

    # def increment_view_count(self):
    #     self.view_count += 1
    #     self.save(update_fields=['view_count'])

    @property
    def is_published(self):
        return self.status == 'published' and self.published_at <= timezone.now()

    @property
    def next_post(self):
        return self.__class__.objects.filter(
            site=self.site ,
            status='published' ,
            published_at__gt=self.published_at
        ).order_by('published_at').first()

    @property
    def previous_post(self):
        return self.__class__.objects.filter(
            site=self.site ,
            status='published' ,
            published_at__lt=self.published_at
        ).order_by('-published_at').first()

    def get_related_posts(self):
        """Get related posts based on tags and category"""
        related = self.related_posts.filter(status='published')
        if related.exists():
            return related

        # If no manually selected related posts, find by tags and category
        return Post.objects.filter(
            models.Q(tags__in=self.tags.all()) |
            models.Q(category=self.category) ,
            site=self.site ,
            status='published'
        ).exclude(id=self.id).distinct()[:3]

    @classmethod
    def create_with_ai(cls , topic , author , site , category , keywords=None):
        """Generate a new blog post using AI"""
        try:
            generator = BlogGenerator()
            blog_data = generator.generate_blog_content(topic , keywords)

            # Create the post
            post = cls(
                title=blog_data['title'] ,
                slug=slugify(blog_data['title']) ,
                content=blog_data['content'] ,
                excerpt=blog_data['excerpt'] ,
                meta_title=blog_data['meta_title'] ,
                meta_description=blog_data['meta_description'] ,
                focus_keywords=blog_data['focus_keywords'] ,
                author=author ,
                site=site ,
                category=category ,
                status='draft' ,
                estimated_reading_time=int(blog_data['estimated_reading_time'])
            )
            post.save()

            # Add suggested tags
            for tag_name in blog_data['suggested_tags']:
                tag , _ = Tag.objects.get_or_create(
                    name=tag_name ,
                    site=site ,
                    defaults={'slug': slugify(tag_name)}
                )
                post.tags.add(tag)

            return post , None  # Return post and no error
        except Exception as e:
            return None , str(e)  # Return no post and error message


class Comment(BaseModel):
    """Comment model for blog posts"""
    post = models.ForeignKey(Post , on_delete=models.CASCADE , related_name='comments')
    author_name = models.CharField(max_length=100)
    author_email = models.EmailField()
    author_url = models.URLField(blank=True)
    content = models.TextField()
    parent = models.ForeignKey(
        'self' ,
        null=True ,
        blank=True ,
        on_delete=models.CASCADE ,
        related_name='replies'
    )
    is_approved = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Comment by {self.author_name} on {self.post.title}'

    @property
    def is_reply(self):
        return self.parent is not None

    @property
    def reply_count(self):
        return self.replies.count()


class PostRevision(BaseModel):
    """Model to track post revisions"""
    post = models.ForeignKey(Post , on_delete=models.CASCADE , related_name='revisions')
    title = models.CharField(max_length=200)
    content = models.TextField()
    excerpt = models.TextField()
    author = models.ForeignKey(User , on_delete=models.CASCADE)
    revision_note = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Revision of {self.post.title} at {self.created_at}'
    