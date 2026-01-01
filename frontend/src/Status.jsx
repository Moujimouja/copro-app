import { useState, useEffect } from 'react'
import './Status.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function Status() {
  const [statusData, setStatusData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
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
      identified: 'incident-identified',
      monitoring: 'incident-monitoring',
      resolved: 'incident-resolved',
      scheduled: 'incident-scheduled'
    }
    return statusMap[status] || 'status-unknown'
  }

  const getStatusLabel = (status) => {
    const labelMap = {
      operational: 'Operational',
      degraded: 'Degraded Performance',
      partial_outage: 'Partial Outage',
      major_outage: 'Major Outage',
      maintenance: 'Under Maintenance',
      investigating: 'Investigating',
      identified: 'Identified',
      monitoring: 'Monitoring',
      resolved: 'Resolved',
      scheduled: 'Scheduled'
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
        <div className={`overall-status ${getStatusClass(statusData.overall_status)}`}>
          <span className="status-indicator"></span>
          <span className="status-text">{getStatusLabel(statusData.overall_status)}</span>
        </div>
      </div>

      <div className="status-content">
        <section className="services-section">
          <h2>Services</h2>
          <div className="services-grid">
            {statusData.services.map((service) => (
              <div key={service.id} className={`service-card ${getStatusClass(service.status)}`}>
                <div className="service-header">
                  <span className="service-status-indicator"></span>
                  <h3>{service.name}</h3>
                </div>
                {service.description && (
                  <p className="service-description">{service.description}</p>
                )}
                <div className="service-status">
                  {getStatusLabel(service.status)}
                </div>
              </div>
            ))}
            {statusData.services.length === 0 && (
              <p className="no-services">Aucun service configuré</p>
            )}
          </div>
        </section>

        <section className="incidents-section">
          <h2>Incidents Récents</h2>
          {statusData.incidents.length > 0 ? (
            <div className="incidents-list">
              {statusData.incidents.map((incident) => (
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
                    <span>{formatDate(incident.created_at)}</span>
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
            <p className="no-incidents">Aucun incident récent. Tous les systèmes fonctionnent normalement.</p>
          )}
        </section>
      </div>
    </div>
  )
}

export default Status


