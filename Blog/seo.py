# Blog/seo.py
from django.contrib.sitemaps import Sitemap
from django.utils.html import strip_tags
import re


class BlogSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Post.objects.filter(status='published')

    def lastmod(self , obj):
        return obj.updated_at


def generate_schema_markup(post):
    """Generate Schema.org JSON-LD markup for a blog post"""
    return {
        "@context": "https://schema.org" ,
        "@type": "BlogPosting" ,
        "headline": post.title ,
        "description": post.excerpt ,
        "image": post.featured_image.url if post.featured_image else None ,
        "datePublished": post.published_at.isoformat() if post.published_at else None ,
        "dateModified": post.updated_at.isoformat() if post.updated_at else None ,
        "author": {
            "@type": "Person" ,
            "name": post.author.get_full_name() or post.author.username if post.author else None
        } ,
        "publisher": {
            "@type": "Organization" ,
            "name": "Your Blog Name" ,  # Change this to your blog name
            "logo": {
                "@type": "ImageObject" ,
                "url": "your-logo-url"  # Add your logo URL here
            }
        }
    }


class SEOHealthMixin:
    def get_seo_health(self):
        """Calculate SEO health score and get recommendations"""
        score = 0
        max_score = 100
        checks = []
        recommendations = []

        # Content Length Check (20 points)
        content_length = len(strip_tags(self.content))
        if content_length >= 1500:
            score += 20
            checks.append(('Content Length' , 'Excellent' , 20))
        elif content_length >= 900:
            score += 15
            checks.append(('Content Length' , 'Good' , 15))
            recommendations.append('Consider expanding content to 1500+ words for better ranking')
        else:
            score += 5
            checks.append(('Content Length' , 'Poor' , 5))
            recommendations.append('Content is too short. Aim for at least 900 words')

        # Title Length Check (15 points)
        title_length = len(self.meta_title or self.title)
        if 50 <= title_length <= 60:
            score += 15
            checks.append(('Title Length' , 'Excellent' , 15))
        elif 40 <= title_length <= 70:
            score += 10
            checks.append(('Title Length' , 'Good' , 10))
            recommendations.append('Optimize title length to be between 50-60 characters')
        else:
            score += 5
            checks.append(('Title Length' , 'Poor' , 5))
            recommendations.append('Title length is not optimal. Aim for 50-60 characters')

        # Meta Description Check (15 points)
        meta_desc_length = len(self.meta_description or self.excerpt)
        if 145 <= meta_desc_length <= 160:
            score += 15
            checks.append(('Meta Description' , 'Excellent' , 15))
        elif 130 <= meta_desc_length <= 170:
            score += 10
            checks.append(('Meta Description' , 'Good' , 10))
            recommendations.append('Optimize meta description length to be between 145-160 characters')
        else:
            score += 5
            checks.append(('Meta Description' , 'Poor' , 5))
            recommendations.append('Meta description length is not optimal. Aim for 145-160 characters')

        # Focus Keywords Check (15 points)
        if self.focus_keywords:
            keywords = [k.strip() for k in self.focus_keywords.split(',')]
            content_text = strip_tags(self.content).lower()
            title_text = self.title.lower()

            keyword_score = 0
            for keyword in keywords:
                keyword = keyword.lower()
                if keyword in title_text:
                    keyword_score += 5
                content_count = content_text.count(keyword)
                if content_count >= 3 and content_count <= 8:
                    keyword_score += 5
                elif content_count > 8:
                    recommendations.append(
                        f'Keyword "{keyword}" appears too many times. Reduce usage to avoid keyword stuffing')
                elif content_count < 3:
                    recommendations.append(f'Keyword "{keyword}" appears too few times. Include it at least 3 times')

            keyword_score = min(15 , keyword_score)
            score += keyword_score
            checks.append(('Keyword Usage' , 'Good' if keyword_score > 10 else 'Fair' , keyword_score))
        else:
            checks.append(('Keyword Usage' , 'Missing' , 0))
            recommendations.append('No focus keywords defined. Add relevant keywords')

        # Image SEO Check (10 points)
        image_score = 0
        if self.featured_image:
            if self.image_alt:
                image_score += 5
            else:
                recommendations.append('Add alt text to featured image')

            if self.featured_image.name.lower().endswith(('.jpg' , '.png' , '.webp')):
                image_score += 5
            else:
                recommendations.append('Use optimized image formats (JPG, PNG, or WebP)')
        else:
            recommendations.append('Add a featured image to improve visual appeal and sharing')

        score += image_score
        checks.append(('Image Optimization' , 'Good' if image_score > 5 else 'Poor' , image_score))

        # URL Optimization (10 points)
        url_score = 0
        if len(self.slug) <= 60:
            url_score += 5
        else:
            recommendations.append('URL is too long. Keep it under 60 characters')

        if re.match(r'^[a-z0-9-]+$' , self.slug):
            url_score += 5
        else:
            recommendations.append('URL should only contain lowercase letters, numbers, and hyphens')

        score += url_score
        checks.append(('URL Optimization' , 'Good' if url_score > 5 else 'Poor' , url_score))

        # Internal Linking Check (15 points)
        link_pattern = r'href=["\'](?!http)[^"\']*["\']'
        internal_links = len(re.findall(link_pattern , self.content))
        if internal_links >= 3:
            score += 15
            checks.append(('Internal Linking' , 'Excellent' , 15))
        elif internal_links >= 1:
            score += 10
            checks.append(('Internal Linking' , 'Good' , 10))
            recommendations.append('Add more internal links (aim for at least 3)')
        else:
            score += 0
            checks.append(('Internal Linking' , 'Poor' , 0))
            recommendations.append('No internal links found. Add links to other relevant content')

        # Schema Markup Check (10 points)
        schema_score = 0
        schema_markup = generate_schema_markup(self)

        if schema_markup.get('headline'):
            schema_score += 2
        if schema_markup.get('description'):
            schema_score += 2
        if schema_markup.get('image'):
            schema_score += 2
        if schema_markup.get('datePublished'):
            schema_score += 2
        if schema_markup.get('author' , {}).get('name'):
            schema_score += 2

        score += schema_score
        checks.append(('Schema Markup' , 'Good' if schema_score >= 8 else 'Fair' , schema_score))

        if schema_score < 10:
            recommendations.append('Complete all schema markup fields for better search visibility')

        health_status = 'Excellent' if score >= 90 else 'Good' if score >= 70 else 'Fair' if score >= 50 else 'Poor'

        return {
            'score': score ,
            'max_score': max_score ,
            'status': health_status ,
            'checks': checks ,
            'recommendations': recommendations
        }

    def get_seo_health_display(self):
        """Get a formatted display of SEO health"""
        health = self.get_seo_health()
        status_colors = {
            'Excellent': 'success' ,
            'Good': 'info' ,
            'Fair': 'warning' ,
            'Poor': 'danger'
        }

        return {
            'score': health['score'] ,
            'status': health['status'] ,
            'status_color': status_colors[health['status']] ,
            'checks': health['checks'] ,
            'recommendations': health['recommendations']
        }