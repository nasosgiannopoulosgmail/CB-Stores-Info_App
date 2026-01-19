import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import StoresList from './pages/StoresList'
import StoreDetail from './pages/StoreDetail'
import MapViewer from './pages/MapViewer'
import Login from './pages/Login'
import Layout from './components/Layout'
import './App.css'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/stores" replace />} />
            <Route path="stores" element={<StoresList />} />
            <Route path="stores/:id" element={<StoreDetail />} />
            <Route path="map" element={<MapViewer />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
