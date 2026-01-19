/**
 * Type definitions
 */

export interface Store {
  id: number
  name: string
  latitude: number
  longitude: number
  entersoft_key?: string
  inorder_key?: string
  future_proof_key?: string
  current_franchisee_id?: number
  address?: string
  phone?: string
  email?: string
  active: boolean
  created_at: string
  updated_at: string
}

export interface Polygon {
  id: number
  store_id: number
  polygon_type: 'dedicated' | 'delivery'
  coordinates: [number, number][]  // [longitude, latitude]
  version_number: number
  is_current: boolean
  inactive: boolean
  created_at: string
  notes?: string
}

export interface Franchisee {
  id: number
  name: string
  company_name?: string
  entersoft_key?: string
  inorder_key?: string
  future_proof_key?: string
  contact_email?: string
  contact_phone?: string
  active: boolean
  created_at: string
  updated_at: string
}

export interface TimeRange {
  start: string  // HH:MM
  end: string    // HH:MM
}

export interface Schedule {
  id: number
  store_id: number
  day_of_week: number  // 0=Monday, 6=Sunday
  time_ranges: TimeRange[]
  is_holiday: boolean
  date_override?: string
  active: boolean
  created_at: string
  updated_at: string
}

export interface Point {
  latitude: number
  longitude: number
}

export interface PointCheckResult {
  point: Point
  contained: boolean
  stores: Array<{
    store_id: number
    store_name: string
    latitude: number
    longitude: number
    polygon_id: number
    polygon_type: string
    version_number: number
  }>
}
