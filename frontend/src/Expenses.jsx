import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import './Expenses.css'

function Expenses() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    // Vérifier si l'utilisateur est connecté
    const checkLogin = () => {
      const token = localStorage.getItem('token')
      setIsLoggedIn(!!token)
    }
    
    checkLogin()
    
    // Écouter les changements de localStorage
    window.addEventListener('storage', checkLogin)
    window.addEventListener('loginStateChanged', checkLogin)
    
    return () => {
      window.removeEventListener('storage', checkLogin)
      window.removeEventListener('loginStateChanged', checkLogin)
    }
  }, [])

  if (!isLoggedIn) {
    return (
      <div className="expenses-page">
        <div className="expenses-error">
          <div className="error-content">
            <h2>Accès restreint</h2>
            <p>Vous devez avoir un compte et être connecté pour consulter les dépenses de la copropriété.</p>
            <button onClick={() => navigate('/login')} className="btn-login-redirect">
              Se connecter
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="expenses-page">
      <div className="expenses-header">
        <h1>Suivi des Dépenses</h1>
      </div>
      <div className="expenses-iframe-container">
        <iframe
          width="100%"
          height="800"
          src="https://lookerstudio.google.com/embed/reporting/8a6389bc-3386-4ae0-95b7-0ccfd8f5ad67/page/biQHD"
          frameBorder="0"
          style={{ border: 0 }}
          allowFullScreen
          sandbox="allow-storage-access-by-user-activation allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox"
          title="Suivi des dépenses"
        />
      </div>
    </div>
  )
}

export default Expenses

