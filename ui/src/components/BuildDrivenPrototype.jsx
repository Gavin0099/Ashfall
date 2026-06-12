import React, { useMemo, useState } from 'react';
import clinicScene from '../assets/clinic-scene.svg';
import checkpointScene from '../assets/checkpoint-scene.svg';
import marketScene from '../assets/market-scene.svg';

const RUN_PATH = [
  { id: 'roadside_trap', title: '路邊陷阱' },
  { id: 'locked_clinic', title: '封鎖診所' },
  { id: 'infection_checkpoint', title: '感染檢查站' },
  { id: 'underground_market', title: '地下市場' },
  { id: 'vault_gate', title: '避難所閘門' },
];

const KIND_LABELS = {
  common: '共通選項',
  build_gated: 'Build 開啟',
  flag_gated: '旗標開啟',
  locked: '鎖定誘惑',
};

const RESOURCE_LABELS = {
  hp: '生命',
  water: '水',
  ammo: '彈藥',
  medkits: '醫療包',
};

const PROTOTYPE_STATES = [
  {
    id: 'vault_mechanic',
    buildName: '避難所技工',
    fantasy: '我比人更懂舊世界系統。',
    eventId: 'locked_clinic',
    eventTitle: '封鎖診所',
    eventNumber: 2,
    image: clinicScene,
    scene:
      '診所的門卡在半開狀態，通電的磁鎖還在低鳴。窗戶裂了，但門邊控制板穿過灰塵與乾血，仍閃著微弱燈號。',
    highRoutes: ['修理', '終端機', '掃描器'],
    weakness: '不擅長威嚇，也很難取得黑市信任。',
    special: { STR: 2, PER: 6, INT: 8, CHA: 2, SUR: 4 },
    traits: ['技工', '避難所居民'],
    resources: { hp: 18, water: 2, ammo: 6, medkits: 1 },
    choices: [
      {
        id: 'force_clinic_window',
        label: '硬撬破裂的診所窗戶',
        kind: 'common',
        consequencePreview: '會損失生命，並留下「強行闖入診所」的後果。',
      },
      {
        id: 'repair_clinic_door',
        label: '修復門邊控制板',
        kind: 'build_gated',
        requirementLabel: '[智力] [技工]',
        consequencePreview: '安全進入診所，保留補給，並為後續檢查站留下醫療憑證。',
      },
    ],
    lockedChoices: [
      {
        id: 'fake_medical_authorization',
        label: '用偽造醫療授權通過',
        kind: 'locked',
        requirementLabel: '[魅力] [騙徒]',
        lockedText: '你看得懂印章格式，但你沒有把謊言賣出去的本事。',
      },
      {
        id: 'intimidate_squatters',
        label: '威嚇裡面的佔屋者',
        kind: 'locked',
        requirementLabel: '[力量] [威嚇者]',
        lockedText: '你的聲音裡沒有足以讓他們相信的暴力。',
      },
    ],
    consequenceLog: [
      '路邊陷阱已被乾淨解除。',
      '旗標：trap_disarmed',
      '預告：安全進入診所後，後續可能取得無菌補給。',
    ],
    summary: {
      opened: ['repair_clinic_door'],
      locked: ['fake_medical_authorization', 'intimidate_squatters'],
      flags: ['trap_disarmed', 'clinic_entered_safely'],
      endingPreview: '技術進入結局現在變得合理。',
    },
    testFocus: '技術能力應該打開乾淨進入路線，同時讓社交與暴力路線保持可見但不可用。',
  },
  {
    id: 'wasteland_grifter',
    buildName: '廢土騙徒',
    fantasy: '我靠讀懂人心，並比他們更會說謊活下來。',
    eventId: 'infection_checkpoint',
    eventTitle: '感染檢查站',
    eventNumber: 3,
    image: checkpointScene,
    scene:
      '兩名守衛拉著隔離繩，一台老舊掃描器不停吐出誤判。隊伍裡每個人都在盤算，自己還買得起哪一種故事。',
    highRoutes: ['唬弄', '交易', '偽造文件'],
    weakness: '不擅長正面武力，也不懂技術系統。',
    special: { STR: 2, PER: 4, INT: 3, CHA: 8, SUR: 3 },
    traits: ['騙徒', '商販'],
    resources: { hp: 16, water: 3, ammo: 3, medkits: 0 },
    choices: [
      {
        id: 'wait_out_screening',
        label: '排隊等完篩檢',
        kind: 'common',
        consequencePreview: '消耗食物與時間壓力，但不需要特殊能力。',
      },
      {
        id: 'talk_through_checkpoint',
        label: '用一套說法混過檢查站',
        kind: 'build_gated',
        requirementLabel: '[魅力] [商販]',
        consequencePreview: '讓守衛相信你的故事，並留下檢查站通過旗標。',
      },
      {
        id: 'present_clinic_papers',
        label: '拿出偽造診所文件',
        kind: 'flag_gated',
        requirementLabel: '[clinic_fake_credentials]',
        consequencePreview: '消耗前面建立的假文件優勢。',
      },
    ],
    lockedChoices: [
      {
        id: 'use_sterile_clinic_supplies',
        label: '使用無菌診所補給',
        kind: 'locked',
        requirementLabel: '[clinic_entered_safely]',
        lockedText: '你之前沒有乾淨進入診所，手上沒有足以說服人的醫療證明。',
      },
      {
        id: 'recognize_raider_scar_protocol',
        label: '辨認掠奪者疤痕暗號',
        kind: 'locked',
        requirementLabel: '[ex_raider]',
        lockedText: '守衛身上的疤痕確實有意思，但那不是你的語言。',
      },
    ],
    consequenceLog: [
      '用撿來的紙張偽造了診所授權。',
      '旗標：clinic_fake_credentials',
      '消耗：market_contact_earned 讓說法更可信。',
    ],
    summary: {
      opened: ['talk_through_checkpoint', 'present_clinic_papers'],
      locked: ['use_sterile_clinic_supplies', 'recognize_raider_scar_protocol'],
      flags: ['clinic_fake_credentials', 'checkpoint_story_believed'],
      endingPreview: '社交詐欺結局現在變得合理。',
    },
    testFocus: '社交掩護應該把前面的假文件變成活路，同時讓技術證明與暴力暗號保持鎖定。',
  },
  {
    id: 'ex_raider',
    buildName: '前掠奪者',
    fantasy: '我懂暴力者怎麼思考，因為我以前就是其中之一。',
    eventId: 'underground_market',
    eventTitle: '地下市場',
    eventNumber: 4,
    image: marketScene,
    scene:
      '市場藏在裂開的加油站底下。沒有人把舊幫派的名字說出口，但每個人都認得誰還背著那筆債。',
    highRoutes: ['威嚇', '幫派辨識', '暴力捷徑'],
    weakness: '平民不信任你，權威也更容易敵視你。',
    special: { STR: 8, PER: 3, INT: 2, CHA: 3, SUR: 6 },
    traits: ['前掠奪者', '威嚇者'],
    resources: { hp: 20, water: 1, ammo: 8, medkits: 0 },
    choices: [
      {
        id: 'buy_overpriced_pass',
        label: '買下過度抬價的通行證',
        kind: 'common',
        consequencePreview: '消耗廢料，但不產生特殊槓桿。',
      },
      {
        id: 'call_in_raider_debt',
        label: '討回一筆舊掠奪者人情債',
        kind: 'build_gated',
        requirementLabel: '[前掠奪者]',
        consequencePreview: '設定掠奪者人情債旗標，但也增加結局代價。',
      },
      {
        id: 'show_checkpoint_scar',
        label: '亮出檢查站疤痕暗號',
        kind: 'flag_gated',
        requirementLabel: '[checkpoint_guard_spooked]',
        consequencePreview: '把前面製造的恐懼轉成市場通行權。',
      },
    ],
    lockedChoices: [
      {
        id: 'repair_vendor_scanner',
        label: '修理攤販的掃描器',
        kind: 'locked',
        requirementLabel: '[智力] [技工]',
        lockedText: '這台掃描器是舊世界垃圾。你只知道怎麼把它砸壞。',
      },
      {
        id: 'forge_market_contact',
        label: '偽造市場人脈',
        kind: 'locked',
        requirementLabel: '[魅力] [商販]',
        lockedText: '這群人要的是收據，不是包裝成人情的威脅。',
      },
    ],
    consequenceLog: [
      '檢查站守衛認出舊疤暗號後退縮。',
      '旗標：checkpoint_guard_spooked',
      '預告：掠奪者壓力能打開避難所，但倖存者會記住你。',
    ],
    summary: {
      opened: ['call_in_raider_debt', 'show_checkpoint_scar'],
      locked: ['repair_vendor_scanner', 'forge_market_contact'],
      flags: ['checkpoint_guard_spooked', 'raider_debt_called'],
      endingPreview: '威嚇進入結局現在變得合理。',
    },
    testFocus: '暴力名聲應該變成可用槓桿，同時讓技術修理與乾淨交易保持不可及。',
  },
];

