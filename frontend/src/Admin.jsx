import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import './Admin.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function Admin() {
  const [equipments, setEquipments] = useState([])
  const [tickets, setTickets] = useState([])
  const [incidents, setIncidents] = useState([])
  const [admins, setAdmins] = useState([])
  const [buildings, setBuildings] = useState([])
  const [serviceTypes, setServiceTypes] = useState([])
  const [copro, setCopro] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('copro')
  const [selectedTicket, setSelectedTicket] = useState(null)
  const [selectedIncident, setSelectedIncident] = useState(null)
  const [showCommentForm, setShowCommentForm] = useState(false)
  const [newComment, setNewComment] = useState('')
  const [showIncidentForm, setShowIncidentForm] = useState(false)
  const [selectedEquipmentForIncident, setSelectedEquipmentForIncident] = useState(null)
  const [incidentFormData, setIncidentFormData] = useState({
    title: '',
    message: ''
  })
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
      loadAdmins()
    } else if (activeTab === 'incidents') {
      loadIncidents()
      loadAdmins()
    }
  }, [activeTab, loadEquipments, loadBuildings, loadServiceTypes, loadTickets, loadCopro, navigate])

  const loadAdmins = useCallback(async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        return
      }

      const response = await fetch(`${API_URL}/api/v1/admin/admins`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setAdmins(data)
      }
    } catch (error) {
      console.error('Erreur chargement admins:', error)
    }
  }, [])

  const loadIncidents = useCallback(async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      if (!token) {
        return
      }

      const response = await fetch(`${API_URL}/api/v1/admin/incidents`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setIncidents(data)
      } else if (response.status === 401) {
        localStorage.removeItem('token')
        window.location.href = '/login'
        return
      }
    } catch (error) {
      console.error('Erreur chargement incidents:', error)
    } finally {
      setLoading(false)
    }
  }, [])

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

  const openIncidentForm = (equipment) => {
    setSelectedEquipmentForIncident(equipment)
    setIncidentFormData({
      title: '',
      message: ''
    })
    setShowIncidentForm(true)
  }

  const handleIncidentFormChange = (e) => {
    const { name, value } = e.target
    setIncidentFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmitIncident = async (e) => {
    e.preventDefault()
    if (!selectedEquipmentForIncident) return

    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`${API_URL}/api/v1/admin/incidents`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          service_instance_id: selectedEquipmentForIncident.id,
          title: incidentFormData.title,
          message: incidentFormData.message,
          status: 'investigating'
        })
      })
      if (response.ok) {
        toast.success('Incident créé avec succès')
        setShowIncidentForm(false)
        setSelectedEquipmentForIncident(null)
        setIncidentFormData({ title: '', message: '' })
        loadEquipments()
        loadIncidents()
      } else {
        const error = await response.json().catch(() => ({ detail: 'Erreur lors de la création de l\'incident' }))
        toast.error(`Erreur: ${error.detail || 'Erreur lors de la création de l\'incident'}`)
      }
    } catch (error) {
      console.error('Erreur création incident:', error)
      toast.error('Erreur lors de la création de l\'incident')
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

  const assignTicket = async (ticketId, adminId) => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(
        `${API_URL}/api/v1/admin/tickets/${ticketId}/assign`,
        {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ assigned_to: adminId })
        }
      )
      if (response.ok) {
        toast.success('Ticket assigné avec succès')
        loadTickets()
      } else {
        const error = await response.json()
        toast.error(`Erreur: ${error.detail || 'Erreur lors de l\'assignation'}`)
      }
    } catch (error) {
      console.error('Erreur assignation ticket:', error)
      toast.error('Erreur lors de l\'assignation')
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
        if (createIncident) {
          loadIncidents()
        }
      } else {
        const error = await response.json()
        toast.error(`Erreur: ${error.detail || 'Erreur lors du traitement du ticket'}`)
      }
    } catch (error) {
      console.error('Erreur traitement ticket:', error)
      toast.error('Erreur lors du traitement du ticket')
    }
  }

  const rejectTicket = async (ticketId, notes) => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(
        `${API_URL}/api/v1/admin/tickets/${ticketId}/reject`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ admin_notes: notes || '' })
        }
      )
      if (response.ok) {
        toast.success('Ticket rejeté')
        loadTickets()
      } else {
        const error = await response.json()
        toast.error(`Erreur: ${error.detail || 'Erreur lors du rejet'}`)
      }
    } catch (error) {
      console.error('Erreur rejet ticket:', error)
      toast.error('Erreur lors du rejet')
    }
  }

  const updateIncidentStatus = async (incidentId, newStatus) => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(
        `${API_URL}/api/v1/admin/incidents/${incidentId}/status`,
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
        toast.success('Statut de l\'incident mis à jour')
        loadIncidents()
        if (selectedIncident && selectedIncident.id === incidentId) {
          loadIncidentDetails(incidentId)
        }
      } else {
        const error = await response.json()
        toast.error(`Erreur: ${error.detail || 'Erreur lors de la mise à jour'}`)
      }
    } catch (error) {
      console.error('Erreur mise à jour statut incident:', error)
      toast.error('Erreur lors de la mise à jour')
    }
  }

  const loadIncidentDetails = async (incidentId) => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(
        `${API_URL}/api/v1/admin/incidents/${incidentId}`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      )
      if (response.ok) {
        const data = await response.json()
        setSelectedIncident(data)
      }
    } catch (error) {
      console.error('Erreur chargement détails incident:', error)
    }
  }

  const addIncidentComment = async (incidentId, comment) => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(
        `${API_URL}/api/v1/admin/incidents/${incidentId}/comments`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ comment })
        }
      )
      if (response.ok) {
        toast.success('Commentaire ajouté')
        setNewComment('')
        setShowCommentForm(false)
        loadIncidentDetails(incidentId)
        loadIncidents()
      } else {
        const error = await response.json()
        toast.error(`Erreur: ${error.detail || 'Erreur lors de l\'ajout du commentaire'}`)
      }
    } catch (error) {
      console.error('Erreur ajout commentaire:', error)
      toast.error('Erreur lors de l\'ajout du commentaire')
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
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer cet équipement ?')) {
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
        <button 
          className={activeTab === 'incidents' ? 'active' : ''}
          onClick={() => setActiveTab('incidents')}
        >
          Incidents ({incidents.filter(i => i.status !== 'closed').length})
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

          <div className="equipments-table-container">
            <table className="equipments-table">
              <thead>
                <tr>
                  <th>Nom</th>
                  <th>Bâtiment</th>
                  <th>Type</th>
                  <th>Localisation</th>
                  <th>Statut</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {equipments.map(equipment => (
                  <tr key={equipment.id} className={`equipment-row ${getStatusClass(equipment.status)}`}>
                    <td className="equipment-name">{equipment.name}</td>
                    <td>{equipment.building_name}</td>
                    <td>{equipment.service_type_name}</td>
                    <td>{equipment.location || '-'}</td>
                    <td>
                      <select
                        value={equipment.status}
                        onChange={(e) => updateEquipmentStatus(equipment.id, e.target.value)}
                        className="status-select"
                      >
                        <option value="operational">Opérationnel</option>
                        <option value="degraded">Dégradé</option>
                        <option value="partial_outage">Panne partielle</option>
                        <option value="major_outage">Panne majeure</option>
                        <option value="maintenance">Maintenance</option>
                      </select>
                    </td>
                    <td className="equipment-actions-cell">
                      <div className="action-icons">
                        <button
                          onClick={() => openEditForm(equipment)}
                          className="icon-btn icon-btn-edit"
                          title="Modifier"
                        >
                          ✏️
                        </button>
                        <button
                          onClick={() => {
                            if (window.confirm(`Êtes-vous sûr de vouloir supprimer l'équipement "${equipment.name}" ?`)) {
                              handleDeleteEquipment(equipment.id)
                            }
                          }}
                          className="icon-btn icon-btn-delete"
                          title="Supprimer"
                        >
                          🗑️
                        </button>
                        <button
                          onClick={() => openIncidentForm(equipment)}
                          className="icon-btn icon-btn-incident"
                          title="Créer un incident"
                        >
                          ⚠️
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {equipments.length === 0 && (
            <p className="no-equipments">Aucun équipement configuré</p>
          )}

          {showIncidentForm && selectedEquipmentForIncident && (
            <div className="modal-overlay" onClick={() => setShowIncidentForm(false)}>
              <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                  <h3>Créer un incident</h3>
                  <button className="btn-close" onClick={() => setShowIncidentForm(false)}>×</button>
                </div>
                <form onSubmit={handleSubmitIncident} className="incident-form">
                  <div className="form-group">
                    <label>Équipement</label>
                    <input
                      type="text"
                      value={selectedEquipmentForIncident.name}
                      disabled
                      className="form-input-disabled"
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor="incident-title">Titre de l'incident *</label>
                    <input
                      type="text"
                      id="incident-title"
                      name="title"
                      value={incidentFormData.title}
                      onChange={handleIncidentFormChange}
                      required
                      placeholder="Ex: Panne de l'ascenseur"
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor="incident-message">Description *</label>
                    <textarea
                      id="incident-message"
                      name="message"
                      value={incidentFormData.message}
                      onChange={handleIncidentFormChange}
                      required
                      rows="5"
                      placeholder="Décrivez le problème en détail..."
                    />
                  </div>
                  <div className="form-actions">
                    <button type="button" onClick={() => setShowIncidentForm(false)} className="btn-cancel">
                      Annuler
                    </button>
                    <button type="submit" className="btn-submit">
                      Créer l'incident
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
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
                  {ticket.reporter_phone && <p><strong>Téléphone:</strong> {ticket.reporter_phone}</p>}
                  {ticket.location && <p><strong>Localisation:</strong> {ticket.location}</p>}
                  {ticket.service_instance && <p><strong>Équipement:</strong> {ticket.service_instance}</p>}
                  {ticket.assigned_admin && <p><strong>Assigné à:</strong> {ticket.assigned_admin}</p>}
                  {ticket.admin_notes && <p><strong>Notes admin:</strong> {ticket.admin_notes}</p>}
                  {ticket.incident_id && <p><strong>Incident créé:</strong> #{ticket.incident_id}</p>}
                  <p><strong>Date:</strong> {new Date(ticket.created_at).toLocaleString('fr-FR')}</p>
                  {ticket.reviewed_at && <p><strong>Traité le:</strong> {new Date(ticket.reviewed_at).toLocaleString('fr-FR')}</p>}
                </div>
                <div className="ticket-actions">
                  {ticket.status === 'pending' && (
                    <>
                      <select
                        onChange={(e) => {
                          if (e.target.value) {
                            assignTicket(ticket.id, parseInt(e.target.value))
                          }
                        }}
                        defaultValue=""
                        className="select-assign"
                      >
                        <option value="">Assigner à...</option>
                        {admins.map(admin => (
                          <option key={admin.id} value={admin.id}>{admin.username}</option>
                        ))}
                      </select>
                      <button
                        onClick={() => {
                          const notes = window.prompt('Notes (optionnel):') || ''
                          reviewTicket(ticket.id, 'approved', true, notes)
                        }}
                        className="btn-approve"
                      >
                        Approuver et créer incident
                      </button>
                      <button
                        onClick={() => {
                          const notes = window.prompt('Raison du rejet:') || ''
                          rejectTicket(ticket.id, notes)
                        }}
                        className="btn-reject"
                      >
                        Rejeter
                      </button>
                    </>
                  )}
                  {(ticket.status === 'reviewing' || ticket.status === 'approved') && (
                    <>
                      <button
                        onClick={() => {
                          const notes = window.prompt('Notes (optionnel):') || ''
                          reviewTicket(ticket.id, 'approved', true, notes)
                        }}
                        className="btn-approve"
                      >
                        Approuver et créer incident
                      </button>
                      <button
                        onClick={() => {
                          const notes = window.prompt('Raison du rejet:') || ''
                          rejectTicket(ticket.id, notes)
                        }}
                        className="btn-reject"
                      >
                        Rejeter
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))}
            {tickets.length === 0 && <p>Aucun ticket</p>}
          </div>
        </div>
      )}

      {activeTab === 'incidents' && (
        <div className="incidents-section">
          <h2>Gestion des Incidents</h2>
          <div className="incidents-list">
            {incidents.map(incident => (
              <div 
                key={incident.id} 
                className={`incident-card incident-${incident.status}`}
                onClick={() => {
                  setSelectedIncident(null)
                  loadIncidentDetails(incident.id)
                }}
              >
                <div className="incident-header">
                  <h3>{incident.title}</h3>
                  <select
                    value={incident.status}
                    onChange={(e) => {
                      e.stopPropagation()
                      updateIncidentStatus(incident.id, e.target.value)
                    }}
                    onClick={(e) => e.stopPropagation()}
                    className={`incident-status-select incident-status-${incident.status}`}
                  >
                    <option value="investigating">En cours d'analyse</option>
                    <option value="in_progress">En cours de traitement</option>
                    <option value="resolved">Résolu</option>
                    <option value="closed">Clos</option>
                  </select>
                </div>
                <div className="incident-body">
                  <p><strong>Description:</strong> {incident.message}</p>
                  {incident.service_instance && <p><strong>Équipement:</strong> {incident.service_instance}</p>}
                  <p><strong>Créé le:</strong> {new Date(incident.created_at).toLocaleString('fr-FR')}</p>
                  {incident.resolved_at && <p><strong>Résolu le:</strong> {new Date(incident.resolved_at).toLocaleString('fr-FR')}</p>}
                </div>
                <div className="incident-actions">
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      setSelectedIncident(null)
                      loadIncidentDetails(incident.id)
                    }}
                    className="btn-view"
                  >
                    Voir détails
                  </button>
                </div>
              </div>
            ))}
            {incidents.length === 0 && <p>Aucun incident</p>}
          </div>

          {selectedIncident && (
            <div className="modal-overlay" onClick={() => setSelectedIncident(null)}>
              <div className="modal-content modal-large" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                  <h3>Détails de l'incident: {selectedIncident.title}</h3>
                  <button className="btn-close" onClick={() => setSelectedIncident(null)}>×</button>
                </div>
                <div className="incident-details">
                  <div className="incident-info">
                    <div className="incident-info-row">
                      <label><strong>Statut:</strong></label>
                      <select
                        value={selectedIncident.status}
                        onChange={(e) => updateIncidentStatus(selectedIncident.id, e.target.value)}
                        className={`incident-status-select incident-status-${selectedIncident.status}`}
                      >
                        <option value="investigating">En cours d'analyse</option>
                        <option value="in_progress">En cours de traitement</option>
                        <option value="resolved">Résolu</option>
                        <option value="closed">Clos</option>
                      </select>
                    </div>
                    <p><strong>Description:</strong> {selectedIncident.message}</p>
                    {selectedIncident.service_instance && <p><strong>Équipement:</strong> {selectedIncident.service_instance}</p>}
                    <p><strong>Créé le:</strong> {new Date(selectedIncident.created_at).toLocaleString('fr-FR')}</p>
                    {selectedIncident.resolved_at && <p><strong>Résolu le:</strong> {new Date(selectedIncident.resolved_at).toLocaleString('fr-FR')}</p>}
                  </div>


                  <div className="comments-section">
                    <h4>Commentaires</h4>
                    <div className="comments-list">
                      {selectedIncident.comments && selectedIncident.comments.length > 0 ? (
                        selectedIncident.comments.map(comment => (
                          <div key={comment.id} className="comment-item">
                            <div className="comment-header">
                              <strong>{comment.admin_username}</strong>
                              <span className="comment-date">
                                {new Date(comment.created_at).toLocaleString('fr-FR')}
                              </span>
                            </div>
                            <div className="comment-body">{comment.comment}</div>
                          </div>
                        ))
                      ) : (
                        <p className="no-comments">Aucun commentaire</p>
                      )}
                    </div>
                    {!showCommentForm ? (
                      <button
                        onClick={() => setShowCommentForm(true)}
                        className="btn-add-comment"
                      >
                        + Ajouter un commentaire
                      </button>
                    ) : (
                      <div className="comment-form">
                        <textarea
                          value={newComment}
                          onChange={(e) => setNewComment(e.target.value)}
                          placeholder="Votre commentaire..."
                          rows="4"
                        />
                        <div className="comment-form-actions">
                          <button
                            onClick={() => {
                              setNewComment('')
                              setShowCommentForm(false)
                            }}
                            className="btn-cancel"
                          >
                            Annuler
                          </button>
                          <button
                            onClick={() => {
                              if (newComment.trim()) {
                                addIncidentComment(selectedIncident.id, newComment)
                              }
                            }}
                            className="btn-submit"
                            disabled={!newComment.trim()}
                          >
                            Envoyer
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default Admin

