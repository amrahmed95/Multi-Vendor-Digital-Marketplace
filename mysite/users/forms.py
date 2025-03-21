from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import Profile

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text='Required. Inform a valid email address.')
    is_vendor = forms.BooleanField(required=False, label='Are you a vendor?')

    # Vendor-specific fields
    business_name = forms.CharField(max_length=255, required=False, label='Business Name')
    contact_email = forms.EmailField(required=False, label='Contact Email')
    contact_phone = forms.CharField(max_length=20, required=False, label='Contact Phone')

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'is_vendor', 'business_name', 'contact_email', 'contact_phone']

    def clean(self):
        cleaned_data = super().clean()
        is_vendor = cleaned_data.get('is_vendor')
        business_name = cleaned_data.get('business_name')
        contact_email = cleaned_data.get('contact_email')
        contact_phone = cleaned_data.get('contact_phone')

        # Validate vendor-specific fields if the user is a vendor
        if is_vendor:
            if not business_name:
                self.add_error('business_name', 'Business Name is required for vendors.')
            if not contact_email:
                self.add_error('contact_email', 'Contact Email is required for vendors.')
            if not contact_phone:
                self.add_error('contact_phone', 'Contact Phone is required for vendors.')

        return cleaned_data
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_picture', 'bio', 'phone_number', 'address', 'city', 'country', 'is_vendor']