# Blog/services.py
import openai
from django.conf import settings
import json


class BlogGenerator:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.model = "gpt-4-turbo-preview"  # or "gpt-3.5-turbo"

    def generate_blog_content(self , topic , keywords=None):
        prompt = f"""
        Generate a comprehensive, engaging blog post about "{topic}".

        Requirements:
        1. Length: Minimum 1200 words
        2. Structure: Include introduction, multiple subheadings, and conclusion
        3. Style: Engaging, informative, and conversational
        4. SEO Optimization: Use relevant keywords naturally

        Please provide the response in the following JSON format:
        {{
            "title": "SEO-optimized title",
            "meta_title": "SEO meta title (60 chars max)",
            "meta_description": "Compelling meta description (160 chars max)",
            "excerpt": "Brief excerpt (160 chars max)",
            "content": "Full blog content with HTML formatting",
            "focus_keywords": "comma-separated keywords",
            "suggested_tags": ["tag1", "tag2", "tag3"],
            "estimated_reading_time": "estimated time in minutes"
        }}
        """

        if keywords:
            prompt += f"\nPlease incorporate these keywords naturally: {', '.join(keywords)}"

        try:
            response = openai.ChatCompletion.create(
                model=self.model ,
                messages=[
                    {"role": "system" , "content": "You are an expert blog writer and SEO specialist."} ,
                    {"role": "user" , "content": prompt}
                ] ,
                temperature=0.7 ,
                max_tokens=4000
            )

            content = response.choices[0].message.content
            return json.loads(content)

        except Exception as e:
            raise Exception(f"Error generating blog content: {str(e)}")