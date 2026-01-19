/**
 * Authentication service
 */
import api from './api'

export interface LoginCredentials {
  client_id: string
  client_secret: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  refresh_token?: string
}

export async function login(credentials: LoginCredentials): Promise<TokenResponse> {
  // OAuth2 client credentials flow
  const formData = new URLSearchParams()
  formData.append('grant_type', 'client_credentials')
  
  const response = await api.post('/api/v1/auth/oauth/token', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Authorization': `Basic ${btoa(`${credentials.client_id}:${credentials.client_secret}`)}`
    }
  })
  
  const tokenData: TokenResponse = response.data
  localStorage.setItem('access_token', tokenData.access_token)
  
  return tokenData
}

export function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('api_key')
}

export function setApiKey(apiKey: string) {
  localStorage.setItem('api_key', apiKey)
}

export function getApiKey(): string | null {
  return localStorage.getItem('api_key')
}

export function getAccessToken(): string | null {
  return localStorage.getItem('access_token')
}

export function isAuthenticated(): boolean {
  return !!(getAccessToken() || getApiKey())
}
