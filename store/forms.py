from django import forms
from django.db.models import fields
from .import models

class ReviewForm(forms.ModelForm):
    class Meta:
        model = models.ReviewRating
        fields = ['subject', 'review', 'rating']