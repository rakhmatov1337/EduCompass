from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        email = data.get("email")
        user.username = email
        user.full_name = data.get("name", "") or data.get("full_name", "")
        user.role = "STUDENT"
        return user
