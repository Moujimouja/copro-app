import { useState, useEffect } from 'react'
import { QRCodeSVG } from 'qrcode.react'
import './ReportIncident.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function ReportIncident() {
  const [formData, setFormData] = useState({
    service_instance_id: null,
    reporter_name: '',
    reporter_email: '',
    reporter_phone: '',
    title: '',
    description: '',
    location: ''
  })
  const [equipments, setEquipments] = useState([])
  const [loading, setLoading] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState(null)
  const [showQR, setShowQR] = useState(false)

  useEffect(() => {
    loadEquipments()
  }, [])

  const loadEquipments = async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/public/service-instances`)
      if (response.ok) {
        const data = await response.json()
        setEquipments(data)
      }
    } catch (error) {
      console.error('Erreur chargement équipements:', error)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_URL}/api/v1/public/tickets`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      })

      if (response.ok) {
        setSubmitted(true)
      } else {
        try {
          const data = await response.json()
          // Gérer les erreurs de validation FastAPI qui peuvent être un tableau
          if (Array.isArray(data.detail)) {
            const errorMessages = data.detail.map(err => {
              if (typeof err === 'object' && err.msg) {
                const field = err.loc ? err.loc.slice(1).join('.') : 'Champ'
                return `${field}: ${err.msg}`
              }
              return String(err)
            }).join('; ')
            setError(errorMessages || 'Erreur de validation')
          } else if (typeof data.detail === 'string') {
            setError(data.detail)
          } else if (data.detail && typeof data.detail === 'object') {
            // Si c'est un objet avec un message
            setError(data.detail.msg || data.detail.message || 'Erreur lors de la soumission')
          } else {
            setError(`Erreur ${response.status}: ${response.statusText}`)
          }
        } catch (parseError) {
          setError(`Erreur ${response.status}: ${response.statusText}`)
        }
      }
    } catch (error) {
      setError('Erreur de connexion. Veuillez réessayer.')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: name === 'service_instance_id' 
        ? (value ? Number(value) : null) 
        : value
    }))
  }

  const qrCodeUrl = `${window.location.origin}/report`

  if (submitted) {
    return (
      <div className="report-incident-page">
        <div className="success-message">
          <h2>✅ Ticket créé avec succès</h2>
          <p>Votre déclaration a été enregistrée et sera analysée par un administrateur.</p>
          <p>Vous recevrez une réponse par email si vous avez fourni votre adresse.</p>
          <button onClick={() => {
            setSubmitted(false)
            setFormData({
              service_instance_id: null,
              reporter_name: '',
              reporter_email: '',
              reporter_phone: '',
              title: '',
              description: '',
              location: ''
            })
          }}>
            Déclarer un autre incident
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="report-incident-page">
      <div className="report-header">
        <h1>Déclaration d'Incident</h1>
        <button 
          className="btn-qr"
          onClick={() => setShowQR(!showQR)}
        >
          {showQR ? 'Masquer' : 'Afficher'} QR Code
        </button>
      </div>

      {showQR && (
        <div className="qr-section">
          <h3>Scanner pour accéder directement au formulaire</h3>
          <div className="qr-container">
            <QRCodeSVG value={qrCodeUrl} size={256} />
            <p className="qr-url">{qrCodeUrl}</p>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="incident-form">
          {error && <div className="error-message">{error}</div>}

        <div className="form-group">
          <label htmlFor="service_instance_id">Équipement concerné</label>
          <select
            id="service_instance_id"
            name="service_instance_id"
            value={formData.service_instance_id || ''}
            onChange={handleChange}
          >
            <option value="">Sélectionner un équipement (optionnel)</option>
            {equipments.map(equipment => (
              <option key={equipment.id} value={equipment.id}>
                {equipment.name} - {equipment.building} ({equipment.status})
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="title">Titre de l'incident *</label>
          <input
            type="text"
            id="title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
            placeholder="Ex: Ascenseur en panne"
          />
        </div>

        <div className="form-group">
          <label htmlFor="description">Description *</label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            required
            rows="5"
            placeholder="Décrivez le problème en détail..."
          />
        </div>

        <div className="form-group">
          <label htmlFor="location">Localisation précise</label>
          <input
            type="text"
            id="location"
            name="location"
            value={formData.location}
            onChange={handleChange}
            placeholder="Ex: Rez-de-chaussée, Bâtiment A"
          />
        </div>

        <h3>Vos coordonnées (optionnel)</h3>

        <div className="form-group">
          <label htmlFor="reporter_name">Nom</label>
          <input
            type="text"
            id="reporter_name"
            name="reporter_name"
            value={formData.reporter_name}
            onChange={handleChange}
            placeholder="Votre nom"
          />
        </div>

        <div className="form-group">
          <label htmlFor="reporter_email">Email</label>
          <input
            type="email"
            id="reporter_email"
            name="reporter_email"
            value={formData.reporter_email}
            onChange={handleChange}
            placeholder="votre@email.com"
          />
        </div>

        <div className="form-group">
          <label htmlFor="reporter_phone">Téléphone</label>
          <input
            type="tel"
            id="reporter_phone"
            name="reporter_phone"
            value={formData.reporter_phone}
            onChange={handleChange}
            placeholder="06 12 34 56 78"
          />
        </div>

        <button type="submit" disabled={loading} className="btn-submit">
          {loading ? 'Envoi en cours...' : 'Envoyer la déclaration'}
        </button>
      </form>
    </div>
  )
}

export default ReportIncident

