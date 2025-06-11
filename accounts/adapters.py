from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        # Emailni username sifatida belgilaymiz
        user.username = data.get("email") or data.get("id")

        # Rolni STUDENT qilib belgilaymiz
        user.role = "STUDENT"

        return user
