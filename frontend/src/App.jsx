import { useState, useEffect, useCallback } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom'
import { Toaster, toast } from 'react-hot-toast'
import Status from './Status'
import Admin from './Admin'
import ReportIncident from './ReportIncident'
import Expenses from './Expenses'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function Login() {
  const [activeTab, setActiveTab] = useState('login') // 'login' ou 'register'
  const [email, setEmail] = useState('') // Utiliser email au lieu de username
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')
  const [buildings, setBuildings] = useState([])
  const [registerData, setRegisterData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: '',
    lot_number: '',
    floor: '',
    building_id: null
  })
  const navigate = useNavigate()

  useEffect(() => {
    // Charger les bâtiments pour le formulaire d'inscription
    const loadBuildings = async () => {
      try {
        const response = await fetch(`${API_URL}/api/v1/public/buildings`)
        if (response.ok) {
          const data = await response.json()
          setBuildings(data)
        }
      } catch (error) {
        console.error('Erreur chargement bâtiments:', error)
      }
    }
    if (activeTab === 'register') {
      loadBuildings()
    }
  }, [activeTab])

  const handleLoginSubmit = async (e) => {
    e.preventDefault()
    try {
      const formData = new FormData()
      formData.append('username', email) // OAuth2PasswordRequestForm utilise 'username' mais on y met l'email
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

  const handleRegisterChange = (e) => {
    const { name, value } = e.target
    setRegisterData(prev => ({
      ...prev,
      [name]: name === 'building_id' ? (value ? Number(value) : null) : value
    }))
  }

  const handleRegisterSubmit = async (e) => {
    e.preventDefault()
    
    // Validation des champs obligatoires
    if (!registerData.email) {
      toast.error('L\'email est obligatoire')
      return
    }
    if (!registerData.first_name) {
      toast.error('Le prénom est obligatoire')
      return
    }
    if (!registerData.last_name) {
      toast.error('Le nom est obligatoire')
      return
    }
    if (!registerData.building_id) {
      toast.error('Le bâtiment est obligatoire')
      return
    }
    
    // Validation du mot de passe
    if (registerData.password.length < 8) {
      toast.error('Le mot de passe doit contenir au moins 8 caractères')
      return
    }
    
    if (registerData.password !== registerData.confirmPassword) {
      toast.error('Les mots de passe ne correspondent pas')
      return
    }

    try {
      const dataToSend = {
        email: registerData.email,
        password: registerData.password,
        first_name: registerData.first_name,
        last_name: registerData.last_name,
        building_id: registerData.building_id,
        lot_number: registerData.lot_number || null,
        floor: registerData.floor || null
      }

      const response = await fetch(`${API_URL}/api/v1/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(dataToSend)
      })

      if (response.ok) {
        toast.success('Compte créé avec succès! Votre compte sera activé par un administrateur.')
        setMessage('Compte créé avec succès! Votre compte sera activé par un administrateur.')
        // Réinitialiser le formulaire
        setRegisterData({
          email: '',
          password: '',
          confirmPassword: '',
          first_name: '',
          last_name: '',
          lot_number: '',
          floor: '',
          building_id: null
        })
        // Basculer vers l'onglet de connexion
        setTimeout(() => setActiveTab('login'), 2000)
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Erreur lors de la création du compte' }))
        let errorMessage = errorData.detail || 'Erreur lors de la création du compte'
        if (Array.isArray(errorData.detail)) {
          errorMessage = errorData.detail.map(err => {
            if (typeof err === 'object' && err.msg) {
              const field = err.loc ? err.loc.slice(1).join('.') : 'Champ'
              return `${field}: ${err.msg}`
            }
            return String(err)
          }).join('; ')
        }
        toast.error(`Erreur: ${errorMessage}`)
        setMessage(`Erreur: ${errorMessage}`)
      }
    } catch (error) {
      toast.error('Erreur de connexion. Vérifiez votre connexion internet.')
      setMessage('Erreur: ' + error.message)
    }
  }

  return (
    <div className="login">
      <div className="login-tabs">
        <button
          className={activeTab === 'login' ? 'active' : ''}
          onClick={() => setActiveTab('login')}
        >
          Connexion
        </button>
        <button
          className={activeTab === 'register' ? 'active' : ''}
          onClick={() => setActiveTab('register')}
        >
          Créer un compte
        </button>
      </div>

      {activeTab === 'login' && (
        <div className="login-form-container">
          <h2>Connexion</h2>
          <form onSubmit={handleLoginSubmit}>
            <div className="form-group">
              <label>Email:</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="Votre adresse email"
              />
            </div>
            <div className="form-group">
              <label>Mot de passe:</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="Votre mot de passe"
              />
            </div>
            <button type="submit" className="btn-submit">Se connecter</button>
            {message && <p className="form-message">{message}</p>}
          </form>
        </div>
      )}

      {activeTab === 'register' && (
        <div className="register-form-container">
          <h2>Créer un compte</h2>
          <p className="register-info">Votre compte sera inactif jusqu'à activation par un administrateur.</p>
          <form onSubmit={handleRegisterSubmit}>
            <div className="form-group">
              <label>Email *</label>
              <input
                type="email"
                name="email"
                value={registerData.email}
                onChange={handleRegisterChange}
                required
                placeholder="Ex: jdupont@example.com"
              />
            </div>
            <div className="form-group">
              <label>Mot de passe * (minimum 8 caractères)</label>
              <input
                type="password"
                name="password"
                value={registerData.password}
                onChange={handleRegisterChange}
                required
                minLength={8}
                placeholder="••••••••"
              />
            </div>
            <div className="form-group">
              <label>Confirmer le mot de passe *</label>
              <input
                type="password"
                name="confirmPassword"
                value={registerData.confirmPassword}
                onChange={handleRegisterChange}
                required
                placeholder="••••••••"
              />
            </div>
            <div className="form-group">
              <label>Prénom *</label>
              <input
                type="text"
                name="first_name"
                value={registerData.first_name}
                onChange={handleRegisterChange}
                required
                placeholder="Ex: Jean"
              />
            </div>
            <div className="form-group">
              <label>Nom *</label>
              <input
                type="text"
                name="last_name"
                value={registerData.last_name}
                onChange={handleRegisterChange}
                required
                placeholder="Ex: Dupont"
              />
            </div>
            <div className="form-group">
              <label>Bâtiment *</label>
              <select
                name="building_id"
                value={registerData.building_id || ''}
                onChange={handleRegisterChange}
                required
              >
                <option value="">Sélectionner un bâtiment</option>
                {buildings.map(building => (
                  <option key={building.id} value={building.id}>
                    {building.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Numéro de lot</label>
              <input
                type="text"
                name="lot_number"
                value={registerData.lot_number}
                onChange={handleRegisterChange}
                placeholder="Ex: 12"
              />
            </div>
            <div className="form-group">
              <label>Étage</label>
              <input
                type="text"
                name="floor"
                value={registerData.floor}
                onChange={handleRegisterChange}
                placeholder="Ex: 3"
              />
            </div>
            <button type="submit" className="btn-submit">Créer le compte</button>
            {message && <p className="form-message">{message}</p>}
          </form>
        </div>
      )}
    </div>
  )
}

function AppContent() {
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('token'))
  const [isAdmin, setIsAdmin] = useState(false)
  const navigate = useNavigate()

  // Fonction pour décoder le token JWT et extraire is_superuser
  const decodeToken = (token) => {
    try {
      const base64Url = token.split('.')[1]
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
      const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
      }).join(''))
      return JSON.parse(jsonPayload)
    } catch (error) {
      console.error('Erreur décodage token:', error)
      return null
    }
  }

  useEffect(() => {
    // Vérifier si l'utilisateur est connecté et son rôle
    const checkLogin = () => {
      const token = localStorage.getItem('token')
      setIsLoggedIn(!!token)
      
      if (token) {
        const decoded = decodeToken(token)
        setIsAdmin(decoded?.is_superuser === true)
      } else {
        setIsAdmin(false)
      }
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
    setIsAdmin(false)
    setIsMenuOpen(false)
    // Déclencher un événement pour mettre à jour l'état de connexion
    window.dispatchEvent(new Event('loginStateChanged'))
    // Rediriger vers l'accueil
    navigate('/status')
  }

  const [isMenuOpen, setIsMenuOpen] = useState(false)

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen)
  }

  const closeMenu = () => {
    setIsMenuOpen(false)
  }

  return (
    <div className="app">
      <nav className={isMenuOpen ? 'menu-open' : ''}>
        <div className="nav-header">
          <button className={`burger-menu ${isMenuOpen ? 'active' : ''}`} onClick={toggleMenu} aria-label="Toggle menu">
            <span></span>
            <span></span>
            <span></span>
          </button>
        </div>
        <div className="nav-content">
          <div className="nav-left">
            <Link to="/status" onClick={closeMenu}>Statut de la copropriété</Link>
            <Link to="/report" onClick={closeMenu}>Nouvelle demande ou incident</Link>
            <Link to="/expenses" onClick={closeMenu}>Suivi des dépenses</Link>
            {isLoggedIn && isAdmin && <Link to="/admin" onClick={closeMenu}>Administration</Link>}
          </div>
          <div className="nav-right">
            {isLoggedIn ? (
              <button onClick={handleLogout} className="btn-logout">Déconnexion</button>
            ) : (
              <Link to="/login" onClick={closeMenu}>Login</Link>
            )}
          </div>
        </div>
      </nav>
      <main>
        <Routes>
          <Route path="/" element={<Status />} />
          <Route path="/status" element={<Status />} />
          <Route path="/report" element={<ReportIncident />} />
          <Route path="/expenses" element={<Expenses />} />
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
  )
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  )
}

export default App

