import React, { useState } from "react";
import UploadForm from "./UploadForm";
import Results from "./results";
import "./App.css"

export default function App() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  return (
    <div className="app-container">
      <div className="grid-pattern"></div>
      
      <div className="content-wrapper">
        <header className="app-header">
          <div className="status-indicator">
            <div className="status-dot"></div>
            <span className="status-text">System Online</span>
          </div>
          
          <h1>
            <span className="header-main">CloudSaver</span>
            <span className="header-gradient">Cost Advisor</span>
          </h1>
          <p>Upload a cloud billing CSV to generate an optimal saving plan</p>
        </header>
        
        <main>
          <UploadForm
            onUploadStart={() => {
              setLoading(true);
              setResults(null);
              setError(null);
            }}
            onUploadSuccess={(data) => {
              setResults(data);
              setLoading(false);
            }}
            onUploadError={(errMessage) => {
              setLoading(false);
              setError(errMessage);
              alert(`Error: ${errMessage}`);
            }}
          />
          
          <div className="results-container">
            {loading && <div className="loader">Analyzing your data...</div>}
            {error && (
              <div className="error-message">
                <p>
                  <strong>Analysis Failed:</strong> {error}
                </p>
              </div>
            )}
            {results && <Results data={results} />}
          </div>
        </main>
      </div>
    </div>
  );
}