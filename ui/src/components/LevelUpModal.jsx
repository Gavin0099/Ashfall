import React, { useState, useEffect } from 'react';

const PERK_ICONS = {
  'pack_rat_perk': '📦',
  'eagle_eye_perk': '👁️',
  'scrappie_perk': '🔧',
  'tough_as_nails': '🛡️',
  'quick_hands': '⚡',
  'lead_stomach': '☢️',
  'scavengers_luck': '🍀',
  'field_medic_perk': '💉',
  'default': '🌟'
};

const LevelUpModal = ({ onSelect }) => {
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/run/level_up/options')
      .then(res => res.json())
      .then(data => {
        setOptions(data.options || []);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch perks', err);
        setLoading(false);
      });
  }, []);

  if (loading) return (
    <div className="level-up-overlay">
      <div className="level-up-title">LEVEL UP!</div>
      <div className="level-up-subtitle">Loading Perks...</div>
    </div>
  );

  return (
    <div className="level-up-overlay">
      <div className="level-up-title">LEVEL UP!</div>
      <div className="level-up-subtitle">Select a new Perk to strengthen your survivor</div>
      
      <div className="perk-options-grid">
        {options.map(perk => (
          <div key={perk.id} className="perk-card" onClick={() => onSelect(perk.id)}>
            <span className="perk-icon">{PERK_ICONS[perk.id] || PERK_ICONS.default}</span>
            <h3>{perk.display_name}</h3>
            <p>{perk.description}</p>
          </div>
        ))}
        {options.length === 0 && <div className="text-white">No eligible perks available.</div>}
      </div>
      
      <div className="mt-8 text-secondary text-sm opacity-50 italic">
        Select wisely. Perks are permanent for the duration of this run.
      </div>
    </div>
  );
};

export default LevelUpModal;
