import React, { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { analyzeBillingData } from "./api"; 

const UploadForm = ({ onUploadStart, onUploadSuccess, onUploadError }) => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "text/csv": [".csv"] },
    multiple: false,
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return alert("Please select a CSV file.");

    setLoading(true);
    onUploadStart();

    try {
      const reader = new FileReader();
      reader.onload = async (ev) => {
        const text = ev.target.result;
        console.log("File preview (first 1000 chars):\n", text.slice(0, 1000));

        const data = await analyzeBillingData(file);
        console.log("API response data:", data);
        onUploadSuccess(data);
      };
      reader.onerror = (err) => {
        console.error("File read error:", err);
        onUploadError("Failed to read file.");
      };
      reader.readAsText(file);

    } catch (err) {
      console.error("Upload error:", err);
      const detail = err.response?.data?.detail || err.message || "Unknown error";
      onUploadError(`Upload failed: ${detail}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="upload-form">
      <div
        {...getRootProps()}
        className={`upload-dropzone ${isDragActive ? "dragging" : ""}`}
      >
        <input {...getInputProps()} />
        <p>Drag 'n' drop a .csv file here, or click to select</p>
        <button
          type="button"
          className="upload-button"
          style={{ pointerEvents: "none" }}
        >
          Select File
        </button>
        {file && <p className="file-name">{file.name}</p>}
      </div>

      <button
        type="submit"
        className="upload-button"
        disabled={loading || !file}
        style={{ marginTop: "16px" }}
      >
        {loading ? "Analyzing..." : "Upload & Analyze"}
      </button>
    </form>
  );
};

export default UploadForm;