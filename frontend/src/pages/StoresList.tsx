import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import api from '../services/api'
import { Store } from '../types'
import './StoresList.css'

export default function StoresList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['stores'],
    queryFn: async () => {
      const response = await api.get('/api/v1/stores', {
        params: { limit: 1000, active_only: true }
      })
      return response.data
    }
  })

  if (isLoading) return <div>Loading...</div>
  if (error) return <div>Error loading stores</div>

  const stores: Store[] = data?.stores || []

  return (
    <div className="stores-list">
      <div className="stores-header">
        <h2>Stores ({stores.length})</h2>
        <Link to="/map">View on Map</Link>
      </div>
      
      <div className="stores-table">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Location</th>
              <th>Keys</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {stores.map((store) => (
              <tr key={store.id}>
                <td>{store.id}</td>
                <td>{store.name}</td>
                <td>
                  {store.latitude.toFixed(6)}, {store.longitude.toFixed(6)}
                </td>
                <td>
                  {store.entersoft_key || '-'} / {store.inorder_key || '-'}
                </td>
                <td>
                  <Link to={`/stores/${store.id}`}>View</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