function Badge({ children, tone = 'neutral' }) {
  return <span className={`bd-badge bd-badge-${tone}`}>{children}</span>;
}

function ChoiceCard({ choice }) {
  const isLocked = choice.kind === 'locked';
  const tone = choice.kind === 'common' ? 'neutral' : choice.kind === 'flag_gated' ? 'warning' : isLocked ? 'danger' : 'primary';

  return (
    <article className={`bd-choice ${isLocked ? 'is-locked' : ''}`}>
      <div className="bd-choice-topline">
        <Badge tone={tone}>{KIND_LABELS[choice.kind] || choice.kind}</Badge>
        {choice.requirementLabel && <span className="bd-requirement">{choice.requirementLabel}</span>}
      </div>
      <h3>{choice.label}</h3>
      <p>{isLocked ? choice.lockedText : choice.consequencePreview}</p>
    </article>
  );
}

function BuildDrivenPrototype({ onBack }) {
  const [activeBuildId, setActiveBuildId] = useState(PROTOTYPE_STATES[0].id);
  const activeState = useMemo(
    () => PROTOTYPE_STATES.find((state) => state.id === activeBuildId) || PROTOTYPE_STATES[0],
    [activeBuildId]
  );

  return (
    <div className="bd-shell">
      <header className="bd-header">
        <div>
          <div className="bd-kicker">P4-UI-B // STATIC VALIDATION</div>
          <h1>Ashfall Build 驗證台</h1>
          <p>同一條事件鏈，不同 build，不同故事證據。</p>
        </div>
        <button className="bd-back-button" onClick={onBack}>返回</button>
      </header>

      <main className="bd-workbench">
        <aside className="bd-build-rail">
          <div className="bd-rail-heading">
            <span>選擇 Build</span>
            <strong>3 個預設</strong>
          </div>
          <section className="bd-build-select" aria-label="Build select">
            {PROTOTYPE_STATES.map((state) => (
              <button
                key={state.id}
                className={`bd-build-card ${state.id === activeBuildId ? 'is-active' : ''}`}
                onClick={() => setActiveBuildId(state.id)}
              >
                <span>{state.buildName}</span>
                <small>{state.fantasy}</small>
              </button>
            ))}
          </section>

          <section className="bd-panel bd-identity-panel">
            <div className="bd-panel-heading">
              <h2>身分</h2>
              <Badge tone="primary">{activeState.eventId}</Badge>
            </div>
            <p className="bd-build-fantasy">{activeState.fantasy}</p>
            <div className="bd-stat-grid">
              {Object.entries(activeState.special).map(([key, value]) => (
                <div key={key} className="bd-stat">
                  <span>{key}</span>
                  <strong>{value}</strong>
                </div>
              ))}
            </div>
            <div className="bd-traits">
              {activeState.traits.map((trait) => (
                <Badge key={trait} tone="neutral">{trait}</Badge>
              ))}
            </div>
          </section>

          <section className="bd-panel">
            <div className="bd-panel-heading">
              <h2>Run 路徑</h2>
              <span>固定序列</span>
            </div>
            <ol className="bd-timeline">
              {RUN_PATH.map((event, index) => {
                const isCurrent = event.id === activeState.eventId;
                const isComplete = index + 1 < activeState.eventNumber;
                return (
                  <li key={event.id} className={`${isCurrent ? 'is-current' : ''} ${isComplete ? 'is-complete' : ''}`}>
                    <span>{index + 1}</span>
                    <div>
                      <strong>{event.title}</strong>
                      <small>{isCurrent ? '目前事件' : isComplete ? '已解決' : '尚未抵達'}</small>
                    </div>
                  </li>
                );
              })}
            </ol>
          </section>
        </aside>

        <section className="bd-event-column">
          <div className="bd-scene-panel">
            <div className="bd-scene-visual">
              <img src={activeState.image} alt={`${activeState.eventTitle}場景概念圖`} />
              <div className="bd-scene-overlay" aria-hidden="true">
                <div className="bd-map-line"></div>
                <div className="bd-map-node is-complete">01</div>
                <div className="bd-map-node is-current">{String(activeState.eventNumber).padStart(2, '0')}</div>
                <div className="bd-map-node">05</div>
              </div>
            </div>
            <div className="bd-scene-copy">
              <div className="bd-kicker">事件 {activeState.eventNumber} / 5</div>
              <h2>{activeState.eventTitle}</h2>
              <p>{activeState.scene}</p>
              <div className="bd-test-focus">
                <span>驗證焦點</span>
                <strong>{activeState.testFocus}</strong>
              </div>
            </div>
          </div>

          <section className="bd-evidence-strip">
            <article>
              <span>Build 開啟</span>
              <strong>{activeState.summary.opened.length}</strong>
            </article>
            <article>
              <span>鎖定誘惑</span>
              <strong>{activeState.summary.locked.length}</strong>
            </article>
            <article>
              <span>作用中旗標</span>
              <strong>{activeState.summary.flags.length}</strong>
            </article>
          </section>

          <section className="bd-panel">
            <div className="bd-panel-heading">
              <h2>可用選項</h2>
              <span>{activeState.choices.length} 條路線可用</span>
            </div>
            <div className="bd-choice-grid">
              {activeState.choices.map((choice) => (
                <ChoiceCard key={choice.id} choice={choice} />
              ))}
            </div>
          </section>

          <section className="bd-panel">
            <div className="bd-panel-heading">
              <h2>鎖定誘惑</h2>
              <span>{activeState.lockedChoices.length} 個重玩提示</span>
            </div>
            <div className="bd-choice-grid">
              {activeState.lockedChoices.map((choice) => (
                <ChoiceCard key={choice.id} choice={choice} />
              ))}
            </div>
          </section>
        </section>

        <aside className="bd-proof-column">
          <section className="bd-panel">
            <div className="bd-panel-heading">
              <h2>資源</h2>
              <span>次要訊號</span>
            </div>
            <div className="bd-resource-grid">
              {Object.entries(activeState.resources).map(([key, value]) => (
                <div key={key} className="bd-resource">
                  <span>{RESOURCE_LABELS[key] || key}</span>
                  <strong>{value}</strong>
                </div>
              ))}
            </div>
          </section>

          <section className="bd-panel">
            <div className="bd-panel-heading">
              <h2>後果紀錄</h2>
              <span>玩家可讀</span>
            </div>
            <ul className="bd-log">
              {activeState.consequenceLog.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>

          <section className="bd-panel">
            <div className="bd-panel-heading">
              <h2>Run 摘要</h2>
              <span>除錯鏡像</span>
            </div>
            <dl className="bd-summary">
              <dt>已開啟</dt>
              <dd>{activeState.summary.opened.join(', ')}</dd>
              <dt>看見但鎖定</dt>
              <dd>{activeState.summary.locked.join(', ')}</dd>
              <dt>旗標</dt>
              <dd>{activeState.summary.flags.join(', ')}</dd>
              <dt>結局預告</dt>
              <dd>{activeState.summary.endingPreview}</dd>
            </dl>
          </section>
        </aside>
      </main>
    </div>
  );
}

export default BuildDrivenPrototype;
