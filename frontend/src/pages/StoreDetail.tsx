import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import api from '../services/api'
import { Store, Polygon } from '../types'
import './StoreDetail.css'

export default function StoreDetail() {
  const { id } = useParams<{ id: string }>()

  const { data: store, isLoading } = useQuery({
    queryKey: ['store', id],
    queryFn: async () => {
      const response = await api.get(`/api/v1/stores/${id}`)
      return response.data as Store
    },
    enabled: !!id
  })

  const { data: polygons } = useQuery({
    queryKey: ['polygons', id],
    queryFn: async () => {
      const response = await api.get(`/api/v1/polygons/stores/${id}/polygons/current`)
      return response.data.polygons as Polygon[]
    },
    enabled: !!id
  })

  if (isLoading) return <div>Loading...</div>
  if (!store) return <div>Store not found</div>

  return (
    <div className="store-detail">
      <div className="store-header">
        <h2>{store.name}</h2>
        <Link to="/stores">← Back to Stores</Link>
      </div>

      <div className="store-info">
        <div className="info-section">
          <h3>Location</h3>
          <p>Latitude: {store.latitude}</p>
          <p>Longitude: {store.longitude}</p>
          <Link to={`/map?store=${store.id}`}>View on Map</Link>
        </div>

        <div className="info-section">
          <h3>External Keys</h3>
          <p>Entersoft: {store.entersoft_key || '-'}</p>
          <p>Inorder: {store.inorder_key || '-'}</p>
          <p>Future Proof: {store.future_proof_key || '-'}</p>
        </div>

        <div className="info-section">
          <h3>Contact</h3>
          <p>Address: {store.address || '-'}</p>
          <p>Phone: {store.phone || '-'}</p>
          <p>Email: {store.email || '-'}</p>
        </div>
      </div>

      <div className="polygons-section">
        <h3>Polygons</h3>
        {polygons && polygons.length > 0 ? (
          <div className="polygons-list">
            {polygons.map((polygon) => (
              <div key={polygon.id} className="polygon-card">
                <h4>{polygon.polygon_type.toUpperCase()}</h4>
                <p>Version: {polygon.version_number}</p>
                <p>Points: {polygon.coordinates.length}</p>
                {polygon.is_current && <span className="badge">Current</span>}
              </div>
            ))}
          </div>
        ) : (
          <p>No polygons found</p>
        )}
      </div>
    </div>
  )
}
