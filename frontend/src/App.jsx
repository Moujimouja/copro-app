import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom'
import { Toaster, toast } from 'react-hot-toast'
import Status from './Status'
import Admin from './Admin'
import ReportIncident from './ReportIncident'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const formData = new FormData()
      formData.append('username', username)
      formData.append('password', password)
      
      const response = await fetch(`${API_URL}/api/v1/auth/login`, {
        method: 'POST',
        body: formData,
      })
      
      if (response.ok) {
        const data = await response.json()
        // Stocker le token
        if (data.access_token) {
          localStorage.setItem('token', data.access_token)
          console.log('Token stocké:', data.access_token.substring(0, 50) + '...')
          toast.success('Connexion réussie!')
          setMessage('Connexion réussie!')
          // Déclencher un événement pour mettre à jour l'état de connexion dans App
          window.dispatchEvent(new Event('loginStateChanged'))
          // Rediriger vers admin immédiatement
          setTimeout(() => navigate('/admin'), 500)
        } else {
          toast.error('Erreur: Token non reçu')
          setMessage('Erreur: Token non reçu')
        }
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Échec de la connexion' }))
        toast.error(`Erreur: ${errorData.detail || 'Échec de la connexion'}`)
        setMessage(`Erreur: ${errorData.detail || 'Échec de la connexion'}`)
      }
    } catch (error) {
      setMessage('Error: ' + error.message)
    }
  }

  return (
    <div className="login">
      <h2>Login</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label>Username:</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <div>
          <label>Password:</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <button type="submit">Login</button>
        {message && <p>{message}</p>}
      </form>
    </div>
  )
}

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('token'))

  useEffect(() => {
    // Vérifier si l'utilisateur est connecté
    const checkLogin = () => {
      const token = localStorage.getItem('token')
      setIsLoggedIn(!!token)
    }
    
    // Vérifier au montage
    checkLogin()
    
    // Écouter les changements de localStorage (pour les autres onglets)
    window.addEventListener('storage', checkLogin)
    
    // Écouter un événement personnalisé pour les changements dans le même onglet
    window.addEventListener('loginStateChanged', checkLogin)
    
    return () => {
      window.removeEventListener('storage', checkLogin)
      window.removeEventListener('loginStateChanged', checkLogin)
    }
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('token')
    setIsLoggedIn(false)
    // Déclencher un événement pour mettre à jour l'état de connexion
    window.dispatchEvent(new Event('loginStateChanged'))
  }

  return (
    <Router>
      <div className="app">
        <nav>
          <div className="nav-left">
            <Link to="/status">Statut de la copropriété</Link>
            <Link to="/report">Déclarer un incident</Link>
            {isLoggedIn && <Link to="/admin">Administration</Link>}
          </div>
          <div className="nav-right">
            {isLoggedIn ? (
              <button onClick={handleLogout} className="btn-logout">Déconnexion</button>
            ) : (
              <Link to="/login">Login</Link>
            )}
          </div>
        </nav>
        <main>
          <Routes>
            <Route path="/" element={<Status />} />
            <Route path="/status" element={<Status />} />
            <Route path="/report" element={<ReportIncident />} />
            <Route path="/admin" element={<Admin />} />
            <Route path="/login" element={<Login />} />
          </Routes>
        </main>
        <Toaster 
          position="top-right"
          toastOptions={{
            duration: 3000,
            style: {
              background: '#363636',
              color: '#fff',
              borderRadius: '8px',
              padding: '12px 16px',
              fontSize: '14px',
            },
            success: {
              duration: 3000,
              iconTheme: {
                primary: '#10b981',
                secondary: '#fff',
              },
            },
            error: {
              duration: 4000,
              iconTheme: {
                primary: '#ef4444',
                secondary: '#fff',
              },
            },
          }}
        />
      </div>
    </Router>
  )
}

export default App

