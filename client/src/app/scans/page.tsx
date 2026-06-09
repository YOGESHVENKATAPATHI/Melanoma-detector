"use client";
import { useState, useEffect } from 'react';
import Loader from '@/components/Loader';

export default function Scans() {
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch user history from backend
    fetch('http://localhost:8000/api/history?user_id=1')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) setHistory(data);
      })
      .catch(err => console.error("Failed to fetch history:", err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="dashboard-content">
      {loading && <Loader text="Retrieving Historical Scans..." />}

      <h2 style={{ color: 'var(--text-dark)', marginBottom: '24px' }}>Historical Scan Archive</h2>

      <div className="panel">
        <h3 className="panel-title">Previous Scans (Timeline)</h3>
        <table className="history-table">
          <thead>
            <tr>
              <th>Scan ID</th>
              <th>Date</th>
              <th>Diagnosis</th>
              <th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {history.length > 0 ? (
              history.map((scan: any) => (
                <tr key={scan.id}>
                  <td>#SCN-{scan.id.toString().padStart(4, '0')}</td>
                  <td>{new Date(scan.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' })}</td>
                  <td>
                    <span className={`badge ${scan.final_verdict === 'Malignant' ? 'badge-malignant' : 'badge-benign'}`}>
                      {scan.final_verdict}
                    </span>
                  </td>
                  <td style={{ color: 'var(--primary-color)' }}>{(scan.prediction_score * 100).toFixed(1)}%</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={4} style={{ textAlign: 'center', padding: '40px', color: 'var(--text-light)', fontStyle: 'italic' }}>
                  No historical scans found for this account.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
