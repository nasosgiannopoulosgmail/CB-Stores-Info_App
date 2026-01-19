import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Loader } from '@googlemaps/js-api-loader'
import api from '../services/api'
import { Store, Polygon } from '../types'
import './MapViewer.css'

const GOOGLE_MAPS_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || ''

export default function MapViewer() {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapInstanceRef = useRef<google.maps.Map | null>(null)
  const [mapLoaded, setMapLoaded] = useState(false)

  // Load stores
  const { data: storesData } = useQuery({
    queryKey: ['stores'],
    queryFn: async () => {
      const response = await api.get('/api/v1/stores', {
        params: { limit: 1000, active_only: true }
      })
      return response.data
    }
  })

  // Initialize Google Maps
  useEffect(() => {
    if (!mapRef.current || mapLoaded || !GOOGLE_MAPS_API_KEY) return

    const loader = new Loader({
      apiKey: GOOGLE_MAPS_API_KEY,
      version: 'weekly',
    })

    loader.load().then(() => {
      if (!mapRef.current) return

      const map = new google.maps.Map(mapRef.current, {
        center: { lat: 37.9755, lng: 23.7348 }, // Default: Athens, Greece
        zoom: 12,
      })

      mapInstanceRef.current = map
      setMapLoaded(true)
    })
  }, [mapLoaded])

  // Load and display polygons
  useEffect(() => {
    if (!mapLoaded || !mapInstanceRef.current || !storesData) return

    const stores: Store[] = storesData.stores || []
    const polygonPromises = stores.map(async (store) => {
      try {
        const response = await api.get(`/api/v1/polygons/stores/${store.id}/polygons/current`)
        return { store, polygons: response.data.polygons as Polygon[] }
      } catch {
        return { store, polygons: [] }
      }
    })

    Promise.all(polygonPromises).then((results) => {
      const map = mapInstanceRef.current!
      const markers: google.maps.Marker[] = []
      const polygonOverlays: google.maps.Polygon[] = []

      results.forEach(({ store, polygons }) => {
        // Add store marker
        const marker = new google.maps.Marker({
          position: { lat: store.latitude, lng: store.longitude },
          map,
          title: store.name,
          label: store.id.toString(),
        })
        markers.push(marker)

        // Add polygons
        polygons.forEach((polygon) => {
          const path = polygon.coordinates.map(
            ([lng, lat]) => ({ lat, lng })
          )

          const color = polygon.polygon_type === 'dedicated' 
            ? '#4285F4'  // Blue for dedicated
            : '#34A853'  // Green for delivery

          const polygonOverlay = new google.maps.Polygon({
            paths: path,
            map,
            strokeColor: color,
            strokeOpacity: 0.8,
            strokeWeight: 2,
            fillColor: color,
            fillOpacity: 0.2,
            title: `${store.name} - ${polygon.polygon_type}`,
          })
          polygonOverlays.push(polygonOverlay)
        })
      })

      // Store references for cleanup
      return () => {
        markers.forEach(m => m.setMap(null))
        polygonOverlays.forEach(p => p.setMap(null))
      }
    })
  }, [mapLoaded, storesData])

  if (!GOOGLE_MAPS_API_KEY) {
    return (
      <div className="map-error">
        <p>Google Maps API key is not configured.</p>
        <p>Please set VITE_GOOGLE_MAPS_API_KEY environment variable.</p>
      </div>
    )
  }

  return (
    <div className="map-viewer">
      <h2>Store Map</h2>
      <div ref={mapRef} className="map-container" />
    </div>
  )
}
