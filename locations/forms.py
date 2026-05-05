from django import forms
from .models import Location


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['name', 'campus_area', 'longitude', 'latitude', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '位置名称'}),
            'campus_area': forms.Select(attrs={'class': 'form-control'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
