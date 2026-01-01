import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import './Status.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function Status() {
  const [statusData, setStatusData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [isAdmin, setIsAdmin] = useState(false)

  useEffect(() => {
    // Vérifier si l'utilisateur est admin
    const token = localStorage.getItem('token')
    setIsAdmin(!!token)
    
    fetchStatus()
    // Refresh every 30 seconds
    const interval = setInterval(fetchStatus, 30000)
    return () => clearInterval(interval)
  }, [])

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
        <h1>Statut des Services</h1>
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
            // Grouper les services par bâtiment puis par type
            const groupedServices = {}
            const allOperational = statusData.services.every(s => s.status === 'operational')
            
            statusData.services.forEach(service => {
              const buildingKey = service.building_identifier || service.building_name || 'Commun'
              const typeKey = service.service_type_name || 'Autre'
              
              if (!groupedServices[buildingKey]) {
                groupedServices[buildingKey] = {}
              }
              if (!groupedServices[buildingKey][typeKey]) {
                groupedServices[buildingKey][typeKey] = []
              }
              groupedServices[buildingKey][typeKey].push(service)
            })
            
            if (statusData.services.length === 0) {
              return <p className="no-services">Aucun service configuré</p>
            }
            
            return (
              <div className={`services-container ${allOperational ? 'services-compact' : ''}`}>
                {Object.entries(groupedServices).map(([buildingKey, types]) => (
                  <div key={buildingKey} className="building-group">
                    <h3 className="building-title">{buildingKey}</h3>
                    <div className="building-group-types">
                      {Object.entries(types).map(([typeKey, services]) => {
                      const typeStatus = services.some(s => s.status !== 'operational') 
                        ? services.find(s => s.status !== 'operational')?.status || 'operational'
                        : 'operational'
                      
                      return (
                        <div key={typeKey} className={`service-type-group ${allOperational ? 'type-compact' : ''}`}>
                          {!allOperational && (
                            <div className={`type-header ${getStatusClass(typeStatus)}`}>
                              <span className="type-status-indicator"></span>
                              <span className="type-name">{typeKey}</span>
                              <span className="type-count">({services.length})</span>
                            </div>
                          )}
                          <div className={`services-list ${allOperational ? 'services-list-compact' : ''}`}>
                            {services.map((service) => (
                              <div 
                                key={service.id} 
                                className={`service-item ${getStatusClass(service.status)} ${allOperational ? 'service-compact' : ''} ${isAdmin ? 'service-item-admin' : ''}`}
                              >
                                {!allOperational && (
                                  <>
                                    <div className="service-header">
                                      <span className="service-status-indicator"></span>
                                      <h4>{service.name}</h4>
                                    </div>
                                    {service.description && (
                                      <p className="service-description">{service.description}</p>
                                    )}
                                    <div className="service-status">
                                      {getStatusLabel(service.status)}
                                    </div>
                                  </>
                                )}
                                {allOperational && (
                                  <div className="service-compact-content">
                                    <span className="service-status-indicator service-indicator-small"></span>
                                    <span className="service-name-compact">{service.name}</span>
                                  </div>
                                )}
                                {isAdmin && (
                                  <div className="service-status-buttons">
                                    {statusOptions.map((option) => (
                                      <button
                                        key={option.value}
                                        className={`status-btn ${service.status === option.value ? 'status-btn-active' : ''}`}
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
                        </div>
                      )
                    })}
                    </div>
                  </div>
                ))}
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


