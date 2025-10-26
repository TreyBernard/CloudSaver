import React from "react";
import { Bar, Pie, Doughnut } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from "chart.js";
import ReactMarkdown from "react-markdown"; 
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

const getSavingsByService = (items) => {
  const serviceMap = items.reduce((acc, item) => {
    const service = item.service || "Unknown";
    const savings = Number(item.estimated_savings || 0);
    acc[service] = (acc[service] || 0) + savings;
    return acc;
  }, {});

  const labels = Object.keys(serviceMap);
  const data = Object.values(serviceMap);

  return {
    labels,
    datasets: [
      {
        data,
        backgroundColor: [
          "#4285F4",
          "#34A853",
          "#FBBC05",
          "#EA4335",
          "#a142f4",
          "#f441a0",
        ],
      },
    ],
  };
};

const getSavingsByIssueType = (items) => {
  const issueMap = items.reduce((acc, item) => {
    const issue = item.issue || "Unknown";
    const savings = Number(item.estimated_savings || 0);
    acc[issue] = (acc[issue] || 0) + savings;
    return acc;
  }, {});

  const labels = Object.keys(issueMap);
  const data = Object.values(issueMap);
  return {
    labels,
    datasets: [
      {
        data,
        backgroundColor: ["#FBBC05", "#EA4335", "#4285F4", "#34A853"],
      },
    ],
  };
};

const getTopSavings = (items, topN = 10) => {
  const sortedItems = [...items].sort(
    (a, b) => Number(b.estimated_savings || 0) - Number(a.estimated_savings || 0)
  );
  const topItems = sortedItems.slice(0, topN);

  const labels = topItems.map(
    (i) => i.resource_name || i.service || "unknown"
  );
  const data = topItems.map((i) => Number(i.estimated_savings || 0));
  return {
    labels,
    datasets: [
      {
        label: "Estimated Savings ($)",
        data,
        backgroundColor: "rgba(52, 168, 83, 0.6)",
        borderColor: "rgba(52, 168, 83, 1)",
        borderWidth: 1,
      },
    ],
  };
};

const Results = ({ data }) => {
  const items = Array.isArray(data?.findings) ? data.findings : [];
  const totalSavings = data?.total_estimated_monthly_savings || 0;
  const numFindings = data?.num_findings || 0;

  if (numFindings === 0) {
    return (
      <div className="results-summary" style={{ justifyContent: "center" }}>
        <h3>No optimization findings identified. Looks good!</h3>
      </div>
    );
  }
  const savingsByServiceData = getSavingsByService(items);
  const savingsByIssueData = getSavingsByIssueType(items);
  const topSavingsData = getTopSavings(items);

  return (
    <section className="results-section">
      {/* 1. Summary Cards */}
      <div className="results-summary">
        <div className="summary-stat">
          <h3>Total Estimated Savings</h3>
          <p>${totalSavings.toLocaleString()}</p>
        </div>
        <div className="summary-stat findings">
          <h3>Total Findings</h3>
          <p>{numFindings}</p>
        </div>
      </div>

      {/* 2. Charts Grid */}
      <div className="charts-grid">
        <div className="chart-container">
          <h3>Savings by Service</h3>
          <Pie data={savingsByServiceData} options={{ responsive: true, maintainAspectRatio: false }} />
        </div>
        <div className="chart-container">
          <h3>Savings by Issue Type</h3>
          <Doughnut data={savingsByIssueData} options={{ responsive: true, maintainAspectRatio: false }} />
        </div>
        <div className="chart-container" style={{ gridColumn: "1 / -1" }}>
          <h3>Top 10 Savings Opportunities</h3>
          <Bar data={topSavingsData} options={{ responsive: true, maintainAspectRatio: false }} />
        </div>
      </div>

      {/* 3. Findings List */}
      <div className="findings-list">
        <h2>All Findings</h2>
        {items.map((f, idx) => (
          <div key={idx} className="finding-card">
            <div className="finding-header">
              <h3>
                {f.resource_name || "Unknown Resource"}{" "}
                <span className="service">({f.service})</span>
              </h3>
              <span className="savings">
                ${Number(f.estimated_savings || 0).toLocaleString()}
              </span>
            </div>
            <div className="finding-body">
              <div className="finding-section">
                <h4>Explanation</h4>
                <p>{f.explanation}</p>
                <hr style={{border: 0, borderTop: '1px solid #e2e8f0', margin: '16px 0'}} />
                <p><strong>Issue:</strong> {f.issue}</p>
                <p><strong>Confidence:</strong> {f.confidence}</p>
              </div>
              <div className="finding-section">
                <h4>Action Plan</h4>
                <div className="action-plan-content">
                  <ReactMarkdown>{f.action_command}</ReactMarkdown>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};

export default Results;