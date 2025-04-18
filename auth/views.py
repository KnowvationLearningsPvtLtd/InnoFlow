
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

class RegisterView(APIView):
    def post(self, request):
        # ... (existing code)
        # Add email sending after user creation:
        uid = urlsafe_base64_encode(force_bytes(user.id))
        token = default_token_generator.make_token(user)
        verification_link = f"http://localhost:8000/auth/verify-email/{uid}/{token}/"
        
        send_mail(
            'Verify Your Email',
            render_to_string('emails/verification_email.html', {'verification_link': verification_link}),
            os.getenv('EMAIL_HOST_USER'),
            [user.email],
            fail_silently=False,
        )


class PasswordResetView(APIView):
    def post(self, request):
        email = request.data.get('email')
        user = User.objects.filter(email=email).first()
        if user:
            # Generate reset link (similar to email verification)
            # Send email with reset link
            return Response({"message": "Password reset email sent"})
        return Response({"error": "User not found"}, status=404)

class PasswordResetConfirmView(APIView):
    def post(self, request, uidb64, token):
        # Validate token and update password
        # (Refer to earlier code snippets)