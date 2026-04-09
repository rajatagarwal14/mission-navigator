import { Routes, Route } from 'react-router-dom';
import Layout from './components/shared/Layout';
import ProtectedRoute from './components/shared/ProtectedRoute';
import ChatPage from './pages/ChatPage';
import IntakePage from './pages/IntakePage';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import KnowledgePage from './pages/KnowledgePage';
export default function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<ChatPage />} />
      <Route path="/intake" element={<IntakePage />} />
      <Route path="/admin/login" element={<LoginPage />} />

      {/* Protected admin routes */}
      <Route
        path="/admin/dashboard"
        element={
          <ProtectedRoute>
            <Layout><DashboardPage /></Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/knowledge"
        element={
          <ProtectedRoute>
            <Layout><KnowledgePage /></Layout>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}
