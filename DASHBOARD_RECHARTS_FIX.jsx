// Dashboard.jsx - Fixed Chart Components with Recharts
// Fix for: Recharts width/height -1 warning

import React, { useEffect, useState } from 'react';
import {
  LineChart,
  BarChart,
  PieChart,
  Line,
  Bar,
  Pie,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { apiRequest } from './api-client';
import { DASHBOARD_ENDPOINTS } from './api-client';
import './Dashboard.css';

// ============================================================================
// Helper: Render Custom Label for Pie Chart
// ============================================================================
const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * Math.PI / 180);
  const y = cy + radius * Math.sin(-midAngle * Math.PI / 180);

  return (
    <text
      x={x}
      y={y}
      fill="white"
      textAnchor={x > cx ? 'start' : 'end'}
      dominantBaseline="central"
      fontSize="12"
      fontWeight="bold"
    >
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

// ============================================================================
// Component: Investment Growth Chart
// ============================================================================
function InvestmentGrowthChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="chart-placeholder">
        <p>No investment data available</p>
      </div>
    );
  }

  return (
    <div className="chart-wrapper">
      <h3>Investment Growth Over Time</h3>
      {/* ✅ FIX: Wrap in ResponsiveContainer with explicit height */}
      <ResponsiveContainer width="100%" height={300}>
        <LineChart
          data={data}
          margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="month" 
            fontSize={12}
          />
          <YAxis 
            fontSize={12}
          />
          <Tooltip 
            formatter={(value) => `$${parseFloat(value).toFixed(2)}`}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="invested"
            stroke="#1976d2"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
            name="Amount Invested"
          />
          <Line
            type="monotone"
            dataKey="returns"
            stroke="#4caf50"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
            name="Returns"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// ============================================================================
// Component: Projects Distribution Chart
// ============================================================================
function ProjectsDistributionChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="chart-placeholder">
        <p>No project data available</p>
      </div>
    );
  }

  const COLORS = ['#1976d2', '#f57c00', '#388e3c', '#d32f2f', '#7b1fa2'];

  return (
    <div className="chart-wrapper">
      <h3>Investment Distribution by Project</h3>
      {/* ✅ FIX: Wrap in ResponsiveContainer with explicit height */}
      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={data}
          margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="project" 
            fontSize={12}
            angle={-45}
            textAnchor="end"
            height={60}
          />
          <YAxis 
            fontSize={12}
          />
          <Tooltip 
            formatter={(value) => `$${parseFloat(value).toFixed(2)}`}
          />
          <Legend />
          <Bar
            dataKey="amount"
            fill="#1976d2"
            name="Investment Amount"
            radius={[8, 8, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ============================================================================
// Component: Portfolio Composition Pie Chart
// ============================================================================
function PortfolioCompositionChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="chart-placeholder">
        <p>No portfolio data available</p>
      </div>
    );
  }

  const COLORS = ['#1976d2', '#f57c00', '#388e3c', '#d32f2f', '#7b1fa2'];

  return (
    <div className="chart-wrapper">
      <h3>Portfolio Composition</h3>
      {/* ✅ FIX: Wrap in ResponsiveContainer with explicit height */}
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={renderCustomLabel}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={COLORS[index % COLORS.length]}
              />
            ))}
          </Pie>
          <Tooltip 
            formatter={(value) => `$${parseFloat(value).toFixed(2)}`}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

// ============================================================================
// Component: Investor Dashboard (Main)
// ============================================================================
function InvestorDashboard() {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        setLoading(true);
        const data = await apiRequest(
          DASHBOARD_ENDPOINTS.INVESTOR,
          'GET'
        );
        setDashboardData(data);
        setError(null);
      } catch (err) {
        setError(err.message || 'Failed to load dashboard');
        console.error('Dashboard error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, []);

  if (loading) {
    return <div className="loading">Loading dashboard...</div>;
  }

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  if (!dashboardData) {
    return <div className="empty">No dashboard data available</div>;
  }

  return (
    <div className="dashboard-container">
      <h1>Investor Dashboard</h1>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="card">
          <h3>Total Invested</h3>
          <p className="value">
            ${parseFloat(dashboardData.total_invested || 0).toFixed(2)}
          </p>
        </div>
        <div className="card">
          <h3>Projects</h3>
          <p className="value">{dashboardData.projects_invested || 0}</p>
        </div>
        <div className="card">
          <h3>Total Shares</h3>
          <p className="value">{dashboardData.total_shares_owned || 0}</p>
        </div>
        <div className="card">
          <h3>Investments</h3>
          <p className="value">{dashboardData.investment_count || 0}</p>
        </div>
      </div>

      {/* Charts Section */}
      <div className="charts-section">
        {/* Investment Growth Chart */}
        {dashboardData.growth_data && (
          <InvestmentGrowthChart data={dashboardData.growth_data} />
        )}

        {/* Projects Distribution Chart */}
        {dashboardData.projects_data && (
          <ProjectsDistributionChart data={dashboardData.projects_data} />
        )}

        {/* Portfolio Composition Chart */}
        {dashboardData.portfolio_data && (
          <PortfolioCompositionChart data={dashboardData.portfolio_data} />
        )}
      </div>
    </div>
  );
}

export default InvestorDashboard;
