import React from 'react';

const ResourceCard = ({ label, value, max, color }) => (
  <div className="resource-card">
    <label>
      <span>{label}</span>
      <span>{value} / {max}</span>
    </label>
    <div className="resource-bar">
      <div 
        className="resource-fill" 
        style={{ 
          width: `${(value / max) * 100}%`, 
          backgroundColor: color 
        }} 
      />
    </div>
  </div>
);

const ResourcePanel = ({ player }) => {
  return (
    <div className="glass h-full">
      <div className="glass-header">Vitals & Resources</div>
      <div className="p-4">
        <ResourceCard 
          label="HEALTH" 
          value={player.hp} 
          max={player.max_hp} 
          color="var(--accent-primary)" 
        />
        <ResourceCard 
          label="FOOD" 
          value={player.food} 
          max={20} 
          color="var(--accent-warning)" 
        />
        <ResourceCard 
          label="RADIATION" 
          value={player.radiation} 
          max={10} 
          color="var(--accent-danger)" 
        />
        
        <div className="mt-8 grid grid-cols-2 gap-4">
           <div className="item-slot text-center">
              <div className="text-secondary text-xs">AMMO</div>
              <div className="text-xl font-bold">{player.ammo}</div>
           </div>
           <div className="item-slot text-center">
              <div className="text-secondary text-xs">SCRAP</div>
              <div className="text-xl font-bold" style={{color: 'var(--accent-warning)'}}>{player.scrap}</div>
           </div>
           <div className="item-slot text-center">
              <div className="text-secondary text-xs">MEDKITS</div>
              <div className="text-xl font-bold" style={{color: 'var(--accent-secondary)'}}>{player.medkits}</div>
           </div>
           <div className="item-slot text-center">
              <div className="text-secondary text-xs">LVL</div>
              <div className="text-xl font-bold">1</div>
           </div>
        </div>
      </div>
    </div>
  );
};

export default ResourcePanel;
