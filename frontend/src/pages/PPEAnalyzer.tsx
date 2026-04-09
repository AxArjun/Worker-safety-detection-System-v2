import React, { useState, useRef } from 'react';
import { 
  Upload, ShieldCheck, AlertCircle, RefreshCcw, 
  User as UserIcon, HardHat, Shirt, FileText, 
  Clock, Info,
  Scan, Activity
} from 'lucide-react';
import axios from 'axios';
import { BASE_URL } from '../api/client';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';

/**
 * Enterprise PPE Detection Schema (Frontend-side)
 * Optimized for multi-class status reporting.
 */
interface PPEDetection {
  person_id: number;
  bbox?: number[];
  helmet?: boolean;
  vest?: boolean;
  confidence?: number;
  status?: 'FULLY_COMPLIANT' | 'NO_VEST' | 'NO_HELMET' | 'NON_COMPLIANT';
}

interface PPESummary {
  total_persons: number;
  compliant: number;
  partial: number;
  non_compliant: number;
}

interface PPEResponse {
  detections: PPEDetection[];
  violations: string[];
  compliance: string;
  summary: PPESummary;
  image_base64: string;
  timestamp: string;
}

export default function PPEAnalyzer() {
  const { user } = useAuth();
  
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<PPEResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setResult(null);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsAnalyzing(true);
    setError(null);
    
    const formData = new FormData();
    formData.append('image', selectedFile);

    try {
      const token = localStorage.getItem('token');
      
      const res = await axios.post(`${BASE_URL}/api/ppe/analyze`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log("PPE MULTI-CLASS API RESPONSE:", res.data);

      if (!res || !res.data) {
        throw new Error("Industrial Analysis Pipeline returned empty response");
      }

      setResult(res.data);
      toast.success('Multi-class analysis archived to audit trail');
    } catch (err: any) {
      console.error('PPE Analysis error:', err);
      const errMsg = err.response?.data?.detail || err.message || 'Industrial analysis pipeline failed';
      setError(errMsg);
      toast.error(errMsg);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const reset = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setResult(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  if (error) {
    return (
      <div className="ppe-enterprise-container flex items-center justify-center">
        <div className="card p-8 border-accent-danger max-w-md text-center">
          <AlertCircle className="text-accent-danger mx-auto mb-4" size={48} />
          <h2 className="enterprise-title mb-2">Analysis System Failure</h2>
          <p className="text-secondary mb-6">{error}</p>
          <button className="btn-enterprise-primary" onClick={reset}>
            <RefreshCcw size={14} />
            <span>Retry Pipeline</span>
          </button>
        </div>
      </div>
    );
  }

  const showUploadMode = !isAnalyzing && !result;

  return (
    <div className="ppe-enterprise-container">
      {/* Top Header Section */}
      <div className="enterprise-header">
        <div className="header-main">
          <div className="title-group">
            <h1 className="enterprise-title">Multi-Class PPE Analyzer</h1>
            <div className="enterprise-subtitle">
              <Scan size={14} className="text-secondary" />
              <span>Multi-Region Pipeline v3.2 • Roboflow PPE Integrated</span>
            </div>
          </div>
          
          <div className="header-actions">
            {(result || previewUrl) && (
              <div className="audit-metadata">
                <Clock size={14} />
                <span>{result?.timestamp ? new Date(result.timestamp).toLocaleString() : 'Manual Inspection Session'}</span>
                <span className="divider">|</span>
                <UserIcon size={14} />
                <span>Operator: {user?.email || 'System'}</span>
              </div>
            )}
            <button className="btn-secondary" onClick={reset}>
               <RefreshCcw size={14} />
               <span>Clear Session</span>
            </button>
          </div>
        </div>
      </div>

      <div className="enterprise-body">
        <div className="layout-grid">
          
          {/* LEFT: Primary Visual Interface */}
          <div className="viewport-card card">
            {showUploadMode && !previewUrl ? (
              <div className="dropzone-area" onClick={() => fileInputRef.current?.click()}>
                <div className="dropzone-hint">
                  <div className="icon-box">
                    <Upload size={24} />
                  </div>
                  <h3>Ingest Source Material</h3>
                  <p>Drag detection frames or site snapshots here</p>
                  <div className="format-badges">
                    <span>JPEG</span>
                    <span>PNG</span>
                    <span>HI-RES</span>
                  </div>
                </div>
                <input 
                  type="file" 
                  ref={fileInputRef} 
                  onChange={handleFileChange} 
                  accept="image/*" 
                  style={{ display: 'none' }} 
                />
              </div>
            ) : (
              <div className="viewer-container">
                <div className="viewer-inner">
                  {result?.image_base64 ? (
                    <img 
                      src={`data:image/jpeg;base64,${result.image_base64}`} 
                      alt="Processed Inspection" 
                      className="viewer-image"
                    />
                  ) : previewUrl ? (
                    <img 
                      src={previewUrl} 
                      alt="Ingested Source" 
                      className="viewer-image opacity-50"
                    />
                  ) : null}

                  {isAnalyzing && (
                    <div className="analysis-shimmer">
                      <div className="shimmer-bar" />
                      <div className="shimmer-content">
                        <div className="spinner-small" />
                        <span>Running Multi-Region PPE Validation...</span>
                      </div>
                    </div>
                  )}
                </div>

                {!result && !isAnalyzing && previewUrl && (
                  <div className="viewer-actions">
                    <button className="btn-enterprise-primary" onClick={handleUpload}>
                      <ShieldCheck size={18} />
                      Execute Multi-Class Audit
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* RIGHT: Data Insights & Audit Results */}
          <div className="side-panel">
            {/* Compliance Summary HUD */}
            <div className="panel-section status-section">
               <div className="section-header-compact">COMPLIANCE SUMMARY</div>
               
               {result ? (
                 <div className="summary-dashboard flex flex-col gap-2">
                    <div className="summary-stat-row flex justify-between gap-3">
                       <div className="stat-card flex-1 p-2 bg-surface border border-default">
                          <span className="text-secondary text-[0.65rem] block">TOTAL</span>
                          <span className="text-lg font-bold">{result.summary.total_persons}</span>
                       </div>
                       <div className="stat-card flex-1 p-2 bg-surface-dim border border-accent-success text-accent-success">
                          <span className="text-[0.65rem] block">SAFE</span>
                          <span className="text-lg font-bold">{result.summary.compliant}</span>
                       </div>
                    </div>
                    <div className="summary-stat-row flex justify-between gap-3">
                       <div className="stat-card flex-1 p-2 bg-surface-dim border border-accent-warning text-accent-warning">
                          <span className="text-[0.65rem] block">PARTIAL</span>
                          <span className="text-lg font-bold">{result.summary.partial}</span>
                       </div>
                       <div className="stat-card flex-1 p-2 bg-surface-dim border border-accent-danger text-accent-danger">
                          <span className="text-[0.65rem] block">VIOLATED</span>
                          <span className="text-lg font-bold">{result.summary.non_compliant}</span>
                       </div>
                    </div>
                 </div>
               ) : (
                 <div className="status-hud-placeholder">
                    {isAnalyzing ? (
                      <RefreshCcw size={24} className="animate-spin opacity-50" />
                    ) : (
                      <Info size={24} className="opacity-20" />
                    )}
                    <span>{isAnalyzing ? 'Processing telemetry...' : 'Awaiting data ingestion...'}</span>
                 </div>
               )}
            </div>

            {/* Worker Details List */}
            <div className="panel-section">
               <div className="section-header-compact">WORKER TELEMETRY</div>
               <div className="telemetry-list max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
                 {result?.detections?.map((worker, idx) => {
                   const getStatusColor = (status?: string) => {
                     if (status === 'FULLY_COMPLIANT') return 'border-accent-success text-accent-success';
                     if (status === 'NON_COMPLIANT') return 'border-accent-danger text-accent-danger';
                     return 'border-accent-warning text-accent-warning';
                   };

                   return (
                     <div key={worker.person_id || idx} className={`telemetry-card mb-2 border-l-4 ${getStatusColor(worker?.status)}`}>
                        <div className="card-top flex justify-between mb-1">
                          <div className="worker-id flex items-center gap-1 text-[0.7rem] font-bold">
                            <Activity size={10} />
                            <span>NODE-{worker.person_id || idx + 1}</span>
                          </div>
                          <div className="status-badge text-[0.6rem] font-bold tracking-tight">
                            {worker?.status?.replace('_', ' ')}
                          </div>
                        </div>
                        
                        <div className="ppe-status-grid flex gap-2">
                          <div className={`ppe-item-compact flex-1 flex items-center gap-2 px-2 py-1 bg-base rounded text-[0.6rem] ${worker.helmet ? 'text-accent-success' : 'text-accent-danger'}`}>
                            <HardHat size={12} />
                            <span>{worker.helmet ? 'HELMET' : 'HEAD UNSAFE'}</span>
                          </div>
                          <div className={`ppe-item-compact flex-1 flex items-center gap-2 px-2 py-1 bg-base rounded text-[0.6rem] ${worker.vest ? 'text-accent-success' : 'text-accent-danger'}`}>
                            <Shirt size={12} />
                            <span>{worker.vest ? 'VEST' : 'TORSO UNSAFE'}</span>
                          </div>
                        </div>
                     </div>
                   );
                 })}
                 
                 {result && (!result?.detections || result.detections.length === 0) && (
                   <div className="empty-state text-[0.7rem] opacity-50 italic">No nodes identified in visual field.</div>
                 )}
                 {!result && !isAnalyzing && <div className="empty-state text-[0.7rem] opacity-50 italic">Data stream offline.</div>}
               </div>
            </div>

            {/* Violation Feed */}
            {result && result?.violations?.length > 0 && (
              <div className="panel-section">
                <div className="section-header-compact">VIOLATION FEED</div>
                <div className="violation-scroll max-h-[150px] overflow-y-auto pr-2 custom-scrollbar">
                  {result.violations.map((v, i) => (
                    <div key={i} className="violation-alert flex items-center gap-2 mb-1 p-2 bg-accent-danger-dim border-l-2 border-accent-danger text-accent-danger text-[0.65rem]">
                      <AlertCircle size={12} />
                      <span>{v}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Action Footer */}
            <div className="panel-section foot-links mt-auto pt-2 border-t border-subtle">
               <div className="enterprise-alert flex items-center gap-2 text-[0.6rem] text-accent-info opacity-70">
                  <FileText size={12} />
                  <span>Report ID: {result?.timestamp ? Date.now().toString().slice(-8) : '---'} persisted</span>
               </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
