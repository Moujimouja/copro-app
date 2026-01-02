import { useState, useEffect } from 'react'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import toast from 'react-hot-toast'
import './Statistics.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function Statistics() {
  const [generalStats, setGeneralStats] = useState(null)
  const [buildingStats, setBuildingStats] = useState({})
  const [buildings, setBuildings] = useState([])
  const [selectedBuilding, setSelectedBuilding] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeSection, setActiveSection] = useState('general')
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear())

  // Générer la liste des années disponibles (année en cours et 5 années précédentes)
  const currentYear = new Date().getFullYear()
  const availableYears = Array.from({ length: 6 }, (_, i) => currentYear - i)

  useEffect(() => {
    loadGeneralStatistics()
    loadBuildings()
  }, [selectedYear])

  useEffect(() => {
    if (selectedBuilding) {
      loadBuildingStatistics(selectedBuilding)
    }
  }, [selectedBuilding, selectedYear])

  const loadGeneralStatistics = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_URL}/api/v1/public/statistics/general?year=${selectedYear}`)
      if (response.ok) {
        const data = await response.json()
        setGeneralStats(data)
      } else {
        toast.error('Erreur lors du chargement des statistiques générales')
      }
    } catch (error) {
      console.error('Erreur chargement statistiques générales:', error)
      toast.error('Erreur de connexion')
    } finally {
      setLoading(false)
    }
  }

  const loadBuildings = async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/public/buildings`)
      if (response.ok) {
        const data = await response.json()
        setBuildings(data)
      }
    } catch (error) {
      console.error('Erreur chargement bâtiments:', error)
    }
  }

  const loadBuildingStatistics = async (buildingId) => {
    try {
      const response = await fetch(`${API_URL}/api/v1/public/statistics/by-building/${buildingId}?year=${selectedYear}`)
      if (response.ok) {
        const data = await response.json()
        setBuildingStats(prev => ({
          ...prev,
          [buildingId]: data
        }))
      } else {
        toast.error('Erreur lors du chargement des statistiques du bâtiment')
      }
    } catch (error) {
      console.error('Erreur chargement statistiques bâtiment:', error)
      toast.error('Erreur de connexion')
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return ''
    const date = new Date(dateString)
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    })
  }

  const formatDateTime = (dateString) => {
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

  const formatHours = (hours) => {
    if (!hours) return 'N/A'
    if (hours < 24) {
      return `${hours.toFixed(1)}h`
    }
    const days = Math.floor(hours / 24)
    const remainingHours = hours % 24
    return `${days}j ${remainingHours.toFixed(1)}h`
  }

  if (loading) {
    return <div className="statistics-loading">Chargement des statistiques...</div>
  }

  const currentStats = activeSection === 'general' ? generalStats : (selectedBuilding ? buildingStats[selectedBuilding] : null)

  return (
    <div className="statistics-page">
      <div className="statistics-header">
        <h1>Statistiques</h1>
        <div className="year-selector">
          <label htmlFor="year-select">Année :</label>
          <select
            id="year-select"
            value={selectedYear}
            onChange={(e) => setSelectedYear(parseInt(e.target.value))}
            className="year-select"
          >
            {availableYears.map(year => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
        </div>
        <div className="statistics-tabs">
          <button
            className={activeSection === 'general' ? 'active' : ''}
            onClick={() => setActiveSection('general')}
          >
            Statistiques générales
          </button>
          <button
            className={activeSection === 'building' ? 'active' : ''}
            onClick={() => setActiveSection('building')}
          >
            Par bâtiment
          </button>
        </div>
      </div>

      {activeSection === 'building' && (
        <div className="building-selector">
          <label>Sélectionner un bâtiment :</label>
          <select
            value={selectedBuilding || ''}
            onChange={(e) => setSelectedBuilding(e.target.value ? parseInt(e.target.value) : null)}
            className="building-select"
          >
            <option value="">-- Sélectionner un bâtiment --</option>
            {buildings.map(building => (
              <option key={building.id} value={building.id}>
                {building.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {activeSection === 'general' && generalStats && (
        <div className="statistics-content">
          <h2>Statistiques générales - {selectedYear}</h2>
          
          <div className="statistics-section">
            <h3>Nombre d'incidents en {selectedYear} (par jour)</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={generalStats.incidents_by_day}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tickFormatter={(value) => formatDate(value)}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis />
                <Tooltip 
                  labelFormatter={(value) => formatDate(value)}
                  formatter={(value) => [value, 'Incidents']}
                />
                <Legend />
                <Line type="monotone" dataKey="count" stroke="#3498db" strokeWidth={2} name="Nombre d'incidents" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="statistics-section">
            <h3>Temps de résolution moyen, min et max par équipement</h3>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={generalStats.resolution_time_by_equipment}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="equipment_name" 
                  angle={-45}
                  textAnchor="end"
                  height={100}
                />
                <YAxis 
                  label={{ value: 'Temps (heures)', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip 
                  formatter={(value) => formatHours(value)}
                />
                <Legend />
                <Bar dataKey="avg_hours" fill="#3498db" name="Moyenne" />
                <Bar dataKey="min_hours" fill="#2ecc71" name="Minimum" />
                <Bar dataKey="max_hours" fill="#e74c3c" name="Maximum" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="statistics-section">
            <h3>Disponibilité par équipement</h3>
            <div className="equipment-availability-table-container">
              <table className="equipment-availability-table">
                <thead>
                  <tr>
                    <th>Équipement</th>
                    <th>Disponibilité</th>
                    <th>Nombre d'incidents</th>
                    <th>Temps moyen de résolution</th>
                  </tr>
                </thead>
                <tbody>
                  {generalStats.equipment_availability && generalStats.equipment_availability.length > 0 ? (
                    generalStats.equipment_availability.map(equipment => (
                      <tr key={equipment.equipment_id}>
                        <td>{equipment.equipment_name}</td>
                        <td>
                          <div className="availability-cell">
                            <span className={`availability-percent ${equipment.availability_percent >= 95 ? 'high' : equipment.availability_percent >= 80 ? 'medium' : 'low'}`}>
                              {equipment.availability_percent.toFixed(2)}%
                            </span>
                            <div className="availability-bar">
                              <div 
                                className="availability-bar-fill"
                                style={{ width: `${equipment.availability_percent}%` }}
                              />
                            </div>
                          </div>
                        </td>
                        <td>{equipment.incident_count}</td>
                        <td>{equipment.avg_resolution_hours ? formatHours(equipment.avg_resolution_hours) : 'N/A'}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="4" className="no-data">Aucun équipement</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="statistics-section">
            <h3>Tous les incidents</h3>
            <div className="incidents-table-container">
              <table className="incidents-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Titre</th>
                    <th>Équipement</th>
                    <th>Statut</th>
                    <th>Créé le</th>
                    <th>Résolu le</th>
                    <th>Temps de résolution</th>
                  </tr>
                </thead>
                <tbody>
                  {generalStats.all_incidents.map(incident => (
                    <tr key={incident.id}>
                      <td>{incident.id}</td>
                      <td>{incident.title}</td>
                      <td>{incident.service_instance || 'N/A'}</td>
                      <td>
                        <span className={`status-badge status-${incident.status}`}>
                          {incident.status}
                        </span>
                      </td>
                      <td>{formatDateTime(incident.created_at)}</td>
                      <td>{incident.resolved_at ? formatDateTime(incident.resolved_at) : 'Non résolu'}</td>
                      <td>{formatHours(incident.resolution_time_hours)}</td>
                    </tr>
                  ))}
                  {generalStats.all_incidents.length === 0 && (
                    <tr>
                      <td colSpan="7" className="no-data">Aucun incident</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeSection === 'building' && selectedBuilding && buildingStats[selectedBuilding] && (
        <div className="statistics-content">
          <h2>Statistiques pour {buildingStats[selectedBuilding].building_name} - {selectedYear}</h2>
          
          <div className="statistics-section">
            <h3>Nombre d'incidents en {selectedYear} (par jour)</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={buildingStats[selectedBuilding].incidents_by_day}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tickFormatter={(value) => formatDate(value)}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis />
                <Tooltip 
                  labelFormatter={(value) => formatDate(value)}
                  formatter={(value) => [value, 'Incidents']}
                />
                <Legend />
                <Line type="monotone" dataKey="count" stroke="#3498db" strokeWidth={2} name="Nombre d'incidents" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="statistics-section">
            <h3>Temps de résolution moyen, min et max par équipement</h3>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={buildingStats[selectedBuilding].resolution_time_by_equipment}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="equipment_name" 
                  angle={-45}
                  textAnchor="end"
                  height={100}
                />
                <YAxis 
                  label={{ value: 'Temps (heures)', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip 
                  formatter={(value) => formatHours(value)}
                />
                <Legend />
                <Bar dataKey="avg_hours" fill="#3498db" name="Moyenne" />
                <Bar dataKey="min_hours" fill="#2ecc71" name="Minimum" />
                <Bar dataKey="max_hours" fill="#e74c3c" name="Maximum" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="statistics-section">
            <h3>Disponibilité par équipement</h3>
            <div className="equipment-availability-table-container">
              <table className="equipment-availability-table">
                <thead>
                  <tr>
                    <th>Équipement</th>
                    <th>Disponibilité</th>
                    <th>Nombre d'incidents</th>
                    <th>Temps moyen de résolution</th>
                  </tr>
                </thead>
                <tbody>
                  {buildingStats[selectedBuilding].equipment_availability && buildingStats[selectedBuilding].equipment_availability.length > 0 ? (
                    buildingStats[selectedBuilding].equipment_availability.map(equipment => (
                      <tr key={equipment.equipment_id}>
                        <td>{equipment.equipment_name}</td>
                        <td>
                          <div className="availability-cell">
                            <span className={`availability-percent ${equipment.availability_percent >= 95 ? 'high' : equipment.availability_percent >= 80 ? 'medium' : 'low'}`}>
                              {equipment.availability_percent.toFixed(2)}%
                            </span>
                            <div className="availability-bar">
                              <div 
                                className="availability-bar-fill"
                                style={{ width: `${equipment.availability_percent}%` }}
                              />
                            </div>
                          </div>
                        </td>
                        <td>{equipment.incident_count}</td>
                        <td>{equipment.avg_resolution_hours ? formatHours(equipment.avg_resolution_hours) : 'N/A'}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="4" className="no-data">Aucun équipement</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="statistics-section">
            <h3>Tous les incidents</h3>
            <div className="incidents-table-container">
              <table className="incidents-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Titre</th>
                    <th>Équipement</th>
                    <th>Statut</th>
                    <th>Créé le</th>
                    <th>Résolu le</th>
                    <th>Temps de résolution</th>
                  </tr>
                </thead>
                <tbody>
                  {buildingStats[selectedBuilding].all_incidents.map(incident => (
                    <tr key={incident.id}>
                      <td>{incident.id}</td>
                      <td>{incident.title}</td>
                      <td>{incident.service_instance || 'N/A'}</td>
                      <td>
                        <span className={`status-badge status-${incident.status}`}>
                          {incident.status}
                        </span>
                      </td>
                      <td>{formatDateTime(incident.created_at)}</td>
                      <td>{incident.resolved_at ? formatDateTime(incident.resolved_at) : 'Non résolu'}</td>
                      <td>{formatHours(incident.resolution_time_hours)}</td>
                    </tr>
                  ))}
                  {buildingStats[selectedBuilding].all_incidents.length === 0 && (
                    <tr>
                      <td colSpan="7" className="no-data">Aucun incident</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeSection === 'building' && !selectedBuilding && (
        <div className="statistics-placeholder">
          <p>Veuillez sélectionner un bâtiment pour afficher les statistiques</p>
        </div>
      )}
    </div>
  )
}

export default Statistics

