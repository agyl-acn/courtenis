import { useState } from 'react';
import AdminSidebar from '../components/admin/AdminSidebar';
import type { AdminTab } from '../components/admin/AdminSidebar';
import DashboardTab from '../components/admin/DashboardTab';
import CourtsTab from '../components/admin/CourtsTab';
import BookingsTab from '../components/admin/BookingsTab';
import './AdminPage.css';

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<AdminTab>('dashboard');

  return (
    <div className="admin-layout">
      <AdminSidebar activeTab={activeTab} onTabChange={setActiveTab} />
      <main className="admin-main">
        {activeTab === 'dashboard' && <DashboardTab />}
        {activeTab === 'courts' && <CourtsTab />}
        {activeTab === 'bookings' && <BookingsTab />}
      </main>
    </div>
  );
}
