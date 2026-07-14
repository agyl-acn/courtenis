import { LayoutDashboard, Landmark, Calendar } from 'lucide-react';
import './AdminSidebar.css';

export type AdminTab = 'dashboard' | 'courts' | 'bookings';

interface Props {
  activeTab: AdminTab;
  onTabChange: (tab: AdminTab) => void;
}

const NAV_ITEMS = [
  { key: 'dashboard' as AdminTab, label: 'Dashboard', icon: <LayoutDashboard size={16} strokeWidth={1.5} /> },
  { key: 'courts' as AdminTab, label: 'Courts', icon: <Landmark size={16} strokeWidth={1.5} /> },
  { key: 'bookings' as AdminTab, label: 'Bookings', icon: <Calendar size={16} strokeWidth={1.5} /> },
];

export default function AdminSidebar({ activeTab, onTabChange }: Props) {
  return (
    <aside className="admin-sidebar">
      <div className="admin-sidebar-header">
        <span className="admin-sidebar-logo" aria-hidden="true">
          <span className="admin-logo-half admin-logo-green" />
          <span className="admin-logo-half admin-logo-light" />
        </span>
        <span className="admin-sidebar-title">Courtenis Admin</span>
      </div>
      <nav className="admin-nav">
        {NAV_ITEMS.map(({ key, label, icon }) => (
          <button
            key={key}
            className={`admin-nav-item${activeTab === key ? ' active' : ''}`}
            onClick={() => onTabChange(key)}
          >
            {icon}
            <span>{label}</span>
          </button>
        ))}
      </nav>
    </aside>
  );
}
