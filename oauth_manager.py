"""
OAuth Token Manager for InfraGenie LangGraph Implementation

Handles OAuth 2.0 Client Credentials flow for authenticating with ansible-mcp server.
"""

import os
import requests
import time
from typing import Optional


class OAuthTokenManager:
    """Manages OAuth token lifecycle using client credentials flow"""
    
    def __init__(self, client_id: str, client_secret: str, issuer_url: str, audience: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.issuer_url = issuer_url.rstrip('/')
        self.audience = audience
        self.token = None
        self.token_expires_at = 0
    
    def get_token(self) -> str:
        """Get a valid OAuth token, refreshing if necessary"""
        current_time = time.time()
        
        # Check if we need to refresh the token (with 60 second buffer)
        if not self.token or current_time >= (self.token_expires_at - 60):
            self._refresh_token()
        
        return self.token
    
    def _refresh_token(self):
        """Refresh the OAuth token using client credentials flow"""
        token_url = f"{self.issuer_url}/oauth/token"
        
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "audience": self.audience
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(token_url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            self.token = token_data["access_token"]
            
            # Calculate expiration time (default to 1 hour if not provided)
            expires_in = token_data.get("expires_in", 3600)
            self.token_expires_at = time.time() + expires_in
            
            print(f"OAuth token refreshed, expires in {expires_in} seconds")
            
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to obtain OAuth token: {e}")


def get_oauth_config() -> tuple[str, str, str, str]:
    """
    Get OAuth configuration from environment variables or AWS Parameter Store.
    
    Returns:
        Tuple of (client_id, client_secret, issuer_url, audience)
    """
    # Try to get OAuth configuration from environment variables first
    client_id = os.getenv('ANSIBLE_MCP_CLIENT_ID')
    client_secret = os.getenv('ANSIBLE_MCP_CLIENT_SECRET')
    issuer_url = os.getenv('ANSIBLE_MCP_ISSUER_URL')
    audience = os.getenv('ANSIBLE_MCP_AUDIENCE')
    
    # If environment variables are not available, try AWS Parameter Store
    if not all([client_id, client_secret, issuer_url, audience]):
        try:
            import boto3
            ssm = boto3.client('ssm', region_name='us-east-1')
            
            # Get parameters from Parameter Store
            if not client_id:
                client_id = ssm.get_parameter(Name='/infragenie/oauth/client_id', WithDecryption=True)['Parameter']['Value']
            if not client_secret:
                client_secret = ssm.get_parameter(Name='/infragenie/oauth/client_secret', WithDecryption=True)['Parameter']['Value']
            if not issuer_url:
                issuer_url = ssm.get_parameter(Name='/infragenie/oauth/issuer_url')['Parameter']['Value']
            if not audience:
                audience = ssm.get_parameter(Name='/infragenie/oauth/audience')['Parameter']['Value']
                
            print("OAuth configuration loaded from AWS Parameter Store")
            
        except Exception as e:
            print(f"Failed to load from Parameter Store: {e}")
            # Fall back to checking what's missing from env vars
            missing_vars = []
            if not client_id: missing_vars.append('ANSIBLE_MCP_CLIENT_ID')
            if not client_secret: missing_vars.append('ANSIBLE_MCP_CLIENT_SECRET')
            if not issuer_url: missing_vars.append('ANSIBLE_MCP_ISSUER_URL')
            if not audience: missing_vars.append('ANSIBLE_MCP_AUDIENCE')
            
            raise ValueError(f"Missing required OAuth configuration. Environment variables: {', '.join(missing_vars)}. Parameter Store paths: /infragenie/oauth/*")
    
    return client_id, client_secret, issuer_url, audience