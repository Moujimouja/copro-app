import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import './Admin.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function Admin() {
  const [equipments, setEquipments] = useState([])
  const [tickets, setTickets] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('equipments')
  const navigate = useNavigate()

  useEffect(() => {
    // Vérifier l'authentification
    const token = localStorage.getItem('token')
    if (!token) {
      navigate('/login')
      return
    }

    if (activeTab === 'equipments') {
      loadEquipments()
    } else if (activeTab === 'tickets') {
      loadTickets()
    }
  }, [activeTab, navigate])

  const loadEquipments = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
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
      } else if (response.status === 403) {
        alert('Accès refusé. Vous devez être administrateur.')
        navigate('/')
      }
    } catch (error) {
      console.error('Erreur chargement équipements:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadTickets = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
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
      }
    } catch (error) {
      console.error('Erreur chargement tickets:', error)
    } finally {
      setLoading(false)
    }
  }

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
        loadEquipments()
      } else {
        alert('Erreur lors de la mise à jour du statut')
      }
    } catch (error) {
      console.error('Erreur mise à jour statut:', error)
      alert('Erreur lors de la mise à jour du statut')
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
        alert('Incident créé avec succès')
        loadEquipments()
      } else {
        alert('Erreur lors de la création de l\'incident')
      }
    } catch (error) {
      console.error('Erreur création incident:', error)
      alert('Erreur lors de la création de l\'incident')
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
        alert('Ticket traité avec succès')
        loadTickets()
      } else {
        alert('Erreur lors du traitement du ticket')
      }
    } catch (error) {
      console.error('Erreur traitement ticket:', error)
      alert('Erreur lors du traitement du ticket')
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
          className={activeTab === 'equipments' ? 'active' : ''}
          onClick={() => setActiveTab('equipments')}
        >
          Équipements
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
          <h2>Gestion des Équipements</h2>
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

