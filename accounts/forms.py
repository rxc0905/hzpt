from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator
from .models import User


class RegisterForm(UserCreationForm):
    nickname = forms.CharField(
        label='昵称', max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入昵称'}),
    )
    student_id = forms.CharField(
        label='学号', max_length=20,
        validators=[RegexValidator(r'^\d{6,20}$', message='学号格式不正确，请输入6-20位数字')],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入学号'}),
    )
    phone = forms.CharField(
        label='手机号', max_length=20, required=False,
        validators=[RegexValidator(r'^\d{11}$', message='手机号格式不正确，请输入11位数字')],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入手机号'}),
    )

    class Meta:
        model = User
        fields = ['username', 'nickname', 'student_id', 'phone', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': '请输入用户名'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': '请输入密码'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': '请确认密码'})


class LoginForm(forms.Form):
    username = forms.CharField(label='用户名', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入用户名'}))
    password = forms.CharField(label='密码', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请输入密码'}))


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['nickname', 'student_id', 'phone', 'bio', 'avatar']
        widgets = {
            'nickname': forms.TextInput(attrs={'class': 'form-control'}),
            'student_id': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            import os
            ext = os.path.splitext(avatar.name)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                raise forms.ValidationError('不支持的图片格式，仅支持 JPG/PNG/GIF/WEBP')
            if avatar.size > 5 * 1024 * 1024:
                raise forms.ValidationError('图片大小不能超过5MB')
        return avatar

    def clean_student_id(self):
        student_id = self.cleaned_data.get('student_id', '')
        if student_id and not student_id.isdigit():
            raise forms.ValidationError('学号格式不正确，请输入数字')
        return student_id

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        if phone and (not phone.isdigit() or len(phone) != 11):
            raise forms.ValidationError('手机号格式不正确，请输入11位数字')
        return phone


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(label='旧密码', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password1 = forms.CharField(label='新密码', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password2 = forms.CharField(label='确认新密码', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old = self.cleaned_data.get('old_password')
        if old and not self.user.check_password(old):
            raise forms.ValidationError('旧密码不正确')
        return old

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password1')
        p2 = cleaned_data.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('两次输入的密码不一致')
        if p1:
            validate_password(p1, self.user)
        return cleaned_data
