import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import './Admin.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function Admin() {
  const [equipments, setEquipments] = useState([])
  const [tickets, setTickets] = useState([])
  const [buildings, setBuildings] = useState([])
  const [serviceTypes, setServiceTypes] = useState([])
  const [copro, setCopro] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('copro')
  const [showCoproForm, setShowCoproForm] = useState(false)
  const [editingCopro, setEditingCopro] = useState(null)
  const [coproFormData, setCoproFormData] = useState({
    name: '',
    address: '',
    city: '',
    postal_code: '',
    country: 'France'
  })
  const [showEquipmentForm, setShowEquipmentForm] = useState(false)
  const [editingEquipment, setEditingEquipment] = useState(null)
  const [showBuildingForm, setShowBuildingForm] = useState(false)
  const [editingBuilding, setEditingBuilding] = useState(null)
  const [buildingFormData, setBuildingFormData] = useState({
    identifier: '',
    name: '',
    description: '',
    order: 0
  })
  const [formData, setFormData] = useState({
    building_id: '',
    service_type_id: '',
    name: '',
    identifier: '',
    description: '',
    location: '',
    status: 'operational',
    order: 0
  })
  const navigate = useNavigate()

  // Déclarer toutes les fonctions de chargement AVANT le useEffect
  const loadEquipments = useCallback(async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      if (!token) {
        console.log('Aucun token trouvé dans localStorage')
        navigate('/login')
        return
      }

      console.log('Token utilisé pour requête:', token.substring(0, 50) + '...')
      const response = await fetch(
        `${API_URL}/api/v1/admin/service-instances`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )
      if (response.ok) {
        const data = await response.json()
        setEquipments(data)
      } else if (response.status === 401) {
        const errorText = await response.text()
        console.error('Erreur 401 - Token invalide:', errorText)
        localStorage.removeItem('token')
        window.location.href = '/login'
        return
      } else if (response.status === 403) {
        toast.error('Accès refusé. Vous devez être administrateur.')
        navigate('/')
      }
    } catch (error) {
      console.error('Erreur chargement équipements:', error)
    } finally {
      setLoading(false)
    }
  }, [navigate])

  const loadBuildings = useCallback(async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      if (!token) {
        return
      }

      const response = await fetch(`${API_URL}/api/v1/admin/buildings`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setBuildings(data)
      } else if (response.status === 401) {
        localStorage.removeItem('token')
        window.location.href = '/login'
        return
      }
    } catch (error) {
      console.error('Erreur chargement bâtiments:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  const loadServiceTypes = useCallback(async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        return
      }

      const response = await fetch(`${API_URL}/api/v1/admin/service-types`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setServiceTypes(data)
      } else if (response.status === 401) {
        localStorage.removeItem('token')
        window.location.href = '/login'
        return
      }
    } catch (error) {
      console.error('Erreur chargement types de services:', error)
    }
  }, [])

  const loadTickets = useCallback(async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      if (!token) {
        return
      }

      const response = await fetch(
        `${API_URL}/api/v1/admin/tickets`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )
      if (response.ok) {
        const data = await response.json()
        setTickets(data)
      } else if (response.status === 401) {
        localStorage.removeItem('token')
        window.location.href = '/login'
        return
      }
    } catch (error) {
      console.error('Erreur chargement tickets:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  const loadCopro = useCallback(async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      if (!token) {
        return
      }

      const response = await fetch(`${API_URL}/api/v1/admin/copro`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setCopro(data)
      } else if (response.status === 404) {
        // Pas de copropriété configurée, c'est normal
        setCopro(null)
      } else if (response.status === 401) {
        localStorage.removeItem('token')
        window.location.href = '/login'
        return
      }
    } catch (error) {
      console.error('Erreur chargement copropriété:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  // useEffect après toutes les déclarations de fonctions
  useEffect(() => {
    // Vérifier l'authentification
    const token = localStorage.getItem('token')
    console.log('Admin useEffect - Token présent:', !!token)
    if (!token) {
      console.log('Pas de token, redirection vers login')
      navigate('/login')
      return
    }

    console.log('Chargement des données pour onglet:', activeTab)
    // Ne charger les données que si on a un token valide
    // Les fonctions de chargement gèrent elles-mêmes les erreurs 401
    if (activeTab === 'copro') {
      loadCopro()
    } else if (activeTab === 'equipments') {
      loadEquipments()
      loadBuildings()
      loadServiceTypes()
    } else if (activeTab === 'buildings') {
      loadBuildings()
    } else if (activeTab === 'tickets') {
      loadTickets()
    }
  }, [activeTab, loadEquipments, loadBuildings, loadServiceTypes, loadTickets, loadCopro, navigate])

  const updateEquipmentStatus = async (equipmentId, newStatus) => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(
        `${API_URL}/api/v1/admin/service-instances/${equipmentId}/status`,
        {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ status: newStatus })
        }
      )
      if (response.ok) {
        toast.success('Statut mis à jour avec succès')
        loadEquipments()
      } else {
        toast.error('Erreur lors de la mise à jour du statut')
      }
    } catch (error) {
      console.error('Erreur mise à jour statut:', error)
      toast.error('Erreur lors de la mise à jour du statut')
    }
  }

  const createIncident = async (equipmentId, title, message) => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`${API_URL}/api/v1/admin/incidents`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          service_instance_id: equipmentId,
          title,
          message,
          status: 'investigating'
        })
      })
      if (response.ok) {
        toast.success('Incident créé avec succès')
        loadEquipments()
      } else {
        toast.error('Erreur lors de la création de l\'incident')
      }
    } catch (error) {
      console.error('Erreur création incident:', error)
      toast.error('Erreur lors de la création de l\'incident')
    }
  }

  const reviewTicket = async (ticketId, status, createIncident, notes) => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(
        `${API_URL}/api/v1/admin/tickets/${ticketId}/review`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            status,
            create_incident: createIncident,
            admin_notes: notes
          })
        }
      )
      if (response.ok) {
        toast.success('Ticket traité avec succès')
        loadTickets()
      } else {
        toast.error('Erreur lors du traitement du ticket')
      }
    } catch (error) {
      console.error('Erreur traitement ticket:', error)
      toast.error('Erreur lors du traitement du ticket')
    }
  }

  const getStatusClass = (status) => {
    const statusMap = {
      operational: 'status-operational',
      degraded: 'status-degraded',
      partial_outage: 'status-partial',
      major_outage: 'status-major',
      maintenance: 'status-maintenance'
    }
    return statusMap[status] || 'status-unknown'
  }

  const getStatusLabel = (status) => {
    const labelMap = {
      operational: 'Opérationnel',
      degraded: 'Dégradé',
      partial_outage: 'Panne partielle',
      major_outage: 'Panne majeure',
      maintenance: 'Maintenance'
    }
    return labelMap[status] || status
  }

  const openCreateForm = () => {
    setEditingEquipment(null)
    setFormData({
      building_id: '',
      service_type_id: '',
      name: '',
      identifier: '',
      description: '',
      location: '',
      status: 'operational',
      order: 0
    })
    setShowEquipmentForm(true)
  }

  const openEditForm = (equipment) => {
    setEditingEquipment(equipment)
    setFormData({
      building_id: equipment.building_id,
      service_type_id: equipment.service_type_id,
      name: equipment.name,
      identifier: equipment.identifier || '',
      description: equipment.description || '',
      location: equipment.location || '',
      status: equipment.status,
      order: equipment.order || 0
    })
    setShowEquipmentForm(true)
  }

  const handleFormChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: name === 'building_id' || name === 'service_type_id' || name === 'order' 
        ? (value ? Number(value) : '') 
        : value
    }))
  }

  const handleSubmitEquipment = async (e) => {
    e.preventDefault()
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        toast.error('Session expirée. Veuillez vous reconnecter.')
        navigate('/login')
        return
      }

      const url = editingEquipment
        ? `${API_URL}/api/v1/admin/service-instances/${editingEquipment.id}`
        : `${API_URL}/api/v1/admin/service-instances`
      
      const method = editingEquipment ? 'PUT' : 'POST'
      
      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      })

      if (response.ok) {
        toast.success(editingEquipment ? 'Équipement mis à jour' : 'Équipement créé')
        setShowEquipmentForm(false)
        loadEquipments()
      } else if (response.status === 401 || response.status === 403) {
        // Token expiré ou invalide
        localStorage.removeItem('token')
        toast.error('Session expirée. Veuillez vous reconnecter.')
        navigate('/login')
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Erreur lors de la sauvegarde' }))
        toast.error(`Erreur: ${errorData.detail || 'Erreur lors de la sauvegarde'}`)
      }
    } catch (error) {
      console.error('Erreur sauvegarde équipement:', error)
      toast.error('Erreur de connexion. Vérifiez votre connexion internet.')
    }
  }

  const handleDeleteEquipment = async (equipmentId) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cet équipement ?')) {
      return
    }

    try {
      const token = localStorage.getItem('token')
      const response = await fetch(
        `${API_URL}/api/v1/admin/service-instances/${equipmentId}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (response.ok) {
        toast.success('Équipement supprimé')
        loadEquipments()
      } else {
        const error = await response.json()
        toast.error(`Erreur: ${error.detail || 'Erreur lors de la suppression'}`)
      }
    } catch (error) {
      console.error('Erreur suppression équipement:', error)
      toast.error('Erreur lors de la suppression')
    }
  }

  // ============ Gestion des Bâtiments ============

  const openCreateBuildingForm = () => {
    setEditingBuilding(null)
    setBuildingFormData({
      identifier: '',
      name: '',
      description: '',
      order: 0
    })
    setShowBuildingForm(true)
  }

  const openEditBuildingForm = (building) => {
    setEditingBuilding(building)
    setBuildingFormData({
      identifier: building.identifier,
      name: building.name || '',
      description: building.description || '',
      order: building.order || 0
    })
    setShowBuildingForm(true)
  }

  const handleBuildingFormChange = (e) => {
    const { name, value } = e.target
    setBuildingFormData(prev => ({
      ...prev,
      [name]: name === 'order' ? (value ? Number(value) : 0) : value
    }))
  }

  const handleSubmitBuilding = async (e) => {
    e.preventDefault()
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        toast.error('Session expirée. Veuillez vous reconnecter.')
        navigate('/login')
        return
      }

      const url = editingBuilding
        ? `${API_URL}/api/v1/admin/buildings/${editingBuilding.id}`
        : `${API_URL}/api/v1/admin/buildings`
      
      const method = editingBuilding ? 'PUT' : 'POST'
      
      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(buildingFormData)
      })

      if (response.ok) {
        toast.success(editingBuilding ? 'Bâtiment mis à jour' : 'Bâtiment créé')
        setShowBuildingForm(false)
        loadBuildings()
        if (activeTab === 'equipments') {
          loadEquipments() // Recharger pour mettre à jour les listes
        }
      } else if (response.status === 401) {
        // Token expiré ou invalide
        localStorage.removeItem('token')
        toast.error('Votre session a expiré. Veuillez vous reconnecter.')
        window.location.href = '/login'
        return
      } else if (response.status === 403) {
        toast.error('Accès refusé. Vous devez être administrateur.')
        return
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Erreur lors de la sauvegarde' }))
        toast.error(`Erreur: ${errorData.detail || 'Erreur lors de la sauvegarde'}`)
      }
    } catch (error) {
      console.error('Erreur sauvegarde bâtiment:', error)
      toast.error('Erreur de connexion. Vérifiez votre connexion internet.')
    }
  }

  // ============ Gestion de la Copropriété ============

  const openCreateCoproForm = () => {
    setEditingCopro(null)
    setCoproFormData({
      name: '',
      address: '',
      city: '',
      postal_code: '',
      country: 'France'
    })
    setShowCoproForm(true)
  }

  const openEditCoproForm = (coproData) => {
    setEditingCopro(coproData)
    setCoproFormData({
      name: coproData.name || '',
      address: coproData.address || '',
      city: coproData.city || '',
      postal_code: coproData.postal_code || '',
      country: coproData.country || 'France'
    })
    setShowCoproForm(true)
  }

  const handleCoproFormChange = (e) => {
    const { name, value } = e.target
    setCoproFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmitCopro = async (e) => {
    e.preventDefault()
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        toast.error('Session expirée. Veuillez vous reconnecter.')
        navigate('/login')
        return
      }

      const url = editingCopro
        ? `${API_URL}/api/v1/admin/copro/${editingCopro.id}`
        : `${API_URL}/api/v1/admin/copro`
      
      const method = editingCopro ? 'PUT' : 'POST'
      
      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(coproFormData)
      })

      if (response.ok) {
        toast.success(editingCopro ? 'Copropriété mise à jour' : 'Copropriété créée')
        setShowCoproForm(false)
        loadCopro()
      } else if (response.status === 401) {
        localStorage.removeItem('token')
        toast.error('Votre session a expiré. Veuillez vous reconnecter.')
        window.location.href = '/login'
        return
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Erreur lors de la sauvegarde' }))
        toast.error(`Erreur: ${errorData.detail || 'Erreur lors de la sauvegarde'}`)
      }
    } catch (error) {
      console.error('Erreur sauvegarde copropriété:', error)
      toast.error('Erreur de connexion. Vérifiez votre connexion internet.')
    }
  }

  const handleDeleteBuilding = async (buildingId) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce bâtiment ?')) {
      return
    }

    try {
      const token = localStorage.getItem('token')
      const response = await fetch(
        `${API_URL}/api/v1/admin/buildings/${buildingId}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (response.ok) {
        toast.success('Bâtiment supprimé')
        loadBuildings()
        if (activeTab === 'equipments') {
          loadEquipments()
        }
      } else {
        const error = await response.json()
        toast.error(`Erreur: ${error.detail || 'Erreur lors de la suppression'}`)
      }
    } catch (error) {
      console.error('Erreur suppression bâtiment:', error)
      toast.error('Erreur lors de la suppression')
    }
  }

  if (loading && equipments.length === 0 && tickets.length === 0) {
    return <div className="admin-loading">Chargement...</div>
  }

  return (
    <div className="admin-page">
      <div className="admin-header">
        <h1>Administration</h1>
      </div>

      <div className="admin-tabs">
        <button 
          className={activeTab === 'copro' ? 'active' : ''}
          onClick={() => setActiveTab('copro')}
        >
          Copropriété
        </button>
        <button 
          className={activeTab === 'equipments' ? 'active' : ''}
          onClick={() => setActiveTab('equipments')}
        >
          Équipements
        </button>
        <button 
          className={activeTab === 'buildings' ? 'active' : ''}
          onClick={() => setActiveTab('buildings')}
        >
          Bâtiments
        </button>
        <button 
          className={activeTab === 'tickets' ? 'active' : ''}
          onClick={() => setActiveTab('tickets')}
        >
          Tickets ({tickets.filter(t => t.status === 'pending').length})
        </button>
      </div>

      {activeTab === 'equipments' && (
        <div className="equipments-section">
          <div className="section-header">
            <h2>Gestion des Équipements</h2>
            <button onClick={openCreateForm} className="btn-create">
              + Créer un équipement
            </button>
          </div>

          {showEquipmentForm && (
            <div className="modal-overlay" onClick={() => setShowEquipmentForm(false)}>
              <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                  <h3>{editingEquipment ? 'Modifier l\'équipement' : 'Créer un équipement'}</h3>
                  <button className="btn-close" onClick={() => setShowEquipmentForm(false)}>×</button>
                </div>
                <form onSubmit={handleSubmitEquipment} className="equipment-form">
                  <div className="form-group">
                    <label>Bâtiment *</label>
                    <select
                      name="building_id"
                      value={formData.building_id}
                      onChange={handleFormChange}
                      required
                    >
                      <option value="">Sélectionner un bâtiment</option>
                      {buildings.map(building => (
                        <option key={building.id} value={building.id}>
                          {building.identifier} - {building.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Type de service *</label>
                    <select
                      name="service_type_id"
                      value={formData.service_type_id}
                      onChange={handleFormChange}
                      required
                    >
                      <option value="">Sélectionner un type</option>
                      {serviceTypes.map(st => (
                        <option key={st.id} value={st.id}>
                          {st.name} {st.category ? `(${st.category})` : ''}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Nom *</label>
                    <input
                      type="text"
                      name="name"
                      value={formData.name}
                      onChange={handleFormChange}
                      required
                      placeholder="Ex: Ascenseur - Bâtiment A"
                    />
                  </div>

                  <div className="form-group">
                    <label>Identifiant</label>
                    <input
                      type="text"
                      name="identifier"
                      value={formData.identifier}
                      onChange={handleFormChange}
                      placeholder="Ex: ASC-A-01"
                    />
                  </div>

                  <div className="form-group">
                    <label>Description</label>
                    <textarea
                      name="description"
                      value={formData.description}
                      onChange={handleFormChange}
                      rows="3"
                    />
                  </div>

                  <div className="form-group">
                    <label>Localisation</label>
                    <input
                      type="text"
                      name="location"
                      value={formData.location}
                      onChange={handleFormChange}
                      placeholder="Ex: Rez-de-chaussée"
                    />
                  </div>

                  <div className="form-group">
                    <label>Statut *</label>
                    <select
                      name="status"
                      value={formData.status}
                      onChange={handleFormChange}
                      required
                    >
                      <option value="operational">Opérationnel</option>
                      <option value="degraded">Dégradé</option>
                      <option value="partial_outage">Panne partielle</option>
                      <option value="major_outage">Panne majeure</option>
                      <option value="maintenance">Maintenance</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Ordre d'affichage</label>
                    <input
                      type="number"
                      name="order"
                      value={formData.order}
                      onChange={handleFormChange}
                      min="0"
                    />
                  </div>

                  <div className="form-actions">
                    <button type="button" onClick={() => setShowEquipmentForm(false)} className="btn-cancel">
                      Annuler
                    </button>
                    <button type="submit" className="btn-submit">
                      {editingEquipment ? 'Mettre à jour' : 'Créer'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          <div className="equipments-grid">
            {equipments.map(equipment => (
              <div key={equipment.id} className={`equipment-card ${getStatusClass(equipment.status)}`}>
                <div className="equipment-header">
                  <h3>{equipment.name}</h3>
                  <span className={`status-badge ${getStatusClass(equipment.status)}`}>
                    {getStatusLabel(equipment.status)}
                  </span>
                </div>
                <div className="equipment-info">
                  <p><strong>Bâtiment:</strong> {equipment.building_name}</p>
                  <p><strong>Type:</strong> {equipment.service_type_name}</p>
                  {equipment.location && <p><strong>Localisation:</strong> {equipment.location}</p>}
                </div>
                <div className="equipment-actions">
                  <div className="action-buttons">
                    <button
                      onClick={() => openEditForm(equipment)}
                      className="btn-edit"
                    >
                      ✏️ Modifier
                    </button>
                    <button
                      onClick={() => handleDeleteEquipment(equipment.id)}
                      className="btn-delete"
                    >
                      🗑️ Supprimer
                    </button>
                  </div>
                  <label>Changer le statut:</label>
                  <select
                    value={equipment.status}
                    onChange={(e) => updateEquipmentStatus(equipment.id, e.target.value)}
                  >
                    <option value="operational">Opérationnel</option>
                    <option value="degraded">Dégradé</option>
                    <option value="partial_outage">Panne partielle</option>
                    <option value="major_outage">Panne majeure</option>
                    <option value="maintenance">Maintenance</option>
                  </select>
                  <button
                    onClick={() => {
                      const title = prompt('Titre de l\'incident:')
                      const message = prompt('Description de l\'incident:')
                      if (title && message) {
                        createIncident(equipment.id, title, message)
                      }
                    }}
                    className="btn-create-incident"
                  >
                    Créer un incident
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'copro' && (
        <div className="copro-section">
          <div className="section-header">
            <h2>Gestion de la Copropriété</h2>
            {!copro && (
              <button onClick={openCreateCoproForm} className="btn-create">
                + Créer la copropriété
              </button>
            )}
          </div>

          {showCoproForm && (
            <div className="modal-overlay" onClick={() => setShowCoproForm(false)}>
              <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                  <h3>{editingCopro ? 'Modifier la copropriété' : 'Créer la copropriété'}</h3>
                  <button className="btn-close" onClick={() => setShowCoproForm(false)}>×</button>
                </div>
                <form onSubmit={handleSubmitCopro} className="equipment-form">
                  <div className="form-group">
                    <label>Nom de la copropriété *</label>
                    <input
                      type="text"
                      name="name"
                      value={coproFormData.name}
                      onChange={handleCoproFormChange}
                      required
                      placeholder="Ex: Résidence Les Jardins"
                    />
                  </div>

                  <div className="form-group">
                    <label>Adresse</label>
                    <input
                      type="text"
                      name="address"
                      value={coproFormData.address}
                      onChange={handleCoproFormChange}
                      placeholder="Ex: 123 Rue de la République"
                    />
                  </div>

                  <div className="form-group">
                    <label>Ville</label>
                    <input
                      type="text"
                      name="city"
                      value={coproFormData.city}
                      onChange={handleCoproFormChange}
                      placeholder="Ex: Paris"
                    />
                  </div>

                  <div className="form-group">
                    <label>Code postal</label>
                    <input
                      type="text"
                      name="postal_code"
                      value={coproFormData.postal_code}
                      onChange={handleCoproFormChange}
                      placeholder="Ex: 75001"
                    />
                  </div>

                  <div className="form-group">
                    <label>Pays</label>
                    <input
                      type="text"
                      name="country"
                      value={coproFormData.country}
                      onChange={handleCoproFormChange}
                      placeholder="Ex: France"
                    />
                  </div>

                  <div className="form-actions">
                    <button type="button" onClick={() => setShowCoproForm(false)} className="btn-cancel">
                      Annuler
                    </button>
                    <button type="submit" className="btn-submit">
                      {editingCopro ? 'Mettre à jour' : 'Créer'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {copro ? (
            <div className="copro-card">
              <div className="copro-header">
                <div>
                  <h3>{copro.name}</h3>
                  {copro.address && (
                    <p className="copro-address">
                      {copro.address}
                      {copro.postal_code && copro.city && `, ${copro.postal_code} ${copro.city}`}
                      {copro.country && `, ${copro.country}`}
                    </p>
                  )}
                </div>
                <button
                  onClick={() => openEditCoproForm(copro)}
                  className="btn-edit"
                >
                  ✏️ Modifier
                </button>
              </div>
              <div className="copro-info">
                <p><strong>Statut:</strong> {copro.is_active ? 'Active' : 'Inactive'}</p>
                {copro.created_at && (
                  <p><strong>Créée le:</strong> {new Date(copro.created_at).toLocaleDateString('fr-FR')}</p>
                )}
              </div>
            </div>
          ) : (
            <div className="copro-empty">
              <p>Aucune copropriété configurée. Créez-en une pour commencer.</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'buildings' && (
        <div className="buildings-section">
          <div className="section-header">
            <h2>Gestion des Bâtiments</h2>
            <button onClick={openCreateBuildingForm} className="btn-create">
              + Créer un bâtiment
            </button>
          </div>

          {showBuildingForm && (
            <div className="modal-overlay" onClick={() => setShowBuildingForm(false)}>
              <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                  <h3>{editingBuilding ? 'Modifier le bâtiment' : 'Créer un bâtiment'}</h3>
                  <button className="btn-close" onClick={() => setShowBuildingForm(false)}>×</button>
                </div>
                <form onSubmit={handleSubmitBuilding} className="equipment-form">
                  <div className="form-group">
                    <label>Identifiant * (A, B, 1, 2, etc.)</label>
                    <input
                      type="text"
                      name="identifier"
                      value={buildingFormData.identifier}
                      onChange={handleBuildingFormChange}
                      required
                      placeholder="Ex: A, B, 1, 2"
                    />
                  </div>

                  <div className="form-group">
                    <label>Nom</label>
                    <input
                      type="text"
                      name="name"
                      value={buildingFormData.name}
                      onChange={handleBuildingFormChange}
                      placeholder="Ex: Bâtiment Principal"
                    />
                  </div>

                  <div className="form-group">
                    <label>Description</label>
                    <textarea
                      name="description"
                      value={buildingFormData.description}
                      onChange={handleBuildingFormChange}
                      rows="3"
                    />
                  </div>

                  <div className="form-group">
                    <label>Ordre d'affichage</label>
                    <input
                      type="number"
                      name="order"
                      value={buildingFormData.order}
                      onChange={handleBuildingFormChange}
                      min="0"
                    />
                  </div>

                  <div className="form-actions">
                    <button type="button" onClick={() => setShowBuildingForm(false)} className="btn-cancel">
                      Annuler
                    </button>
                    <button type="submit" className="btn-submit">
                      {editingBuilding ? 'Mettre à jour' : 'Créer'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          <div className="buildings-list">
            {buildings.map(building => (
              <div key={building.id} className="building-card">
                <div className="building-header">
                  <div>
                    <h3>{building.identifier} {building.name && `- ${building.name}`}</h3>
                    {building.description && (
                      <p className="building-description">{building.description}</p>
                    )}
                  </div>
                  <div className="building-actions">
                    <button
                      onClick={() => openEditBuildingForm(building)}
                      className="btn-edit"
                    >
                      ✏️ Modifier
                    </button>
                    <button
                      onClick={() => handleDeleteBuilding(building.id)}
                      className="btn-delete"
                    >
                      🗑️ Supprimer
                    </button>
                  </div>
                </div>
                <div className="building-info">
                  <p><strong>Ordre:</strong> {building.order}</p>
                  <p><strong>Statut:</strong> {building.is_active ? 'Actif' : 'Inactif'}</p>
                </div>
              </div>
            ))}
            {buildings.length === 0 && <p>Aucun bâtiment configuré</p>}
          </div>
        </div>
      )}

      {activeTab === 'tickets' && (
        <div className="tickets-section">
          <h2>Gestion des Tickets</h2>
          <div className="tickets-list">
            {tickets.map(ticket => (
              <div key={ticket.id} className={`ticket-card ticket-${ticket.status}`}>
                <div className="ticket-header">
                  <h3>{ticket.title}</h3>
                  <span className={`ticket-status ticket-${ticket.status}`}>
                    {ticket.status === 'pending' && 'En attente'}
                    {ticket.status === 'reviewing' && 'En analyse'}
                    {ticket.status === 'approved' && 'Approuvé'}
                    {ticket.status === 'rejected' && 'Rejeté'}
                    {ticket.status === 'resolved' && 'Résolu'}
                  </span>
                </div>
                <div className="ticket-body">
                  <p><strong>Description:</strong> {ticket.description}</p>
                  {ticket.reporter_name && <p><strong>Déclarant:</strong> {ticket.reporter_name}</p>}
                  {ticket.reporter_email && <p><strong>Email:</strong> {ticket.reporter_email}</p>}
                  {ticket.service_instance && <p><strong>Équipement:</strong> {ticket.service_instance}</p>}
                  <p><strong>Date:</strong> {new Date(ticket.created_at).toLocaleString('fr-FR')}</p>
                </div>
                {ticket.status === 'pending' && (
                  <div className="ticket-actions">
                    <button
                      onClick={() => {
                        const notes = prompt('Notes (optionnel):')
                        reviewTicket(ticket.id, 'approved', true, notes)
                      }}
                      className="btn-approve"
                    >
                      Approuver et créer incident
                    </button>
                    <button
                      onClick={() => {
                        const notes = prompt('Raison du rejet:')
                        if (notes) {
                          reviewTicket(ticket.id, 'rejected', false, notes)
                        }
                      }}
                      className="btn-reject"
                    >
                      Rejeter
                    </button>
                  </div>
                )}
              </div>
            ))}
            {tickets.length === 0 && <p>Aucun ticket</p>}
          </div>
        </div>
      )}
    </div>
  )
}

export default Admin

