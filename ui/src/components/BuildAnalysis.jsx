import React, { useState, useEffect } from 'react';

const BuildAnalysis = ({ player, apiBase }) => {
  const [breakdown, setBreakdown] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchBreakdown = async () => {
      try {
        const res = await fetch(`${apiBase}/run/modifiers/breakdown`);
        if (res.ok) {
          const data = await res.json();
          setBreakdown(data);
        }
      } catch (err) {
        console.error("Failed to fetch breakdown", err);
      } finally {
        setLoading(false);
      }
    };
    fetchBreakdown();
  }, [player, apiBase]);

  if (loading) return <div className="text-xs opacity-50 p-4">ANALYZING BUILD...</div>;
  if (!breakdown) return null;

  return (
    <div className="glass p-4 mt-4 border-accent-secondary animate-in fade-in duration-500 overflow-hidden">
      <div className="flex justify-between items-center mb-4 border-b border-white border-opacity-10 pb-2">
        <h3 className="text-accent-secondary font-black text-xs tracking-tighter">BUILD IDENTITY</h3>
        <span className="text-[9px] opacity-40 uppercase">v0.2 Balance Lab</span>
      </div>

      {/* Archetype Tiers */}
      <div className="mb-6 space-y-4">
        {Object.entries(breakdown.tags?.primary || {}).length > 0 || breakdown.archetype ? (
          renderArchetypeTiers()
        ) : (
          <div className="text-[10px] opacity-30 italic text-center py-2">No primary archetypes detected</div>
        )}
        {renderMechanismTags()}
      </div>

      {/* Modifier Breakdown - Collapsible or Mini */}
      <details className="group">
        <summary className="text-[10px] text-secondary uppercase mb-2 cursor-pointer hover:text-white transition-colors flex justify-between items-center">
          <span>Detailed Breakdown</span>
          <span className="text-[8px] opacity-30 group-open:rotate-180 transition-transform">▼</span>
        </summary>
        <div className="space-y-3 mt-2">
          {Object.entries(breakdown.stats).map(([key, data]) => {
            const hasChange = data.final !== data.base;
            if (!hasChange) return null;
            
            return (
              <div key={key} className="text-[11px] p-2 bg-white bg-opacity-5 rounded border border-white border-opacity-5">
                <div className="flex justify-between mb-1">
                  <span className="opacity-70 text-[9px]">{key.replace(/_bonus|_multiplier/g, '').replace(/_/g, ' ').toUpperCase()}</span>
                  <span className="font-mono text-accent-primary">{data.final.toFixed(1)}</span>
                </div>
                <div className="space-y-1 mt-1">
                  {data.sources.map((src, i) => (
                    <div key={i} className={`flex justify-between text-[8px] ${src.type === 'synergy' ? 'text-accent-secondary font-bold' : 'opacity-60'}`}>
                      <span>{src.type === 'synergy' ? '⭐' : '•'} {src.name}</span>
                      <span>{src.value > 0 ? '+' : ''}{src.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </details>
    </div>
  );
};

export default BuildAnalysis;
