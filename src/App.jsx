import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import MobileApp from './components/MobileApp';
import SupplierPortal from './components/SupplierPortal';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/mobile" element={<MobileApp />} />
        <Route path="/supplier" element={<SupplierPortal />} />
      </Routes>
    </BrowserRouter>
  );
}