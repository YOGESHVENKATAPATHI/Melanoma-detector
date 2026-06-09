"use client";

export default function Payments() {
  return (
    <div className="dashboard-content" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <div style={{ textAlign: 'center', marginBottom: '40px' }}>
        <h2 style={{ fontSize: '32px', color: 'white', marginBottom: '16px' }}>Unlock Neural Architecture</h2>
        <p style={{ color: 'var(--text-light)' }}>
          Get unrestricted access to the Melanoma AI framework and clustered Dropbox nodes.
        </p>
      </div>

      <div className="pricing-cards">
        <div className="pricing-card">
          <h3 style={{ color: 'var(--text-light)', marginBottom: '12px' }}>Basic Access</h3>
          <h1 style={{ fontSize: '48px', color: 'white', marginBottom: '24px' }}>Free</h1>
          <ul style={{ listStyle: 'none', padding: 0, color: 'var(--text-light)', marginBottom: '32px', textAlign: 'left' }}>
            <li style={{ marginBottom: '12px' }}>✓ 1 Scan per day</li>
            <li style={{ marginBottom: '12px' }}>✓ Standard Confidence Scoring</li>
            <li style={{ marginBottom: '12px', opacity: 0.5 }}>✗ Multi-Scan Comparison</li>
            <li style={{ marginBottom: '12px', opacity: 0.5 }}>✗ Historical Sync</li>
          </ul>
          <button className="btn-primary" style={{ background: 'var(--border-color)', color: 'white' }}>Current Plan</button>
        </div>

        <div className="pricing-card premium">
          <h3 style={{ color: 'var(--primary-color)', marginBottom: '12px' }}>Clinical Pro</h3>
          <h1 style={{ fontSize: '48px', color: 'white', marginBottom: '24px' }}>₹400<span style={{fontSize: '16px', color: 'var(--text-light)'}}>/week</span></h1>
          <ul style={{ listStyle: 'none', padding: 0, color: 'var(--text-light)', marginBottom: '32px', textAlign: 'left' }}>
            <li style={{ marginBottom: '12px', color: 'white' }}>✓ Unlimited Scans</li>
            <li style={{ marginBottom: '12px', color: 'white' }}>✓ Clustered Node Processing</li>
            <li style={{ marginBottom: '12px', color: 'var(--success)' }}>✓ Multi-Scan Comparison</li>
            <li style={{ marginBottom: '12px', color: 'var(--success)' }}>✓ Historical Sync & Analytics</li>
          </ul>
          <button className="btn-primary">Upgrade to Pro</button>
        </div>
      </div>
    </div>
  );
}
