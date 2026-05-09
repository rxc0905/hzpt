from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import Location


class LocationForm(forms.ModelForm):
    longitude = forms.FloatField(
        label='经度',
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
    )
    latitude = forms.FloatField(
        label='纬度',
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
    )

    class Meta:
        model = Location
        fields = ['name', 'campus_area', 'longitude', 'latitude', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '位置名称'}),
            'campus_area': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
