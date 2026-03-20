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
  const isHpBoosted = player.max_hp > (player.base_max_hp || 20);
  const isFoodBoosted = player.max_food > (player.base_max_food || 20);

  return (
    <div className="glass h-full flex flex-col">
      <div className="glass-header">Vitals & Resources</div>
      <div className="p-4 flex-1">
        <ResourceCard 
          label="HEALTH" 
          value={player.hp} 
          max={player.max_hp} 
          color={isHpBoosted ? "var(--accent-primary)" : "#ff4d4d"} 
        />
        {isHpBoosted && <div className="text-[10px] text-accent-primary -mt-2 mb-2 opacity-80">PERK BOOSTED +{player.max_hp - player.base_max_hp}</div>}
        
        <ResourceCard 
          label="FOOD" 
          value={player.food} 
          max={player.max_food || 20} 
          color="var(--accent-warning)" 
        />
        {isFoodBoosted && <div className="text-[10px] text-accent-warning -mt-2 mb-2 opacity-80">PERK BOOSTED +{player.max_food - player.base_max_food}</div>}

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
              <div className="text-xl font-bold">{player.character?.level || 1}</div>
           </div>
        </div>
      </div>

      {player.character?.perks?.length > 0 && (
        <div className="p-4 border-t border-white border-opacity-10">
          <div className="text-[10px] text-secondary uppercase mb-2">Active Perks</div>
          <div className="flex flex-wrap gap-2">
            {player.character.perks.map(perkId => (
              <span key={perkId} className="px-2 py-0.5 bg-accent-primary bg-opacity-10 border border-accent-primary border-opacity-30 rounded text-[9px] text-accent-primary uppercase tracking-wider">
                {perkId.replace(/_perk/g, '').replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ResourcePanel;
