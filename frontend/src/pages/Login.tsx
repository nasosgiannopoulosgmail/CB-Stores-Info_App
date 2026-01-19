import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login, setApiKey } from '../services/auth'
import './Login.css'

export default function Login() {
  const navigate = useNavigate()
  const [mode, setMode] = useState<'oauth' | 'apikey'>('oauth')
  const [clientId, setClientId] = useState('')
  const [clientSecret, setClientSecret] = useState('')
  const [apiKeyValue, setApiKeyValue] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleOAuthLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login({ client_id: clientId, client_secret: clientSecret })
      navigate('/stores')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const handleApiKeyLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      setApiKey(apiKeyValue)
      navigate('/stores')
    } catch (err: any) {
      setError('Invalid API key')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-container">
      <div className="login-box">
        <h2>Login</h2>
        
        <div className="login-mode-switch">
          <button
            className={mode === 'oauth' ? 'active' : ''}
            onClick={() => setMode('oauth')}
          >
            OAuth2
          </button>
          <button
            className={mode === 'apikey' ? 'active' : ''}
            onClick={() => setMode('apikey')}
          >
            API Key
          </button>
        </div>

        {error && <div className="error">{error}</div>}

        {mode === 'oauth' ? (
          <form onSubmit={handleOAuthLogin}>
            <div>
              <label>Client ID</label>
              <input
                type="text"
                value={clientId}
                onChange={(e) => setClientId(e.target.value)}
                required
              />
            </div>
            <div>
              <label>Client Secret</label>
              <input
                type="password"
                value={clientSecret}
                onChange={(e) => setClientSecret(e.target.value)}
                required
              />
            </div>
            <button type="submit" disabled={loading}>
              {loading ? 'Logging in...' : 'Login'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleApiKeyLogin}>
            <div>
              <label>API Key</label>
              <input
                type="password"
                value={apiKeyValue}
                onChange={(e) => setApiKeyValue(e.target.value)}
                required
              />
            </div>
            <button type="submit" disabled={loading}>
              {loading ? 'Logging in...' : 'Login'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
