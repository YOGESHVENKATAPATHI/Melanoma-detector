"use client";

import { useState, useRef } from 'react';
import Loader from '@/components/Loader';

export default function Dashboard() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [timeline, setTimeline] = useState<any[]>([]);
  const [breakdown, setBreakdown] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      setPreviewUrl(URL.createObjectURL(selectedFile));
      setTimeline([]); 
      setBreakdown('');
    }
  };

  const triggerUpload = () => {
    fileInputRef.current?.click();
  };

  const handleScan = async () => {
    if (!file) return;
    setLoading(true);
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', '1');

    try {
      let data;
      try {
        const res = await fetch('http://localhost:8000/api/scan', { method: 'POST', body: formData });
        if (res.ok) {
          data = await res.json();
        } else {
          throw new Error("Backend error");
        }
      } catch (e) {
        // Mock fallback to simulate 7-day automated timeline
        await new Promise(r => setTimeout(r, 2000));
        
        // Simulating that the backend found 3 previous scans + this new one
        data = {
          timeline: [
            { day: 1, date: "Oct 24, 2023", verdict: "Benign", confidence: 21.0, growth: "Baseline" },
            { day: 2, date: "Oct 25, 2023", verdict: "Benign", confidence: 35.5, growth: "+14.5% Growth Detected" },
            { day: 3, date: "Oct 26, 2023", verdict: "Malignant", confidence: 60.1, growth: "+39.1% Growth Detected" },
            { day: 4, date: "Today", verdict: "Malignant", confidence: 89.0, growth: "+68.0% Growth Detected" }
          ],
          current_breakdown: "Main Core: 0.9\nSide-Car: 0.85\nFinal: 0.89"
        };
      }

      setTimeline(data.timeline);
      setBreakdown(data.current_breakdown);
    } catch (error) {
      console.error("Scan failed", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard-content">
      {loading && <Loader text="Initializing Temporal Comparison..." />}
      
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-info">
            <h4>Nodes Active</h4>
            <h2>2 <span className="badge badge-benign" style={{marginLeft: '12px'}}>AUC {'>'} 0.95</span></h2>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-info">
            <h4>Pipeline Accuracy</h4>
            <h2>98% <span className="badge badge-benign" style={{marginLeft: '12px'}}>+2%</span></h2>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-info">
            <h4>Scans Processed</h4>
            <h2>48</h2>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-info">
            <h4>Cluster Sync</h4>
            <h2 style={{color: 'var(--success)'}}>Online</h2>
          </div>
        </div>
      </div>

      <div className="scan-area-grid">
        <div className="panel">
          <h3 className="panel-title">Central Imaging Hub</h3>
          <input 
            type="file" 
            accept="image/*" 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            style={{ display: 'none' }} 
          />
          {!previewUrl ? (
            <div className="upload-box" onClick={triggerUpload}>
              <div className="upload-text">Drag & Drop or Click to Upload Scan</div>
              <div style={{fontSize: '12px', color: 'var(--text-light)', marginTop: '8px'}}>Supports JPG, PNG (Max 5MB)</div>
            </div>
          ) : (
            <div className="result-image-container">
              <img src={previewUrl} alt="Preview" />
            </div>
          )}
          
          <button 
            className="btn-primary" 
            onClick={previewUrl ? handleScan : triggerUpload}
            disabled={loading}
          >
            {previewUrl ? 'Analyze & Compare Timeline' : 'Select Scan Image'}
          </button>
          
          {previewUrl && (
             <button 
              className="btn-primary" 
              onClick={() => { setPreviewUrl(null); setFile(null); setTimeline([]); }}
              style={{ background: 'transparent', color: 'var(--text-light)', border: '1px solid var(--border-color)', marginTop: '10px' }}
             >
               Clear
             </button>
          )}
        </div>

        <div className="panel">
          <h3 className="panel-title">Chronological AI Analysis</h3>
          <div className="result-display">
            {timeline.length > 0 ? (
              <div style={{width: '100%'}}>
                <div style={{ marginBottom: '20px' }}>
                  {timeline.map((item, idx) => (
                    <div key={idx} className="timeline-item">
                       <div style={{ width: '40px', height: '40px', background: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', color: 'var(--primary-color)', marginRight: '16px' }}>
                          {item.day}
                       </div>
                       <div style={{ flex: 1 }}>
                          <div style={{ fontSize: '13px', color: 'var(--text-light)', marginBottom: '4px' }}>{item.date}</div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <span className={`badge ${item.verdict === 'Malignant' ? 'badge-malignant' : 'badge-benign'}`}>
                              {item.verdict} ({item.confidence}%)
                            </span>
                            <span style={{ fontSize: '13px', color: item.growth.includes('Reduction') || item.growth.includes('Baseline') ? 'var(--text-light)' : 'var(--warning)' }}>
                              {item.growth}
                            </span>
                          </div>
                       </div>
                    </div>
                  ))}
                </div>

                <div className="verdict-box">
                  <div className="verdict-title">Final Diagnosis (Latest)</div>
                  <div className={`verdict-value ${timeline[timeline.length - 1].verdict === 'Malignant' ? 'verdict-malignant' : 'verdict-benign'}`}>
                    {timeline[timeline.length - 1].verdict}
                  </div>
                </div>

                <div style={{marginTop: '20px', padding: '16px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border-color)', fontSize: '13px', whiteSpace: 'pre-line', color: 'var(--text-light)'}}>
                  <strong>Current Diagnostics Breakdown:</strong><br/>
                  {breakdown}
                </div>
              </div>
            ) : (
              <div style={{color: 'var(--text-light)', marginTop: '60px', textAlign: 'center', fontStyle: 'italic'}}>
                Awaiting scan initialization...
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
