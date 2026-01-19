import { Outlet, Link, useLocation } from 'react-router-dom'
import { logout } from '../services/auth'
import './Layout.css'

export default function Layout() {
  const location = useLocation()

  const handleLogout = () => {
    logout()
    window.location.href = '/login'
  }

  return (
    <div className="app">
      <header className="header">
        <h1>Coffee-Berry Stores Management</h1>
        <nav className="nav">
          <Link 
            to="/stores" 
            className={location.pathname.startsWith('/stores') ? 'active' : ''}
          >
            Stores
          </Link>
          <Link 
            to="/map" 
            className={location.pathname === '/map' ? 'active' : ''}
          >
            Map
          </Link>
          <button onClick={handleLogout}>Logout</button>
        </nav>
      </header>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}
