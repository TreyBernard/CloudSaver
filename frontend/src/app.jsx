import React, { useState } from 'react';
import UploadForm from "./UploadForm";
import Results from "./Results";

export default function App() {
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);

    return (
        <div style={{ padding: 24, fontFamily: 'system-ui, Arial' }}>
            <h1>OpenCloud Cost Advisor</h1>
            <p>Upload a cloud billing cvs to generate a optimal saving plan</p>
            <UploadForm setResults={setResults} setLoading={setLoading} />
            <div style={{ marginTop: 24 }}>
                {loading && <p>Loading...</p>}
                {results && <Results results={results} />}
            </div>
        </div>
    );
}
