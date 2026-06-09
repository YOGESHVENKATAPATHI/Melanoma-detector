"use client";
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Sidebar() {
  const pathname = usePathname();

  // Don't show sidebar on login page
  if (pathname === '/login') return null;

  return (
    <div className="sidebar">
      <div className="sidebar-logo">
        Melanoma AI
      </div>
      <ul className="sidebar-menu">
        <Link href="/" style={{ textDecoration: 'none' }}>
          <li className={`sidebar-item ${pathname === '/' ? 'active' : ''}`}>
            Dashboard
          </li>
        </Link>
        <Link href="/scans" style={{ textDecoration: 'none' }}>
          <li className={`sidebar-item ${pathname === '/scans' ? 'active' : ''}`}>
            Patient Scans
          </li>
        </Link>
        <Link href="/payments" style={{ textDecoration: 'none' }}>
          <li className={`sidebar-item ${pathname === '/payments' ? 'active' : ''}`}>
            Payments
          </li>
        </Link>
      </ul>
      
      <div style={{ padding: '20px', marginTop: 'auto' }}>
        <Link href="/login" style={{ textDecoration: 'none' }}>
           <div style={{ color: 'var(--text-light)', fontSize: '13px', cursor: 'pointer' }}>Sign Out</div>
        </Link>
      </div>
    </div>
  );
}
