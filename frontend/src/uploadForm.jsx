// src/uploadForm.jsx
import React, { useState } from "react";
import axios from "axios";
import Results from "./results";

const UploadForm = () => {
  const [file, setFile] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return alert("Please select a CSV file.");
  
    // Log file meta
    console.log("Uploading file:", file.name, "size:", file.size);
  
    // Read and print first 1000 chars to ensure contents are correct
    const reader = new FileReader();
    reader.onload = async (ev) => {
      const text = ev.target.result;
      console.log("File preview (first 1000 chars):\n", text.slice(0, 1000));
  
      // Now upload
      const formData = new FormData();
      formData.append("file", file);
  
      try {
        setLoading(true);
        const res = await axios.post("http://localhost:8000/analyze", formData, {
          headers: { "Content-Type": "multipart/form-data" },
          timeout: 300000,
        });
        console.log("API response (full):", res);
        console.log("API response data:", res.data);
        setResults(res.data);
      } catch (err) {
        console.error("Upload error:", err);
        alert("Upload failed. Check console for details.");
      } finally {
        setLoading(false);
      }
    };
  
    reader.onerror = (err) => {
      console.error("File read error:", err);
      alert("Failed to read file.");
    };
  
    reader.readAsText(file);
  };
  

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input type="file" accept=".csv" onChange={handleFileChange} />
        <button type="submit" disabled={loading}>
          {loading ? "Analyzing..." : "Upload & Analyze"}
        </button>
      </form>

      {/* show raw JSON quickly while debugging */}
      {results && (
        <div style={{ marginTop: 16 }}>
          <Results data={results} />
        </div>
      )}
    </div>
  );
};

export default UploadForm;
