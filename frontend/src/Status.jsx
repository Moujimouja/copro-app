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
      const buildings = new Set(statusData.services.map(s => s.building_name || 'Commun'))
      const initialExpanded = {}
      buildings.forEach(building => {
        initialExpanded[building] = true // Toutes expandées par défaut
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
                              className={`service-item-list ${getStatusClass(service.status)} ${isAdmin ? 'service-item-admin' : ''}`}
                            >
                              <div className="service-item-content">
                                <span className="service-status-indicator"></span>
                                <div className="service-info">
                                  <h4 className="service-name">{service.name}</h4>
                                  {service.description && (
                                    <p className="service-description">{service.description}</p>
                                  )}
                                  <span className="service-status-badge">{getStatusLabel(service.status)}</span>
                                </div>
                              </div>
                              {isAdmin && (
                                <div className="service-status-buttons">
                                  {statusOptions.map((option) => (
                                    <button
                                      key={option.value}
                                      className={`status-btn-small ${service.status === option.value ? 'status-btn-active' : ''}`}
                                      onClick={() => updateServiceStatus(service.id, option.value)}
                                      style={{ 
                                        borderColor: option.color,
                                        color: service.status === option.value ? option.color : '#616061'
                                      }}
                                      title={option.label}
                                    >
                                      {option.label}
                                    </button>
                                  ))}
                                </div>
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
          <h2>Incidents en Cours</h2>
          {(() => {
            const activeIncidents = statusData.incidents.filter(i => i.status !== 'closed' && i.status !== 'resolved')
            return activeIncidents.length > 0 ? (
              <div className="incidents-list">
                {activeIncidents.map((incident) => (
                  <div key={incident.id} className={`incident-card ${getStatusClass(incident.status)}`}>
                    <div className="incident-header">
                      <h3>{incident.title}</h3>
                      <span className={`incident-status ${getStatusClass(incident.status)}`}>
                        {getStatusLabel(incident.status)}
                      </span>
                    </div>
                    {incident.message && (
                      <p className="incident-message">{incident.message}</p>
                    )}
                    <div className="incident-meta">
                      <span>Créé le {formatDate(incident.created_at)}</span>
                    </div>
                    {incident.updates && incident.updates.length > 0 && (
                      <div className="incident-updates">
                        <h4>Mises à jour:</h4>
                        {incident.updates.map((update) => (
                          <div key={update.id} className="incident-update">
                            <span className="update-time">{formatDate(update.created_at)}</span>
                            <p>{update.message}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-incidents">Aucun incident en cours. Tous les systèmes fonctionnent normalement.</p>
            )
          })()}
        </section>

        <section className="incidents-section incidents-past">
          <h2>Incidents Passés</h2>
          {(() => {
            const pastIncidents = statusData.incidents.filter(i => i.status === 'closed' || i.status === 'resolved')
            return pastIncidents.length > 0 ? (
              <div className="incidents-list">
                {pastIncidents.map((incident) => (
                  <div key={incident.id} className={`incident-card incident-past ${getStatusClass(incident.status)}`}>
                    <div className="incident-header">
                      <h3>{incident.title}</h3>
                      <span className={`incident-status ${getStatusClass(incident.status)}`}>
                        {getStatusLabel(incident.status)}
                      </span>
                    </div>
                    {incident.message && (
                      <p className="incident-message">{incident.message}</p>
                    )}
                    <div className="incident-meta">
                      <span>Créé le {formatDate(incident.created_at)}</span>
                      {incident.resolved_at && (
                        <span className="resolved">Résolu le {formatDate(incident.resolved_at)}</span>
                      )}
                    </div>
                    {incident.updates && incident.updates.length > 0 && (
                      <div className="incident-updates">
                        <h4>Mises à jour:</h4>
                        {incident.updates.map((update) => (
                          <div key={update.id} className="incident-update">
                            <span className="update-time">{formatDate(update.created_at)}</span>
                            <p>{update.message}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-incidents">Aucun incident passé.</p>
            )
          })()}
        </section>
      </div>
    </div>
  )
}

export default Status


