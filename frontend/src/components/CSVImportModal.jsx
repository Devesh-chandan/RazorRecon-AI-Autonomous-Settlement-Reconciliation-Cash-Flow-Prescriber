import { useState, useRef } from 'react';
import { UploadCloud, FileText, CheckCircle2, AlertTriangle, X, Play, RefreshCw } from 'lucide-react';
import { uploadCSVFile } from '../api/client';
import { useReconciliation } from '../context/ReconciliationContext';
import './CSVImportModal.css';

export default function CSVImportModal({ isOpen, onClose }) {
  const { startRecon } = useReconciliation();

  const [sourceType, setSourceType] = useState('razorpay_settlement');
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [importSummary, setImportSummary] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const fileInputRef = useRef(null);

  if (!isOpen) return null;

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      setFile(selected);
      setImportSummary(null);
      setErrorMsg(null);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) {
      if (dropped.name.endsWith('.csv') || dropped.name.endsWith('.xlsx')) {
        setFile(dropped);
        setImportSummary(null);
        setErrorMsg(null);
      } else {
        setErrorMsg('Only .csv and .xlsx files are supported.');
      }
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    setErrorMsg(null);
    setImportSummary(null);

    try {
      const result = await uploadCSVFile(file, sourceType);
      setImportSummary(result);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to upload CSV file.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleRunReconImported = async () => {
    onClose();
    await startRecon('imported');
  };

  const handleRunReconAll = async () => {
    onClose();
    await startRecon('all');
  };

  const resetModal = () => {
    setFile(null);
    setImportSummary(null);
    setErrorMsg(null);
  };

  return (
    <div className="csv-modal-backdrop" onClick={onClose}>
      <div className="csv-modal-card card" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="csv-modal-header">
          <div className="csv-header-title-group">
            <UploadCloud size={18} className="text-blue" />
            <h3>Import Batch Data (CSV / Excel)</h3>
          </div>
          <button className="icon-btn close-btn" onClick={onClose} title="Close">
            <X size={16} />
          </button>
        </div>

        <div className="csv-modal-body">
          {/* File Type Selection */}
          <div className="source-type-selector">
            <label className="field-label">Select Data Source Type:</label>
            <div className="radio-options-grid">
              <label className={`radio-card ${sourceType === 'razorpay_settlement' ? 'radio-card--active' : ''}`}>
                <input
                  type="radio"
                  name="sourceType"
                  value="razorpay_settlement"
                  checked={sourceType === 'razorpay_settlement'}
                  onChange={(e) => setSourceType(e.target.value)}
                />
                <div>
                  <strong className="radio-title">Razorpay Settlement Report</strong>
                  <span className="radio-desc">CSV or XLSX report from Razorpay Dashboard</span>
                </div>
              </label>

              <label className={`radio-card ${sourceType === 'erp_ledger' ? 'radio-card--active' : ''}`}>
                <input
                  type="radio"
                  name="sourceType"
                  value="erp_ledger"
                  checked={sourceType === 'erp_ledger'}
                  onChange={(e) => setSourceType(e.target.value)}
                />
                <div>
                  <strong className="radio-title">ERP Sales Ledger</strong>
                  <span className="radio-desc">Tally, Zoho Books, or custom internal ledger</span>
                </div>
              </label>
            </div>
          </div>

          {/* Drag & Drop Area */}
          <div
            className={`dropzone-area ${isDragOver ? 'dropzone--dragover' : ''} ${file ? 'dropzone--hasfile' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx"
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />

            {file ? (
              <div className="file-info-box">
                <FileText size={32} className="text-blue" />
                <div className="file-meta">
                  <span className="file-name">{file.name}</span>
                  <span className="file-size">{(file.size / 1024).toFixed(1)} KB</span>
                </div>
                <button
                  type="button"
                  className="change-file-btn"
                  onClick={(e) => { e.stopPropagation(); resetModal(); }}
                >
                  Change File
                </button>
              </div>
            ) : (
              <div className="dropzone-placeholder">
                <UploadCloud size={36} className="drop-icon" />
                <p className="drop-text">Drag and drop your <strong>.csv</strong> or <strong>.xlsx</strong> file here</p>
                <span className="drop-sub">or click to browse from computer (up to 50 MB)</span>
              </div>
            )}
          </div>

          {/* Error Alert */}
          {errorMsg && (
            <div className="csv-alert csv-alert--error">
              <AlertTriangle size={16} />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Import Summary Results */}
          {importSummary && (
            <div className="import-result-card">
              <div className="result-header">
                <CheckCircle2 size={18} className="text-green" />
                <strong>Import Completed Successfully</strong>
              </div>
              <div className="result-stats-grid">
                <div className="stat-pill">
                  <span className="stat-num">{importSummary.rows_read}</span>
                  <span className="stat-label">Rows Read</span>
                </div>
                <div className="stat-pill stat-pill--imported">
                  <span className="stat-num">{importSummary.rows_imported}</span>
                  <span className="stat-label">Imported</span>
                </div>
                <div className="stat-pill stat-pill--skipped">
                  <span className="stat-num">{importSummary.rows_skipped}</span>
                  <span className="stat-label">Skipped / Duplicates</span>
                </div>
              </div>

              {importSummary.errors?.length > 0 && (
                <div className="row-errors-list">
                  <span className="error-list-title">Row Warnings:</span>
                  <ul>
                    {importSummary.errors.map((err, i) => (
                      <li key={i}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="csv-modal-footer">
          {importSummary ? (
            <div style={{ display: 'flex', gap: '10px', width: '100%', justifyContent: 'flex-end' }}>
              <button className="btn btn-secondary" onClick={handleRunReconAll} style={{ background: '#f1f5f9', color: '#0f172a', border: '1px solid #cbd5e1' }}>
                Audit All DB Records
              </button>
              <button className="btn btn-primary" onClick={handleRunReconImported}>
                <Play size={14} /> Audit Imported Data Only
              </button>
            </div>
          ) : (
            <button
              className="btn btn-primary"
              onClick={handleUpload}
              disabled={!file || isUploading}
            >
              {isUploading ? (
                <>
                  <RefreshCw size={14} className="animate-spin" />
                  Importing...
                </>
              ) : (
                <>
                  <UploadCloud size={14} />
                  Upload &amp; Import Data
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
