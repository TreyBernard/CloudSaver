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
  return { labels, datasets: [{ data, backgroundColor: ["#8b5cf6","#ec4899","#3b82f6","#10b981","#f59e0b","#ef4444"], borderWidth: 0 }] };
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
  return { labels, datasets: [{ data, backgroundColor: ["#f59e0b","#ef4444","#3b82f6","#10b981","#8b5cf6","#ec4899"], borderWidth: 0 }] };
};

const getTopSavings = (items, topN = 10) => {
  const sortedItems = [...items].sort((a, b) => Number(b.estimated_savings || 0) - Number(a.estimated_savings || 0));
  const topItems = sortedItems.slice(0, topN);
  const labels = topItems.map((i) => i.resource_name || i.service || "unknown");
  const data = topItems.map((i) => Number(i.estimated_savings || 0));
  return {
    labels,
    datasets: [
      {
        label: "Estimated Savings ($)",
        data,
        backgroundColor: "rgba(16, 185, 129, 0.8)",
        borderColor: "rgba(5, 150, 105, 1)",
        borderWidth: 1,
        borderRadius: 6,
      },
    ],
  };
};

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: "bottom",
      labels: { color: "#111827", font: { size: 13, family: "Inter, sans-serif" } },
    },
    title: {
      display: true,
      color: "#111827",
      font: { size: 16, weight: "bold" },
    },
    tooltip: {
      backgroundColor: "rgba(255,255,255,0.95)",
      titleColor: "#111827",
      bodyColor: "#374151",
      borderColor: "rgba(229,231,235,1)",
      borderWidth: 1,
    },
  },
};

const barChartOptions = {
  ...chartOptions,
  scales: {
    x: { grid: { color: "rgba(229,231,235,0.6)", drawBorder: false }, ticks: { color: "#374151" } },
    y: { grid: { color: "rgba(229,231,235,0.6)", drawBorder: false }, ticks: { color: "#374151" } },
  },
};

const Results = ({ data }) => {
  const items = Array.isArray(data?.findings) ? data.findings : [];
  const totalSavings = data?.total_estimated_monthly_savings || 0;
  const numFindings = data?.num_findings || 0;

  if (numFindings === 0) {
    return (
      <div className="results-summary" style={{ justifyContent: "center" }}>
        <div className="summary-stat">
          <h3>Status</h3>
          <p style={{ background: "linear-gradient(to right, #10b981, #059669)", WebkitBackgroundClip: "text", color: "transparent", fontWeight: 600 }}>
            All Good!
          </p>
        </div>
      </div>
    );
  }

  const savingsByServiceData = getSavingsByService(items);
  const savingsByIssueData = getSavingsByIssueType(items);
  const topSavingsData = getTopSavings(items);

  return (
    <section className="results-section" style={{ color: "#111827", fontFamily: "Inter, sans-serif" }}>
      {/* Summary */}
      <div className="results-summary" style={{ display: "flex", gap: "2rem", marginBottom: "2rem" }}>
        <div style={{ flex: 1, background: "#f9fafb", padding: "1.5rem", borderRadius: "1rem" }}>
          <h3 style={{ color: "#374151", fontWeight: 600 }}>Total Estimated Savings</h3>
          <p style={{ fontSize: "1.75rem", fontWeight: 700, color: "#059669" }}>${totalSavings.toLocaleString()}</p>
        </div>
        <div style={{ flex: 1, background: "#f9fafb", padding: "1.5rem", borderRadius: "1rem" }}>
          <h3 style={{ color: "#374151", fontWeight: 600 }}>Total Findings</h3>
          <p style={{ fontSize: "1.75rem", fontWeight: 700, color: "#7c3aed" }}>{numFindings}</p>
        </div>
      </div>

      {/* Charts */}
      <div className="charts-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "2rem" }}>
        <div style={{ background: "#fff", borderRadius: "1rem", padding: "1rem", boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}>
          <h3 style={{ marginBottom: "1rem", fontWeight: 600, color: "#111827" }}>Savings by Service</h3>
          <div style={{ height: "260px" }}>
            <Pie data={savingsByServiceData} options={chartOptions} />
          </div>
        </div>

        <div style={{ background: "#fff", borderRadius: "1rem", padding: "1rem", boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}>
          <h3 style={{ marginBottom: "1rem", fontWeight: 600, color: "#111827" }}>Savings by Issue Type</h3>
          <div style={{ height: "260px" }}>
            <Doughnut data={savingsByIssueData} options={chartOptions} />
          </div>
        </div>

        <div style={{ background: "#fff", borderRadius: "1rem", padding: "1rem", boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}>
          <h3 style={{ marginBottom: "1rem", fontWeight: 600, color: "#111827" }}>Top 10 Savings Opportunities</h3>
          <div style={{ height: "280px" }}>
            <Bar data={topSavingsData} options={barChartOptions} />
          </div>
        </div>
      </div>

      <div className="findings-list" style={{ marginTop: "3rem", paddingLeft: "6rem", paddingRight: "6rem" }}>
        <h2 style={{ color: "#000000", fontWeight: 700, marginBottom: "1rem" }}>All Findings</h2>

        {items.map((f, idx) => (
          <div
            key={idx}
            style={{
              background: "#f9fafb",
              borderRadius: "0.75rem",
              padding: "1.5rem",
              marginBottom: "1.5rem",
              boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h3 style={{ fontWeight: 600, color: "#111827" }}>
                {f.resource_name || "Unknown Resource"} <span style={{ color: "#6b7280" }}>({f.service})</span>
              </h3>
              <span style={{ fontWeight: 700, color: "#059669" }}>${Number(f.estimated_savings || 0).toLocaleString()}</span>
            </div>

            <div style={{ marginTop: "1rem" }}>
              <div style={{ marginBottom: "1rem" }}>
                <h4 style={{ fontWeight: 600, color: "#374151" }}>Explanation</h4>
                <p style={{ color: "#374151" }}>{f.explanation}</p>
                <hr style={{ margin: "1rem 0", borderColor: "#e5e7eb" }} />
              </div>

              <div>
                <h4 style={{ fontWeight: 600, color: "#374151" }}>Action Plan</h4>

                <div
                  className="action-plan-content"
                  style={{
                    background: "#fff",
                    borderRadius: "0.5rem",
                    padding: "0.75rem",
                    border: "1px solid #e5e7eb",
                    color: "#111827",
                  }}
                >
                  <ReactMarkdown
                    components={{
                      code({ node, inline, className, children, ...props }) {
                        if (inline) {
                          return (
                            <code style={{ background: "transparent", padding: 0, color: "#111827", fontSize: "0.95rem" }} {...props}>
                              {children}
                            </code>
                          );
                        }
                        return (
                          <pre style={{ background: "transparent", padding: "0.5rem", margin: 0, overflow: "auto" }}>
                            <code style={{ background: "transparent", color: "#111827" }} {...props}>
                              {children}
                            </code>
                          </pre>
                        );
                      },
                      mark({ children }) {
                        return <span style={{ background: "transparent", color: "#111827" }}>{children}</span>;
                      },
                      pre({ children }) {
                        return <div style={{ background: "transparent" }}>{children}</div>;
                      },
                    }}
                  >
                    {f.action_command || ""}
                  </ReactMarkdown>
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
