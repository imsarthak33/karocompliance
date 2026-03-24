// @ts-nocheck
import React from 'react';
import { useDocuments } from '../../hooks/useDocuments';

export const DashboardHome = () => {
  useDocuments();

  return (
    <div className="flex h-full flex-col gap-6 p-6 bg-gray-100">
      <div className="grid grid-cols-4 gap-4">
        <StatCard title="Total Clients" value="42" color="bg-white" />
        <StatCard title="Filings Due" value="12" color="bg-amber-50" />
        <StatCard title="Pending Documents" value="8" color="bg-blue-50" />
        <StatCard title="Critical Anomalies" value="3" color="bg-red-50 text-red-700" />
      </div>

      <div className="rounded-lg bg-white p-4 shadow-sm">
        <h3 className="mb-4 text-lg font-semibold text-gray-800">Filing Calendar</h3>
        {/* Filing Calendar Component Here */}
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="rounded-lg bg-white p-4 shadow-sm h-96 overflow-y-auto">
          <h3 className="mb-4 text-lg font-semibold text-gray-800">Live Document Feed</h3>
          {/* Document Feed Component Here */}
        </div>
        <div className="rounded-lg bg-white p-4 shadow-sm h-96 overflow-y-auto">
          <h3 className="mb-4 text-lg font-semibold text-gray-800">Unresolved Anomalies</h3>
          {/* Anomaly Alerts Component Here */}
        </div>
      </div>
    </div>
  );
};

const StatCard = ({ title, value, color }: { title: string, value: string, color: string }) => (
  <div className={`rounded-lg p-6 shadow-sm border border-gray-200 ${color}`}>
    <h4 className="text-sm font-medium text-gray-500">{title}</h4>
    <p className="mt-2 text-3xl font-bold">{value}</p>
  </div>
);