from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.shortcuts import render, redirect
from django.contrib import messages
from django import forms


class UserForm(forms.ModelForm):
    password = forms.CharField(label='رمز عبور', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_staff']
        labels = {
            'username': 'نام کاربری', 'first_name': 'نام', 'last_name': 'نام خانوادگی',
            'email': 'ایمیل', 'is_staff': 'دسترسی کارمند',
        }

    def clean_password(self):
        password = self.cleaned_data['password']
        validate_password(password, self.instance)
        return password


def is_admin(user):
    return user.is_superuser


@user_passes_test(is_admin)
def user_list(request):
    return render(request, 'accounts/users.html', {'users': User.objects.order_by('username')})


@user_passes_test(is_admin)
def user_create(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, f'کاربر «{user.username}» ایجاد شد.')
            return redirect('accounts:users')
    else:
        form = UserForm()
    return render(request, 'accounts/user_form.html', {'form': form})
