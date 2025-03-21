import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Replace these with your actual client ID and client secret
CLIENT_ID_APP: str = os.getenv("CLIENT_ID_APP")
CLIENT_SECRET_APP: str = os.getenv("CLIENT_SECRET_APP")
REDIRECT_URI = 'http://localhost'

# Twitch OAuth2 endpoints
AUTH_URL = 'https://id.twitch.tv/oauth2/authorize'
TOKEN_URL = 'https://id.twitch.tv/oauth2/token'

# All available scopes
SCOPES = [
    'analytics:read:extensions', 'analytics:read:games', 'bits:read', 'channel:edit:commercial',
    'channel:manage:broadcast', 'channel:manage:extensions', 'channel:manage:polls', 'channel:manage:predictions',
    'channel:manage:redemptions', 'channel:manage:schedule', 'channel:manage:videos', 'channel:read:editors',
    'channel:read:goals', 'channel:read:hype_train', 'channel:read:polls', 'channel:read:predictions',
    'channel:read:redemptions', 'channel:read:stream_key', 'channel:read:subscriptions', 'clips:edit',
    'moderation:read', 'moderator:manage:announcements', 'moderator:manage:automod', 'moderator:manage:banned_users',
    'moderator:manage:blocked_terms', 'moderator:manage:unban_requests', 'moderator:read:chat_messages', 'moderator:manage:chat_messages', 'moderator:manage:chat_settings',
    'moderator:manage:shield_mode', 'moderator:manage:shoutouts', 'moderator:read:automod_settings', 'moderator:read:warnings',
    'moderator:read:blocked_terms', 'moderator:read:banned_users', 'moderator:read:unban_requests', 'moderator:read:chat_settings', 'moderator:read:followers', 'moderator:read:shield_mode',
    'moderator:read:shoutouts', 'user:edit', 'user:edit:follows', 'user:manage:blocked_users', 'user:manage:chat_color',
    'user:manage:whispers', 'user:read:blocked_users', 'user:read:broadcast', 'user:read:email', 'user:read:follows',
    'user:read:subscriptions', 'moderator:manage:warnings', 'channel:moderate', 'chat:edit', 'chat:read', 'whispers:read', 'whispers:edit',
    'moderator:read:moderators', 'moderator:read:vips', 'channel:bot', 'channel:manage:ads', 'channel:manage:guest_star',
    'channel:manage:moderators', 'channel:manage:raids', 'channel:manage:vips', 'channel:read:ads', 'channel:read:charity',
    'channel:read:guest_star', 'channel:read:vips', 'moderator:manage:automod_settings', 'moderator:manage:guest_star',
    'moderator:read:chatters', 'moderator:read:guest_star', 'moderator:read:suspicious_users', 'user:bot', 'user:edit:broadcast',
    'user:read:chat', 'user:read:emotes', 'user:read:moderated_channels', 'user:write:chat'
]

def get_auth_url():
    scope_str = '%20'.join(SCOPES)
    auth_url = f"{AUTH_URL}?client_id={CLIENT_ID_APP}&redirect_uri={REDIRECT_URI}&response_type=code&scope={scope_str}"
    return auth_url

def get_tokens(auth_code):
    data = {
        'client_id': CLIENT_ID_APP,
        'client_secret': CLIENT_SECRET_APP,
        'code': auth_code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI
    }
    response = requests.post(TOKEN_URL, data=data)
    print("Response status code:", response.status_code)
    print("Response content:", response.content)
    return response.json()

if __name__ == "__main__":
    print("Go to the following URL to authorize the application:")
    print(get_auth_url())
    auth_code = input("Enter the authorization code: ")
    tokens = get_tokens(auth_code)
    print("Access Token:", tokens.get('access_token'))
    print("Refresh Token:", tokens.get('refresh_token'))