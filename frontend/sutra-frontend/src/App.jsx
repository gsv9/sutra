import { useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import MobileApp from './components/MobileApp';
import SupplierPortal from './components/SupplierPortal';

export default function App() {
  useEffect(() => {
    // Detect native Android binary execution
    const isNative = window.Capacitor && window.Capacitor.isNativePlatform();
    
    // Check if the current route is the root dashboard
    const isRoot = window.location.pathname === '/';

    // Hijack the route instantly for the Snapdragon mobile node
    if (isNative && isRoot) {
      window.location.replace('/mobile');
    }
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/mobile" element={<MobileApp />} />
        <Route path="/supplier" element={<SupplierPortal />} />
        <Route path="*" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  );
}