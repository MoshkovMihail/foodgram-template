from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailBackend(ModelBackend):
    def authenticate(self, request, username = None, password = None, **kwargs):

        email = username

        if email is None or password is None:
            return None

        try:
            user = User.objects.get(email=email)
            
            if user.check_password(password) and user.is_active:
                return user
                
        except User.DoesNotExist:
            return None
        
        return None