from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from image_uploader.models import User, AccountTier


class CustomUserCreationForm(UserCreationForm):
    tier = forms.ModelChoiceField(queryset=AccountTier.objects.all(), initial=1)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('tier',)


# class CustomUserChangeForm(UserChangeForm):
#     tier = forms.ChoiceField(choices=User.TIER_CHOICES)

#     class Meta(UserChangeForm.Meta):
#         model = User
#         fields = UserChangeForm.Meta.fields + ('tier',)
