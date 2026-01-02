import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import './Status.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function Status() {
  const [statusData, setStatusData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [isAdmin, setIsAdmin] = useState(false)
  const [expandedBuildings, setExpandedBuildings] = useState({})

  useEffect(() => {
    // Vérifier si l'utilisateur est admin
    const token = localStorage.getItem('token')
    setIsAdmin(!!token)
    
    fetchStatus()
    // Refresh every 30 seconds
    const interval = setInterval(fetchStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  // Initialiser les sections expandées quand les données sont chargées
  useEffect(() => {
    if (statusData && statusData.services) {
      // Grouper les services par bâtiment
      const groupedByBuilding = {}
      statusData.services.forEach(service => {
        const buildingKey = service.building_name || 'Commun'
        if (!groupedByBuilding[buildingKey]) {
          groupedByBuilding[buildingKey] = []
        }
        groupedByBuilding[buildingKey].push(service)
      })
      
      // Initialiser l'état d'expansion : collapsed si tous les services sont opérationnels
      const initialExpanded = {}
      Object.keys(groupedByBuilding).forEach(building => {
        const services = groupedByBuilding[building]
        // Vérifier si tous les services sont opérationnels
        const allOperational = services.every(s => s.status === 'operational')
        // Si tous sont opérationnels, le bâtiment est collapsed (false), sinon expanded (true)
        initialExpanded[building] = !allOperational
      })
      setExpandedBuildings(initialExpanded)
    }
  }, [statusData])

  const fetchStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/status/status`)
      if (!response.ok) throw new Error('Failed to fetch status')
      const data = await response.json()
      setStatusData(data)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const getStatusClass = (status) => {
    const statusMap = {
      operational: 'status-operational',
      degraded: 'status-degraded',
      partial_outage: 'status-partial',
      major_outage: 'status-major',
      maintenance: 'status-maintenance',
      investigating: 'incident-investigating',
      in_progress: 'incident-in_progress',
      resolved: 'incident-resolved',
      closed: 'incident-closed',
      scheduled: 'incident-scheduled'
    }
    return statusMap[status] || 'status-unknown'
  }

  const getStatusLabel = (status) => {
    const labelMap = {
      operational: 'Opérationnel',
      degraded: 'Performance dégradée',
      partial_outage: 'Panne partielle',
      major_outage: 'Panne majeure',
      maintenance: 'En maintenance',
      investigating: 'En cours d\'analyse',
      in_progress: 'En cours de traitement',
      resolved: 'Résolu',
      closed: 'Clos',
      scheduled: 'Planifié'
    }
    return labelMap[status] || status
  }

  const formatDate = (dateString) => {
    if (!dateString) return ''
    const date = new Date(dateString)
    return date.toLocaleString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const updateServiceStatus = async (serviceId, newStatus) => {
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        toast.error('Vous devez être connecté pour modifier le statut')
        return
      }

      const response = await fetch(`${API_URL}/api/v1/admin/service-instances/${serviceId}/status`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: newStatus })
      })

      if (response.ok) {
        toast.success('Statut mis à jour')
        // Recharger les données
        fetchStatus()
      } else if (response.status === 401 || response.status === 403) {
        toast.error('Accès refusé. Vous devez être administrateur.')
        setIsAdmin(false)
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Erreur lors de la mise à jour' }))
        toast.error(`Erreur: ${errorData.detail || 'Erreur lors de la mise à jour'}`)
      }
    } catch (error) {
      console.error('Erreur mise à jour statut:', error)
      toast.error('Erreur de connexion')
    }
  }

  const statusOptions = [
    { value: 'operational', label: 'Opérationnel', color: '#10b981' },
    { value: 'degraded', label: 'Dégradé', color: '#f59e0b' },
    { value: 'partial_outage', label: 'Panne partielle', color: '#f97316' },
    { value: 'major_outage', label: 'Panne majeure', color: '#ef4444' },
    { value: 'maintenance', label: 'Maintenance', color: '#6366f1' }
  ]

  // Ordre de priorité des statuts pour le tri (du plus critique au moins critique)
  const statusPriority = {
    'major_outage': 1,
    'partial_outage': 2,
    'degraded': 3,
    'maintenance': 4,
    'operational': 5
  }

  const toggleBuilding = (buildingName) => {
    setExpandedBuildings(prev => ({
      ...prev,
      [buildingName]: !prev[buildingName]
    }))
  }

  if (loading) {
    return (
      <div className="status-page">
        <div className="status-loading">Chargement du statut...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="status-page">
        <div className="status-error">Erreur: {error}</div>
      </div>
    )
  }

  if (!statusData) {
    return (
      <div className="status-page">
        <div className="status-error">Aucune donnée disponible</div>
      </div>
    )
  }

  return (
    <div className="status-page">
      <div className="status-header">
        <h1>Statut des équipements et services de la copropriété</h1>
        {statusData.copro && (
          <div className="copro-info">
            <div className="copro-info-content">
              <div className="copro-image-container">
                <img 
                  src="https://images.squarespace-cdn.com/content/v1/63dd345d04b310097e0bafcf/08d1a6eb-d0f7-4dde-a0a9-b8463c5b1eb0/4+bis+rue+Fabre+d%27E%CC%81glantine+75012+Paris+-+Maison+Cotard+-+3.jpg?format=1500w" 
                  alt={`Photo de ${statusData.copro.name}`}
                  className="copro-map-image"
                  onError={(e) => {
                    // Fallback vers une image placeholder si l'image ne charge pas
                    e.target.src = 'https://via.placeholder.com/200x200/3498db/ffffff?text=📍'
                  }}
                />
              </div>
              <div className="copro-text-content">
                <h3>{statusData.copro.name}</h3>
                {(statusData.copro.address || statusData.copro.city || statusData.copro.postal_code) && (
                  <p className="copro-address">
                    {statusData.copro.address && <span>{statusData.copro.address}</span>}
                    {statusData.copro.address && (statusData.copro.city || statusData.copro.postal_code) && <span>, </span>}
                    {statusData.copro.postal_code && <span>{statusData.copro.postal_code}</span>}
                    {statusData.copro.postal_code && statusData.copro.city && <span> </span>}
                    {statusData.copro.city && <span>{statusData.copro.city}</span>}
                    {statusData.copro.country && (statusData.copro.city || statusData.copro.postal_code || statusData.copro.address) && <span>, </span>}
                    {statusData.copro.country && <span>{statusData.copro.country}</span>}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
        <div className={`overall-status ${getStatusClass(statusData.overall_status)}`}>
          <span className="status-indicator"></span>
          <span className="status-text">{getStatusLabel(statusData.overall_status)}</span>
        </div>
      </div>

      <div className="status-content">
        <section className="services-section">
          <h2>Services</h2>
          {(() => {
            // Grouper les services par bâtiment
            const groupedByBuilding = {}
            
            statusData.services.forEach(service => {
              const buildingKey = service.building_name || 'Commun'
              
              if (!groupedByBuilding[buildingKey]) {
                groupedByBuilding[buildingKey] = []
              }
              groupedByBuilding[buildingKey].push(service)
            })
            
            if (statusData.services.length === 0) {
              return <p className="no-services">Aucun service configuré</p>
            }
            
            // Trier les bâtiments par le statut le plus critique
            const sortedBuildings = Object.entries(groupedByBuilding).sort(([nameA, servicesA], [nameB, servicesB]) => {
              const minPriorityA = Math.min(...servicesA.map(s => statusPriority[s.status] || 99))
              const minPriorityB = Math.min(...servicesB.map(s => statusPriority[s.status] || 99))
              if (minPriorityA !== minPriorityB) {
                return minPriorityA - minPriorityB
              }
              return nameA.localeCompare(nameB)
            })
            
            return (
              <div className="buildings-list-collapsable">
                {sortedBuildings.map(([buildingName, services]) => {
                  // Trier les services par statut (priorité) puis par nom
                  const sortedServices = [...services].sort((a, b) => {
                    const priorityA = statusPriority[a.status] || 99
                    const priorityB = statusPriority[b.status] || 99
                    if (priorityA !== priorityB) {
                      return priorityA - priorityB
                    }
                    return a.name.localeCompare(b.name)
                  })
                  
                  const isExpanded = expandedBuildings[buildingName] !== false // Par défaut expanded
                  const hasIssues = services.some(s => s.status !== 'operational')
                  const worstStatus = sortedServices[0]?.status || 'operational'
                  
                  return (
                    <div key={buildingName} className="building-collapsable">
                      <button 
                        className={`building-collapsable-header ${getStatusClass(worstStatus)}`}
                        onClick={() => toggleBuilding(buildingName)}
                      >
                        <span className="building-collapsable-title">
                          <span className="status-indicator"></span>
                          <span className="building-name">{buildingName}</span>
                          <span className="building-count">({services.length})</span>
                        </span>
                        <span className="building-collapsable-icon">
                          {isExpanded ? '▼' : '▶'}
                        </span>
                      </button>
                      {isExpanded && (
                        <div className="building-collapsable-content">
                          {sortedServices.map((service) => (
                            <div 
                              key={service.id} 
                              className={`service-item-list ${getStatusClass(service.status)}`}
                            >
                              <div className="service-item-content">
                                <span className="service-status-indicator"></span>
                                <span className="service-name">{service.name}</span>
                                {service.description && (
                                  <span className="service-description"> • {service.description}</span>
                                )}
                                <span className="service-status-badge">{getStatusLabel(service.status)}</span>
                              </div>
                              {isAdmin && (
                                <select
                                  className="service-status-dropdown"
                                  value={service.status}
                                  onChange={(e) => updateServiceStatus(service.id, e.target.value)}
                                  style={{
                                    borderColor: statusOptions.find(opt => opt.value === service.status)?.color || '#e5e7eb'
                                  }}
                                >
                                  {statusOptions.map((option) => (
                                    <option key={option.value} value={option.value}>
                                      {option.label}
                                    </option>
                                  ))}
                                </select>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )
          })()}
        </section>

        <section className="incidents-section">
          <h2>Événements en Cours</h2>
          {(() => {
            // Combiner incidents actifs et maintenances actives
            const now = new Date()
            const activeIncidents = statusData.incidents.filter(i => i.status !== 'closed' && i.status !== 'resolved')
            const activeMaintenances = (statusData.maintenances || []).filter(m => {
              const startDate = new Date(m.start_date)
              const endDate = new Date(m.end_date)
              return now >= startDate && now <= endDate
            })
            
            // Créer une liste combinée avec un type pour distinguer
            const activeEvents = [
              ...activeIncidents.map(i => ({ ...i, eventType: 'incident' })),
              ...activeMaintenances.map(m => ({ ...m, eventType: 'maintenance' }))
            ].sort((a, b) => {
              const dateA = new Date(a.created_at || a.start_date)
              const dateB = new Date(b.created_at || b.start_date)
              return dateB - dateA
            })
            
            return activeEvents.length > 0 ? (
              <div className="incidents-list">
                {activeEvents.map((event) => {
                  if (event.eventType === 'maintenance') {
                    return (
                      <div key={`maintenance-${event.id}`} className="incident-item maintenance-item">
                        <div className="incident-header">
                          <span className="incident-status maintenance-badge">🔧 Maintenance</span>
                          <span className="incident-date">
                            {new Date(event.start_date).toLocaleString('fr-FR')} - {new Date(event.end_date).toLocaleString('fr-FR')}
                          </span>
                        </div>
                        <h3 className="incident-title">{event.title}</h3>
                        {event.description && (
                          <p className="incident-message">{event.description}</p>
                        )}
                        {event.service_instance_ids && event.service_instance_ids.length > 0 && (
                          <p className="incident-equipment">
                            Équipements concernés: {event.service_instance_ids.length} équipement(s)
                          </p>
                        )}
                      </div>
                    )
                  } else {
                    return (
                      <div key={`incident-${event.id}`} className={`incident-card ${getStatusClass(event.status)}`}>
                        <div className="incident-header">
                          <h3>{event.title}</h3>
                          <span className={`incident-status ${getStatusClass(event.status)}`}>
                            {getStatusLabel(event.status)}
                          </span>
                        </div>
                        {event.message && (
                          <p className="incident-message">{event.message}</p>
                        )}
                        <div className="incident-meta">
                          <span>Créé le {formatDate(event.created_at)}</span>
                        </div>
                        {event.updates && event.updates.length > 0 && (
                          <div className="incident-updates">
                            <h4>Mises à jour:</h4>
                            {event.updates.map((update) => (
                              <div key={update.id} className="incident-update">
                                <span className="update-time">{formatDate(update.created_at)}</span>
                                <p>{update.message}</p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )
                  }
                })}
              </div>
            ) : (
              <p className="no-incidents">Aucun incident en cours. Tous les systèmes fonctionnent normalement.</p>
            )
          })()}
        </section>

        <section className="incidents-section incidents-past">
          <h2>Historique</h2>
          {(() => {
            // Combiner incidents passés et maintenances passées
            const now = new Date()
            const pastIncidents = statusData.incidents.filter(i => i.status === 'closed' || i.status === 'resolved')
            const pastMaintenances = (statusData.maintenances || []).filter(m => {
              const endDate = new Date(m.end_date)
              return now > endDate
            })
            
            // Créer une liste combinée triée par date
            const pastEvents = [
              ...pastIncidents.map(i => ({ ...i, eventType: 'incident' })),
              ...pastMaintenances.map(m => ({ ...m, eventType: 'maintenance' }))
            ].sort((a, b) => {
              const dateA = new Date(a.resolved_at || a.updated_at || a.created_at || a.end_date)
              const dateB = new Date(b.resolved_at || b.updated_at || b.created_at || b.end_date)
              return dateB - dateA
            })
            
            return pastEvents.length > 0 ? (
              <div className="incidents-list">
                {pastEvents.map((event) => {
                  if (event.eventType === 'maintenance') {
                    return (
                      <div key={`maintenance-${event.id}`} className="incident-item maintenance-item past">
                        <div className="incident-header">
                          <span className="incident-status maintenance-badge">🔧 Maintenance</span>
                          <span className="incident-date">
                            {new Date(event.start_date).toLocaleString('fr-FR')} - {new Date(event.end_date).toLocaleString('fr-FR')}
                          </span>
                        </div>
                        <h3 className="incident-title">{event.title}</h3>
                        {event.description && (
                          <p className="incident-message">{event.description}</p>
                        )}
                      </div>
                    )
                  } else {
                    return (
                      <div key={`incident-${event.id}`} className={`incident-card incident-past ${getStatusClass(event.status)}`}>
                        <div className="incident-header">
                          <h3>{event.title}</h3>
                          <span className={`incident-status ${getStatusClass(event.status)}`}>
                            {getStatusLabel(event.status)}
                          </span>
                        </div>
                        {event.message && (
                          <p className="incident-message">{event.message}</p>
                        )}
                        <div className="incident-meta">
                          <span>Créé le {formatDate(event.created_at)}</span>
                          {event.resolved_at && (
                            <span className="resolved">Résolu le {formatDate(event.resolved_at)}</span>
                          )}
                        </div>
                        {event.updates && event.updates.length > 0 && (
                          <div className="incident-updates">
                            <h4>Mises à jour:</h4>
                            {event.updates.map((update) => (
                              <div key={update.id} className="incident-update">
                                <span className="update-time">{formatDate(update.created_at)}</span>
                                <p>{update.message}</p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )
                  }
                })}
              </div>
            ) : (
              <p className="no-incidents">Aucun événement passé.</p>
            )
          })()}
        </section>
      </div>
    </div>
  )
}

export default Status


