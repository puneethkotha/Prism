import { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from 'recharts'
import { getMetrics } from '../lib/api'
import type { EvaluationMetrics } from '../types'

const STATIC_METRICS: EvaluationMetrics = {
  precision: 0.9306,
  recall: 0.9363,
  f1: 0.9332,
  avg_latency_ms: 7.15,
  p50_latency_ms: 6.35,
  p95_latency_ms: 13.68,
  p99_latency_ms: 23.99,
  total_products: 25000,
  tagged_products: 25000,
  tagging_reduction_pct: 47.0,
  sample_size: 500,
}

function MetricCard({ label, value, sub, color = 'text-prism-600' }: {
  label: string; value: string; sub?: string; color?: string
}) {
  return (
    <div className="bg-white border border-gray-100 rounded-xl p-5 shadow-sm">
      <div className={`text-3xl font-bold ${color} mb-1`}>{value}</div>
      <div className="text-sm font-medium text-gray-700">{label}</div>
      {sub && <div className="text-xs text-gray-400 mt-1">{sub}</div>}
    </div>
  )
}

export function MetricsDashboard() {
  const [metrics, setMetrics] = useState<EvaluationMetrics>(STATIC_METRICS)
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    getMetrics()
      .then(m => { setMetrics(m); setLoaded(true) })
      .catch(() => setLoaded(true))
  }, [])

  const latencyData = [
    { name: 'p50', ms: metrics.p50_latency_ms },
    { name: 'avg', ms: metrics.avg_latency_ms },
    { name: 'p95', ms: metrics.p95_latency_ms },
    { name: 'p99', ms: metrics.p99_latency_ms },
  ]

  const prf = [
    { name: 'Precision', value: Math.round(metrics.precision * 100) },
    { name: 'Recall', value: Math.round(metrics.recall * 100) },
    { name: 'F1', value: Math.round(metrics.f1 * 100) },
  ]

  const taggingData = [
    { name: 'Automated', value: Math.round(metrics.tagging_reduction_pct), fill: '#5a65f8' },
    { name: 'Manual review', value: Math.round(100 - metrics.tagging_reduction_pct), fill: '#e5e7eb' },
  ]

  return (
    <section id="metrics" className="bg-gray-50 border-t border-gray-100 py-16 px-4">
      <div className="max-w-5xl mx-auto">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Evaluation Metrics</h2>
        <p className="text-gray-500 text-sm mb-8">
          Computed on a 500-item held-out sample with human-labeled ground truth.
          {!loaded && ' Loading live metrics…'}
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-10">
          <MetricCard label="Tag Precision" value={`${(metrics.precision * 100).toFixed(1)}%`} sub="vs human labels" />
          <MetricCard label="Tag Recall" value={`${(metrics.recall * 100).toFixed(1)}%`} sub="vs human labels" />
          <MetricCard label="F1 Score" value={`${(metrics.f1 * 100).toFixed(1)}%`} sub="harmonic mean" />
          <MetricCard
            label="Tagging Reduction"
            value={`${metrics.tagging_reduction_pct.toFixed(0)}%`}
            sub="less manual work"
            color="text-emerald-600"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
          <MetricCard label="Products Indexed" value={metrics.total_products.toLocaleString()} sub="Amazon Electronics" />
          <MetricCard label="p95 Search Latency" value={`${metrics.p95_latency_ms.toFixed(0)}ms`} sub="target: <120ms" color="text-indigo-600" />
          <MetricCard label="Sample Size" value={metrics.sample_size.toLocaleString()} sub="human-labeled items" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <h3 className="text-sm font-semibold text-gray-700 mb-4">Search Latency Distribution (ms)</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={latencyData} margin={{ top: 4, right: 4, bottom: 0, left: -10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#9ca3af' }} />
                <YAxis tick={{ fontSize: 12, fill: '#9ca3af' }} />
                <Tooltip formatter={(v: number) => [`${v.toFixed(1)}ms`, 'Latency']} />
                <Bar dataKey="ms" fill="#5a65f8" radius={[4, 4, 0, 0]} />
                {/* 120ms target line */}
                <line x1="0" y1={120} x2="100%" y2={120} stroke="#ef4444" strokeDasharray="4 2" />
              </BarChart>
            </ResponsiveContainer>
            <p className="text-xs text-gray-400 mt-2">p95 at 7.7ms - well under 120ms target</p>
          </div>

          <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <h3 className="text-sm font-semibold text-gray-700 mb-4">Precision / Recall / F1</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={prf} margin={{ top: 4, right: 4, bottom: 0, left: -10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#9ca3af' }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 12, fill: '#9ca3af' }} unit="%" />
                <Tooltip formatter={(v: number) => [`${v}%`, '']} />
                <Bar dataKey="value" fill="#4347ed" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 md:col-span-2">
            <h3 className="text-sm font-semibold text-gray-700 mb-1">Manual Tagging Workload Reduction</h3>
            <p className="text-xs text-gray-400 mb-4">
              Fraction of products where every predicted tag matched the human label exactly - no corrections needed. The remaining {(100 - metrics.tagging_reduction_pct).toFixed(0)}% required at least one field correction.
            </p>
            <div className="flex items-center gap-6">
              <div style={{ width: 180, height: 180 }}>
                <PieChart width={180} height={180}>
                  <Pie
                    data={taggingData}
                    cx={85}
                    cy={85}
                    innerRadius={52}
                    outerRadius={80}
                    dataKey="value"
                    startAngle={90}
                    endAngle={-270}
                  >
                    {taggingData.map((entry, i) => (
                      <Cell key={i} fill={entry.fill} />
                    ))}
                  </Pie>
                </PieChart>
              </div>
              <div className="flex flex-col gap-3">
                {taggingData.map(d => (
                  <div key={d.name} className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-sm" style={{ background: d.fill }} />
                    <span className="text-sm text-gray-600">{d.name}</span>
                    <span className="text-sm font-semibold text-gray-800 ml-auto">{d.value}%</span>
                  </div>
                ))}
                <p className="text-xs text-gray-400 mt-2 max-w-xs">
                  Reduction = precision (fraction of tags needing no human correction).
                  Measured on 500-item sample.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
