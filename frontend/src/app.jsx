// app.jsx
import React, { useState } from "react";
import UploadForm from "./UploadForm";
import Results from "./results";

export default function App() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>☁️ OpenCloud Cost Advisor</h1>
        <p>Upload a cloud billing CSV to generate an optimal saving plan.</p>
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
  );
}