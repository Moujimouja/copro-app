import { useState, useEffect } from 'react'
import { QRCodeSVG } from 'qrcode.react'
import './ReportIncident.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function ReportIncident() {
  const [formData, setFormData] = useState({
    type: 'incident', // 'incident' ou 'request'
    service_instance_ids: [], // Array d'IDs d'équipements
    reporter_name: '',
    reporter_email: '',
    reporter_phone: '',
    title: '',
    description: '',
    location: ''
  })
  const [equipments, setEquipments] = useState([])
  const [equipmentSearch, setEquipmentSearch] = useState('')
  const [loading, setLoading] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState(null)
  const [fieldErrors, setFieldErrors] = useState({})
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

  const validateForm = () => {
    const errors = {}
    
    // Validation du type
    if (!formData.type || (formData.type !== 'incident' && formData.type !== 'request')) {
      errors.type = 'Veuillez sélectionner un type de demande (Incident ou Demande)'
    }
    
    // Validation de l'équipement (obligatoire seulement pour les incidents)
    if (formData.type === 'incident' && (!formData.service_instance_ids || formData.service_instance_ids.length === 0)) {
      errors.service_instance_ids = 'Veuillez sélectionner au moins un équipement concerné'
    }
    
    // Validation du titre
    if (!formData.title || formData.title.trim().length === 0) {
      errors.title = 'Le titre est obligatoire'
    } else if (formData.title.trim().length < 3) {
      errors.title = 'Le titre doit contenir au moins 3 caractères'
    }
    
    // Validation de la description
    if (!formData.description || formData.description.trim().length === 0) {
      errors.description = 'La description est obligatoire'
    } else if (formData.description.trim().length < 10) {
      errors.description = 'La description doit contenir au moins 10 caractères'
    }
    
    // Validation de la localisation (optionnelle, mais si remplie, doit avoir au moins 3 caractères)
    if (formData.location && formData.location.trim().length > 0 && formData.location.trim().length < 3) {
      errors.location = 'La localisation doit contenir au moins 3 caractères si renseignée'
    }
    
    // Validation du nom
    if (!formData.reporter_name || formData.reporter_name.trim().length === 0) {
      errors.reporter_name = 'Le nom est obligatoire'
    } else if (formData.reporter_name.trim().length < 2) {
      errors.reporter_name = 'Le nom doit contenir au moins 2 caractères'
    }
    
    // Validation de l'email
    if (!formData.reporter_email || formData.reporter_email.trim().length === 0) {
      errors.reporter_email = 'L\'adresse email est obligatoire'
    } else {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      if (!emailRegex.test(formData.reporter_email.trim())) {
        errors.reporter_email = 'Veuillez entrer une adresse email valide (exemple: nom@exemple.com)'
      }
    }
    
    // Validation du téléphone (optionnel, mais si rempli, doit être valide)
    if (formData.reporter_phone && formData.reporter_phone.trim().length > 0) {
      // Nettoyer le numéro (enlever espaces, tirets, points)
      const cleanPhone = formData.reporter_phone.replace(/[\s\-\.]/g, '')
      // Vérifier que c'est un numéro français valide (10 chiffres commençant par 0)
      if (!/^0[1-9][0-9]{8}$/.test(cleanPhone)) {
        errors.reporter_phone = 'Veuillez entrer un numéro de téléphone français valide (10 chiffres, exemple: 0612345678)'
      }
    }
    
    setFieldErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setFieldErrors({})
    
    // Validation côté client
    if (!validateForm()) {
      setError('Veuillez corriger les erreurs dans le formulaire')
      return
    }
    
    setLoading(true)

    try {
      const response = await fetch(`${API_URL}/api/v1/public/tickets`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          type: formData.type,
          // Pour l'instant, on prend le premier équipement sélectionné (le backend n'accepte qu'un seul équipement)
          service_instance_id: formData.service_instance_ids && formData.service_instance_ids.length > 0 
            ? formData.service_instance_ids[0] 
            : null,
          title: formData.title.trim(),
          description: formData.description.trim(),
          location: formData.location ? formData.location.trim() : null,
          reporter_name: formData.reporter_name.trim(),
          reporter_email: formData.reporter_email.trim(),
          reporter_phone: formData.reporter_phone && formData.reporter_phone.trim() 
            ? formData.reporter_phone.replace(/[\s\-\.]/g, '') 
            : null
        })
      })

      if (response.ok) {
        setSubmitted(true)
      } else {
        try {
          const data = await response.json()
          // Gérer les erreurs de validation FastAPI qui peuvent être un tableau
          if (Array.isArray(data.detail)) {
            const errors = {}
            data.detail.forEach(err => {
              if (typeof err === 'object' && err.msg && err.loc) {
                const field = err.loc[err.loc.length - 1] // Dernier élément du chemin
                errors[field] = err.msg
              }
            })
            setFieldErrors(errors)
            setError('Veuillez corriger les erreurs dans le formulaire')
          } else if (typeof data.detail === 'string') {
            setError(data.detail)
          } else if (data.detail && typeof data.detail === 'object') {
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
    const newFormData = {
      ...formData,
      [name]: value
    }
    
    // Si le type change vers "Demande", effacer les équipements sélectionnés
    if (name === 'type' && value === 'request') {
      newFormData.service_instance_ids = []
      setEquipmentSearch('')
      if (fieldErrors.service_instance_ids) {
        setFieldErrors(prev => {
          const newErrors = { ...prev }
          delete newErrors.service_instance_ids
          return newErrors
        })
      }
    }
    
    setFormData(newFormData)
    
    // Effacer l'erreur du champ quand l'utilisateur commence à taper
    if (fieldErrors[name]) {
      setFieldErrors(prev => {
        const newErrors = { ...prev }
        delete newErrors[name]
        return newErrors
      })
    }
  }

  const toggleEquipment = (equipmentId) => {
    setFormData(prev => {
      const currentIds = prev.service_instance_ids || []
      const newIds = currentIds.includes(equipmentId)
        ? currentIds.filter(id => id !== equipmentId)
        : [...currentIds, equipmentId]
      return {
        ...prev,
        service_instance_ids: newIds
      }
    })
    
    // Effacer l'erreur si un équipement est sélectionné
    if (fieldErrors.service_instance_ids) {
      setFieldErrors(prev => {
        const newErrors = { ...prev }
        delete newErrors.service_instance_ids
        return newErrors
      })
    }
  }

  const removeEquipment = (equipmentId) => {
    setFormData(prev => ({
      ...prev,
      service_instance_ids: (prev.service_instance_ids || []).filter(id => id !== equipmentId)
    }))
  }

  const toggleSelectAllEquipments = () => {
    if (equipments.length === 0) return
    if (formData.service_instance_ids.length === equipments.length) {
      setFormData(prev => ({
        ...prev,
        service_instance_ids: []
      }))
    } else {
      setFormData(prev => ({
        ...prev,
        service_instance_ids: equipments.map(eq => eq.id)
      }))
    }
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
              type: 'incident',
              service_instance_ids: [],
              reporter_name: '',
              reporter_email: '',
              reporter_phone: '',
              title: '',
              description: '',
              location: ''
            })
            setEquipmentSearch('')
          }}>
            Faire une autre demande
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="report-incident-page">
      <div className="report-header">
        <h1>Faire une demande</h1>
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
          <label htmlFor="type">Type de demande *</label>
          <select
            id="type"
            name="type"
            value={formData.type}
            onChange={handleChange}
            required
            className={fieldErrors.type ? 'error' : ''}
          >
            <option value="incident">Incident</option>
            <option value="request">Demande</option>
          </select>
          {fieldErrors.type && (
            <span className="field-error">{fieldErrors.type}</span>
          )}
        </div>

        {formData.type === 'incident' && (
          <div className="form-group">
            <label>
              Équipements concernés *
              {formData.service_instance_ids && formData.service_instance_ids.length > 0 && (
                <span className="selected-count">
                  ({formData.service_instance_ids.length} sélectionné{formData.service_instance_ids.length > 1 ? 's' : ''})
                </span>
              )}
            </label>
            
            {/* Équipements sélectionnés (tags) */}
            {formData.service_instance_ids && formData.service_instance_ids.length > 0 && (
              <div className="selected-equipments-tags">
                {formData.service_instance_ids.map(equipmentId => {
                  const equipment = equipments.find(eq => eq.id === equipmentId)
                  if (!equipment) return null
                  return (
                    <span key={equipmentId} className="equipment-tag">
                      {equipment.name}
                      {equipment.building && <span className="tag-building"> ({equipment.building})</span>}
                      <button
                        type="button"
                        onClick={() => removeEquipment(equipmentId)}
                        className="tag-remove"
                        title="Retirer"
                      >
                        ×
                      </button>
                    </span>
                  )
                })}
              </div>
            )}

            {/* Multiselect d'équipements */}
            <div className="equipment-multiselect">
              <div className="multiselect-header">
                <input
                  type="text"
                  placeholder="Rechercher un équipement..."
                  value={equipmentSearch}
                  onChange={(e) => setEquipmentSearch(e.target.value)}
                  className="equipment-search-input"
                />
                <button
                  type="button"
                  onClick={toggleSelectAllEquipments}
                  className="btn-select-all"
                >
                  {formData.service_instance_ids.length === equipments.length
                    ? 'Tout désélectionner'
                    : 'Tout sélectionner'}
                </button>
              </div>
              
              {/* Liste des équipements filtrés, groupés par bâtiment */}
              <div className="equipment-list-container">
                {(() => {
                  // Filtrer les équipements selon la recherche
                  const filteredEquipments = equipments.filter(eq => {
                    const searchLower = equipmentSearch.toLowerCase()
                    return eq.name.toLowerCase().includes(searchLower) ||
                           (eq.building && eq.building.toLowerCase().includes(searchLower))
                  })

                  // Grouper par bâtiment
                  const groupedByBuilding = {}
                  filteredEquipments.forEach(eq => {
                    const buildingName = eq.building || 'Autres'
                    if (!groupedByBuilding[buildingName]) {
                      groupedByBuilding[buildingName] = []
                    }
                    groupedByBuilding[buildingName].push(eq)
                  })

                  if (Object.keys(groupedByBuilding).length === 0) {
                    return (
                      <div className="no-equipments-found">
                        Aucun équipement trouvé
                      </div>
                    )
                  }

                  return Object.entries(groupedByBuilding).map(([buildingName, buildingEquipments]) => (
                    <div key={buildingName} className="equipment-building-group">
                      <div className="building-header">{buildingName}</div>
                      <div className="equipment-list">
                        {buildingEquipments.map(equipment => (
                          <label
                            key={equipment.id}
                            className={`equipment-checkbox-label ${formData.service_instance_ids.includes(equipment.id) ? 'selected' : ''}`}
                          >
                            <input
                              type="checkbox"
                              checked={formData.service_instance_ids.includes(equipment.id)}
                              onChange={() => toggleEquipment(equipment.id)}
                            />
                            <span className="equipment-name">{equipment.name}</span>
                            <span className="equipment-status">({equipment.status})</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  ))
                })()}
              </div>
            </div>
            
            {fieldErrors.service_instance_ids && (
              <span className="field-error">{fieldErrors.service_instance_ids}</span>
            )}
          </div>
        )}

        <div className="form-group">
          <label htmlFor="title">Titre {formData.type === 'incident' ? "de l'incident" : "de la demande"} *</label>
          <input
            type="text"
            id="title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
            className={fieldErrors.title ? 'error' : ''}
            placeholder={formData.type === 'incident' ? "Ex: Ascenseur en panne" : "Ex: Demande de réparation"}
          />
          {fieldErrors.title && (
            <span className="field-error">{fieldErrors.title}</span>
          )}
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
            className={fieldErrors.description ? 'error' : ''}
            placeholder="Décrivez le problème en détail..."
          />
          {fieldErrors.description && (
            <span className="field-error">{fieldErrors.description}</span>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="location">Localisation précise</label>
          <input
            type="text"
            id="location"
            name="location"
            value={formData.location}
            onChange={handleChange}
            className={fieldErrors.location ? 'error' : ''}
            placeholder="Ex: Rez-de-chaussée, Bâtiment A (optionnel)"
          />
          {fieldErrors.location && (
            <span className="field-error">{fieldErrors.location}</span>
          )}
        </div>

        <h3>Vos coordonnées</h3>
        <p className="form-hint">Le nom et l'email sont obligatoires, le téléphone est optionnel</p>

        <div className="form-group">
          <label htmlFor="reporter_name">Nom *</label>
          <input
            type="text"
            id="reporter_name"
            name="reporter_name"
            value={formData.reporter_name}
            onChange={handleChange}
            required
            className={fieldErrors.reporter_name ? 'error' : ''}
            placeholder="Votre nom"
          />
          {fieldErrors.reporter_name && (
            <span className="field-error">{fieldErrors.reporter_name}</span>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="reporter_email">Email *</label>
          <input
            type="email"
            id="reporter_email"
            name="reporter_email"
            value={formData.reporter_email}
            onChange={handleChange}
            required
            className={fieldErrors.reporter_email ? 'error' : ''}
            placeholder="votre@email.com"
          />
          {fieldErrors.reporter_email && (
            <span className="field-error">{fieldErrors.reporter_email}</span>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="reporter_phone">Téléphone</label>
          <input
            type="tel"
            id="reporter_phone"
            name="reporter_phone"
            value={formData.reporter_phone}
            onChange={handleChange}
            className={fieldErrors.reporter_phone ? 'error' : ''}
            placeholder="06 12 34 56 78 (optionnel)"
          />
          {fieldErrors.reporter_phone && (
            <span className="field-error">{fieldErrors.reporter_phone}</span>
          )}
        </div>

        <button type="submit" disabled={loading} className="btn-submit">
          {loading 
            ? 'Envoi en cours...' 
            : formData.type === 'incident' 
              ? 'Créer l\'incident' 
              : 'Envoyer la demande'}
        </button>
      </form>
    </div>
  )
}

export default ReportIncident

