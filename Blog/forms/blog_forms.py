# Blog/forms/blog_forms.py
from django import forms
from ..models import Category

class BlogGeneratorForm(forms.Form):
    topic = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'vTextField'}),
        help_text="Enter the main topic for your blog post"
    )
    keywords = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={'class': 'vTextField'}),
        help_text="Enter comma-separated keywords for SEO optimization"
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        widget=forms.Select(attrs={'class': 'vSelectField'}),
        help_text="Select the category for this blog post"
    )