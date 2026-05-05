from django import forms
from .models import Demand, DemandResponse, Comment
from locations.models import Location


class DemandForm(forms.ModelForm):
    class Meta:
        model = Demand
        fields = ['title', 'content', 'type', 'location', 'deadline', 'is_urgent']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入标题'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': '请详细描述您的需求'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.Select(attrs={'class': 'form-control'}),
            'deadline': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_urgent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['location'].queryset = Location.objects.all()
        self.fields['location'].empty_label = '请选择位置'
        self.fields['deadline'].required = False


class DemandResponseForm(forms.ModelForm):
    class Meta:
        model = DemandResponse
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '请输入响应内容'}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['score', 'content']
        widgets = {
            'score': forms.Select(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '请输入评价内容'}),
        }
