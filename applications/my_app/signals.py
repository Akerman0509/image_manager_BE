

# from allauth.socialaccount.signals import social_account_added, social_account_updated
# from rest_framework.response import Response
# from applications.my_app.models import User
# from allauth.socialaccount.models import SocialAccount, SocialToken
# from django.dispatch import receiver
# from applications.my_app.serializers import GGTokenSerializer
# from applications.my_app.models import GGToken


# @receiver(social_account_added)
# @receiver(social_account_updated)
# def handle_google_login(request, sociallogin, **kwargs):
#     try:
#         account = sociallogin.account  # SocialAccount instance
#         email = account.extra_data.get('email')

#         social_token = SocialToken.objects.get(account=account)
#         access_token_google = social_token.token  # optional: store/use for Google API access
        
#         #only update GGToken if user already exists
#         check_user = User.objects.filter(email=email).first()
#         print (f"User already has GGToken: {check_user}")
#         if check_user:
#             GGToken.objects.update_or_create(
#                 user=check_user,
#                 defaults={'token': access_token_google}
#             )
                
#             print({
#                 'user': {
#                     'id': check_user.id,
#                     'username': check_user.username,
#                     'email': check_user.email,
#                 },
#                 'message': 'GGToken updated successfully',
#                 'google_access_token': access_token_google,
#             })
#             return
        
#         # create GG_auth account
#         new_user = User.objects.create_gg_user(username=account.user.username, email=email)

#         if not new_user:
#             return Response({'error': 'Failed to create user'}, status=500)
        
#         res = {}
#         res['user'] = {
#             'id': new_user.id,
#             'username': new_user.username,
#             'email': new_user.email,
#         }
        
#         print (f"User created: {new_user}")
        
#         #create GGToken
#         serializer = GGTokenSerializer(data={
#             'user': new_user.id,
#             'token': access_token_google
#         })
#         if not serializer.is_valid():
#             return Response({
#                 'message': "Invalid token data",
#                 'errors': serializer.errors
#             }, status=400)
#         serializer.save()
#         res.update({
#             'message': 'Extracting with Google and create account successfully',
#             'google_access_token': access_token_google,
#         })
#         print (res)


#     except SocialAccount.DoesNotExist:
#         return Response({'error': 'No linked Google account'}, status=404)
#     except SocialToken.DoesNotExist:
#         return Response({'error': 'No token found for Google account'}, status=404)

    