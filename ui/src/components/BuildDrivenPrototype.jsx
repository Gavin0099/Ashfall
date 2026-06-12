import React, { useMemo, useState } from 'react';
import roadsideTrap from '../../../experiments/build_driven_slice/events/roadside_trap.json';
import lockedClinic from '../../../experiments/build_driven_slice/events/locked_clinic.json';
import infectionCheckpoint from '../../../experiments/build_driven_slice/events/infection_checkpoint.json';
import undergroundMarket from '../../../experiments/build_driven_slice/events/underground_market.json';
import vaultGate from '../../../experiments/build_driven_slice/events/vault_gate.json';
import clinicScene from '../assets/clinic-scene.svg';
import checkpointScene from '../assets/checkpoint-scene.svg';
import marketScene from '../assets/market-scene.svg';

const EVENT_PAYLOADS = [
  roadsideTrap,
  lockedClinic,
  infectionCheckpoint,
  undergroundMarket,
  vaultGate,
];

const EVENT_TITLES = {
  roadside_trap: '路邊陷阱',
  locked_clinic: '封鎖診所',
  infection_checkpoint: '感染檢查站',
  underground_market: '地下市場',
  vault_gate: '避難所閘門',
};

const EVENT_SCENES = {
  roadside_trap: '路邊的碎石底下牽著一條細線，線尾接進半埋的彈藥盒。這不是單純的陷阱，而是一種訊號。',
  locked_clinic: '診所的門卡在半開狀態，通電的磁鎖還在低鳴。窗戶裂了，但門邊控制板穿過灰塵與乾血，仍閃著微弱燈號。',
  infection_checkpoint: '兩名守衛拉著隔離繩，一台老舊掃描器不停吐出誤判。隊伍裡每個人都在盤算，自己還買得起哪一種故事。',
  underground_market: '市場藏在裂開的加油站底下。沒有人把舊幫派的名字說出口，但每個人都認得誰還背著那筆債。',
  vault_gate: '避難所閘門像一塊黑色牆面立在灰燼裡。它不問你想要什麼，只問你是誰，以及你一路留下了什麼證據。',
};

const EVENT_IMAGES = {
  roadside_trap: clinicScene,
  locked_clinic: clinicScene,
  infection_checkpoint: checkpointScene,
  underground_market: marketScene,
  vault_gate: marketScene,
};

const BUILD_PRESETS = [
  {
    id: 'vault_mechanic',
    name: '避難所技工',
    fantasy: '我比人更懂舊世界系統。',
    traits: ['mechanic', 'vault_dweller'],
    traitLabels: ['技工', '避難所居民'],
    special: { STR: 2, PER: 6, INT: 8, CHA: 2, SUR: 4 },
    resources: { hp: 18, water: 2, food: 3, ammo: 6, scrap: 2, medkits: 1 },
    finalFlags: {
      trap_disarmed: true,
      clinic_entered_safely: true,
      infection_screening_passed: true,
      guard_scanner_disabled: true,
    },
    testFocus: '技術能力應該打開乾淨進入路線，同時讓社交與暴力路線保持可見但不可用。',
  },
  {
    id: 'wasteland_grifter',
    name: '廢土騙徒',
    fantasy: '我靠讀懂人心，並比他們更會說謊活下來。',
    traits: ['liar', 'trader'],
    traitLabels: ['騙徒', '商販'],
    special: { STR: 2, PER: 4, INT: 3, CHA: 8, SUR: 3 },
    resources: { hp: 16, water: 3, food: 3, ammo: 3, scrap: 3, medkits: 0 },
    finalFlags: {
      clinic_fake_credentials: true,
      market_contact_earned: true,
      checkpoint_story_believed: true,
    },
    testFocus: '社交掩護應該把前面的假文件變成活路，同時讓技術證明與暴力暗號保持鎖定。',
  },
  {
    id: 'ex_raider',
    name: '前掠奪者',
    fantasy: '我懂暴力者怎麼思考，因為我以前就是其中之一。',
    traits: ['ex_raider', 'intimidator'],
    traitLabels: ['前掠奪者', '威嚇者'],
    special: { STR: 8, PER: 3, INT: 2, CHA: 3, SUR: 6 },
    resources: { hp: 20, water: 1, food: 3, ammo: 8, scrap: 1, medkits: 0 },
    finalFlags: {
      raider_reputation_seen: true,
      checkpoint_guard_spooked: true,
      raider_debt_called: true,
    },
    testFocus: '暴力名聲應該變成可用槓桿，同時讓技術修理與乾淨交易保持不可及。',
  },
];

const OPTION_COPY = {
  push_through_trap: {
    label: '趁沒人注意時硬闖陷阱路段',
    preview: '你穿過了路障，但付出生命與食物代價，沒有取得後續槓桿。',
  },
  detect_tripwire: {
    label: '追出絆線並解除觸發器',
    preview: '感知讓陷阱變成安全通行，也留下可被後續消耗的技術證據。',
    locked: '你看得見線，但看不出讓它保持待發的壓力點。',
  },
  turn_trap_into_warning: {
    label: '讀懂掠奪者標記，留下回應',
    preview: '你把舊幫派語言轉成之後可用的威嚇槓桿。',
    locked: '符號確實有意義，但你不知道它要求哪一種回應。',
  },
  sell_fake_safe_route: {
    label: '把陷阱包裝成假通行費路線',
    preview: '你把危險賣成保護，換到市場裡有人願意聽你的名字。',
    locked: '你看得出這能騙人，但還沒有把危險賣成保護的自信。',
  },
  force_clinic_window: {
    label: '硬撬破裂的診所窗戶',
    preview: '會損失生命，並留下強行闖入診所的後果。',
  },
  repair_clinic_door: {
    label: '修復門邊控制板',
    preview: '安全進入診所，保留補給，並為後續檢查站留下醫療憑證。',
    locked: '控制板仍有電，但這個修理超出你的訓練。',
  },
  intimidate_squatters: {
    label: '威嚇裡面的佔屋者',
    preview: '用威脅取得入口，但後續可能增加不信任。',
    locked: '你可以威脅他們，但他們不相信你真的知道怎麼把話做實。',
  },
  fake_medical_authorization: {
    label: '用偽造醫療授權通過',
    preview: '把封鎖診所轉成一張可用的社交掩護。',
    locked: '你知道這個謊可以成立，但開口時節奏已經不對。',
  },
  wait_out_screening: {
    label: '排隊等完篩檢',
    preview: '消耗食物與時間壓力，但不需要特殊能力。',
  },
  use_sterile_clinic_supplies: {
    label: '使用無菌診所補給',
    preview: '前面安全進入診所，現在變成檢查站捷徑。',
    locked: '你之前沒有乾淨進入診所，手上沒有足以說服人的醫療證明。',
  },
  talk_through_checkpoint: {
    label: '用一套說法混過檢查站',
    preview: '讓守衛相信你的故事，並留下通過檢查站的旗標。',
    locked: '守衛要的是有官方節奏的故事，而你找不到那個節奏。',
  },
  recognize_raider_scar_protocol: {
    label: '辨認掠奪者疤痕暗號',
    preview: '用暴力過去換到捷徑，但也讓權威更容易敵視你。',
    locked: '守衛身上的疤痕確實是在發問，但你不知道答案。',
  },
  buy_overpriced_pass: {
    label: '買下過度抬價的通行證',
    preview: '消耗廢料，但不產生特殊槓桿。',
  },
  forge_market_contact: {
    label: '偽造市場人脈',
    preview: '把社交能力轉成結局前的通行權。',
    locked: '你知道這是關係市場，但不知道哪些名字能安全說出口。',
  },
  repair_vendor_scanner: {
    label: '修理攤販的掃描器',
    preview: '用技術人情排除結局前的掃描障礙。',
    locked: '掃描器的故障很明顯，但修好它需要舊世界修理信心。',
  },
  call_in_raider_debt: {
    label: '討回一筆舊掠奪者人情債',
    preview: '用暴力名聲換取市場通行，但可能提高結局代價。',
    locked: '你能模仿威脅，但這裡沒有人欠你恐懼。',
  },
  force_vault_wait: {
    label: '等換班混亂時硬闖',
    preview: '用昂貴生存代價抵達避難所，而不是靠 build 槓桿。',
  },
  technical_override: {
    label: '觸發技術覆寫',
    preview: '舊世界系統因為你理解並準備過它而打開。',
    locked: '你需要技術能力，也需要前面創造過掃描器破口。',
  },
  social_bypass: {
    label: '借用身份走社交通道',
    preview: '你騙進了一個建立在信任上的系統。',
    locked: '守衛願意相信某個人，但不是現在的你。',
  },
  raider_pressure: {
    label: '讓閘門人員理解跟著你的掠奪者債',
    preview: '暴力可信度打開了閘門，也改變倖存者記住你的方式。',
    locked: '沒有被承認的歷史，威脅在閘門前只是噪音。',
  },
  medical_clearance: {
    label: '用乾淨檢疫紀錄走醫療通道',
    preview: '前面的診所與檢查站選擇創造了非暴力入口。',
    locked: '醫療通道存在，但你前面的選擇沒有留下乾淨紀錄。',
  },
};

const FLAG_LABELS = {
  trap_disarmed: '陷阱已解除',
  clinic_entered_safely: '安全進入診所',
  clinic_forced_entry: '強行闖入診所',
  clinic_fake_credentials: '偽造診所文件',
  clinic_squatters_cowed: '診所佔屋者退讓',
  market_contact_earned: '取得市場人脈',
  infection_screening_passed: '通過感染檢查',
  checkpoint_story_believed: '檢查站相信說法',
  checkpoint_guard_spooked: '守衛被舊暗號嚇退',
  raider_reputation_seen: '辨識掠奪者訊號',
  guard_scanner_disabled: '掃描器障礙已排除',
  raider_debt_called: '掠奪者人情債已啟用',
};

const REQUIREMENT_LABELS = {
  mechanic: '技工',
  vault_dweller: '避難所居民',
  liar: '騙徒',
  trader: '商販',
  ex_raider: '前掠奪者',
  intimidator: '威嚇者',
  strength: '力量',
  perception: '感知',
  intelligence: '智力',
  charisma: '魅力',
  endurance: '耐力',
  luck: '運氣',
};

const KIND_LABELS = {
  common: '共通選項',
  build_gated: 'Build 開啟',
  flag_gated: '旗標開啟',
  locked: '鎖定誘惑',
};

const RESOURCE_LABELS = {
  hp: '生命',
  water: '水',
  food: '食物',
  ammo: '彈藥',
  scrap: '廢料',
  medkits: '醫療包',
};

const ENDING_COPY = {
  vault_entry_costly_survival: {
    title: '昂貴生存',
    body: '你抵達了避難所，但靠的是等待、硬闖與消耗。這條路能活，卻沒有證明你的 build 真的改變世界。',
  },
  vault_entry_technical_success: {
    title: '技術覆寫',
    body: '你一路把舊世界系統變成槓桿。閘門不是被說服，而是被你準備好的故障紀錄打開。',
  },
  vault_entry_social_fraud: {
    title: '社交詐欺',
    body: '你借用名字、文件與關係走進避難所。這不是乾淨勝利，但它完全屬於這個 build。',
  },
  vault_entry_intimidation: {
    title: '威嚇入場',
    body: '暴力名聲替你清出通道，也讓所有倖存者記得你是怎麼進來的。',
  },
  vault_entry_medical_clearance: {
    title: '醫療通行',
    body: '前面的乾淨診所與檢疫選擇在最後變成非暴力入口。這是一條由旗標慢慢鋪出的路。',
  },
};

function eventIndex(eventId) {
  return EVENT_PAYLOADS.findIndex((event) => event.id === eventId);
}

function hasRequiredTrait(option, build) {
  const traits = option.requirements?.trait || [];
  return traits.length === 0 || traits.some((trait) => build.traits.includes(trait));
}

function hasRequiredAttribute(option, build) {
  return Object.entries(option.requirements?.attribute || {}).every(
    ([attribute, value]) => (build.special[attribute] || 0) >= value
  );
}

function hasRequiredFlags(option, runFlags) {
  return Object.entries(option.required_flags || {}).every(([flag, value]) => runFlags[flag] === value);
}

function isOptionAvailable(option, build, flags) {
  return hasRequiredTrait(option, build) && hasRequiredAttribute(option, build) && hasRequiredFlags(option, flags);
}

function formatRequirement(option) {
  const traitLabels = (option.requirements?.trait || []).map((trait) => REQUIREMENT_LABELS[trait] || trait);
  const attributeLabels = Object.entries(option.requirements?.attribute || {}).map(
    ([attribute, value]) => `${REQUIREMENT_LABELS[attribute.toLowerCase()] || attribute} ${value}+`
  );
  const flagLabels = Object.keys(option.required_flags || {}).map((flag) => FLAG_LABELS[flag] || flag);
  const labels = [...traitLabels, ...attributeLabels, ...flagLabels];
  return labels.length > 0 ? labels.map((label) => `[${label}]`).join(' ') : '';
}

function choiceKind(option, available) {
  if (!available) return 'locked';
  if (option.required_flags) return 'flag_gated';
  if (option.requirements) return 'build_gated';
  return 'common';
}

function formatFlagList(flags) {
  const entries = Object.keys(flags || {});
  return entries.length > 0 ? entries.map((flag) => FLAG_LABELS[flag] || flag).join('、') : '無';
}

function formatEffects(effects) {
  const entries = Object.entries(effects || {});
  if (entries.length === 0) return '無資源變化';
  return entries.map(([key, value]) => `${RESOURCE_LABELS[key] || key} ${value > 0 ? '+' : ''}${value}`).join('、');
}

function applyEffects(resources, effects) {
  return Object.entries(effects || {}).reduce((next, [key, value]) => ({
    ...next,
    [key]: (next[key] || 0) + value,
  }), { ...resources });
}

function toChoiceView(option, build, flags) {
  const available = isOptionAvailable(option, build, flags);
  const copy = OPTION_COPY[option.id] || {};

  return {
    id: option.id,
    label: copy.label || option.text,
    kind: choiceKind(option, available),
    requirementLabel: formatRequirement(option),
    lockedText: copy.locked || option.locked_text,
    consequencePreview: copy.preview || option.summary_consequence,
    flagsSet: option.set_flags || {},
    flagsRequired: option.required_flags || {},
    effects: option.effects || {},
    endingId: option.ending_id || '',
  };
}

function buildEventChoiceViews(build, event, flags) {
  return event.options.map((option) => toChoiceView(option, build, flags));
}

function chooseExpectedEnding(build) {
  const finaleChoices = buildEventChoiceViews(build, vaultGate, build.finalFlags);
  const availableEnding = finaleChoices.find((choice) => choice.kind !== 'common' && choice.kind !== 'locked' && choice.endingId);
  const fallbackEnding = finaleChoices.find((choice) => choice.endingId);
  return availableEnding || fallbackEnding;
}

function buildInstrumentedSummary(build) {
  const allChoices = EVENT_PAYLOADS.flatMap((event) => buildEventChoiceViews(build, event, build.finalFlags));
  const buildOptionsTaken = allChoices
    .filter((choice) => choice.kind !== 'common' && choice.kind !== 'locked')
    .map((choice) => choice.id);
  const lockedOptionsSeen = allChoices
    .filter((choice) => choice.kind === 'locked')
    .map((choice) => choice.id);
  const flagsTriggered = Array.from(new Set([
    ...Object.keys(build.finalFlags || {}),
    ...allChoices.flatMap((choice) => Object.keys(choice.flagsSet || {})),
  ]));
  const flagsConsumed = Array.from(new Set(
    allChoices.flatMap((choice) => Object.keys(choice.flagsRequired || {}))
  ));
  const ending = chooseExpectedEnding(build);

  return {
    build_id: build.id,
    buildName: build.name,
    build_options_taken: buildOptionsTaken,
    locked_options_seen: lockedOptionsSeen,
    flags_triggered: flagsTriggered,
    flags_consumed: flagsConsumed,
    ending_id: ending?.endingId || 'vault_entry_costly_survival',
    death_or_win_reason: ending?.consequencePreview || '靠昂貴生存代價抵達避難所。',
  };
}

function buildDemoRunSummary(build, choiceLog, flags, ending) {
  const buildOptionsTaken = choiceLog
    .filter((entry) => entry.kind !== 'common')
    .map((entry) => entry.choiceId);
  const lockedOptionsSeen = Array.from(new Set(choiceLog.flatMap((entry) => entry.lockedSeen)));
  const flagsTriggered = Array.from(new Set([
    ...Object.keys(flags || {}),
    ...choiceLog.flatMap((entry) => Object.keys(entry.flagsSet || {})),
  ]));
  const flagsConsumed = Array.from(new Set(choiceLog.flatMap((entry) => Object.keys(entry.flagsRequired || {}))));

  return {
    build_id: build.id,
    buildName: build.name,
    build_options_taken: buildOptionsTaken,
    locked_options_seen: lockedOptionsSeen,
    flags_triggered: flagsTriggered,
    flags_consumed: flagsConsumed,
    ending_id: ending?.endingId || 'run_in_progress',
    death_or_win_reason: ending?.reason || 'Run 尚未結束。',
  };
}

function Badge({ children, tone = 'neutral' }) {
  return <span className={`bd-badge bd-badge-${tone}`}>{children}</span>;
}

function ChoiceCard({ choice, onChoose }) {
  const isLocked = choice.kind === 'locked';
  const tone = choice.kind === 'common' ? 'neutral' : choice.kind === 'flag_gated' ? 'warning' : isLocked ? 'danger' : 'primary';
  const Wrapper = isLocked ? 'article' : 'button';

  return (
    <Wrapper
      className={`bd-choice ${!isLocked ? 'bd-choice-button' : ''} ${isLocked ? 'is-locked' : ''}`}
      disabled={!isLocked ? false : undefined}
      onClick={!isLocked ? onChoose : undefined}
      type={!isLocked ? 'button' : undefined}
    >
      <div className="bd-choice-topline">
        <Badge tone={tone}>{KIND_LABELS[choice.kind] || choice.kind}</Badge>
        {choice.requirementLabel && <span className="bd-requirement">{choice.requirementLabel}</span>}
      </div>
      <h3>{choice.label}</h3>
      <p>{isLocked ? choice.lockedText : choice.consequencePreview}</p>
      <div className="bd-choice-debug">
        <span>{choice.id}</span>
        <span>{formatEffects(choice.effects)}</span>
      </div>
    </Wrapper>
  );
}

function InstrumentedSummaryCard({ summary }) {
  return (
    <article className="bd-summary-card">
      <div className="bd-summary-card-title">
        <h3>{summary.buildName}</h3>
        <Badge tone="warning">{summary.ending_id}</Badge>
      </div>
      <dl>
        <dt>Build 選項</dt>
        <dd>{summary.build_options_taken.length > 0 ? summary.build_options_taken.join(', ') : '無'}</dd>
        <dt>鎖定誘惑</dt>
        <dd>{summary.locked_options_seen.length > 0 ? summary.locked_options_seen.join(', ') : '無'}</dd>
        <dt>觸發旗標</dt>
        <dd>{summary.flags_triggered.length > 0 ? summary.flags_triggered.join(', ') : '無'}</dd>
        <dt>消耗旗標</dt>
        <dd>{summary.flags_consumed.length > 0 ? summary.flags_consumed.join(', ') : '無'}</dd>
      </dl>
      <p>{summary.death_or_win_reason}</p>
    </article>
  );
}

function BuildDrivenPrototype({ onBack }) {
  const [selectedBuildId, setSelectedBuildId] = useState(BUILD_PRESETS[0].id);
  const [runStarted, setRunStarted] = useState(false);
  const [eventCursor, setEventCursor] = useState(0);
  const [runFlags, setRunFlags] = useState({});
  const [resources, setResources] = useState(BUILD_PRESETS[0].resources);
  const [choiceLog, setChoiceLog] = useState([]);
  const [ending, setEnding] = useState(null);

  const selectedBuild = useMemo(
    () => BUILD_PRESETS.find((build) => build.id === selectedBuildId) || BUILD_PRESETS[0],
    [selectedBuildId]
  );
  const currentEvent = EVENT_PAYLOADS[Math.min(eventCursor, EVENT_PAYLOADS.length - 1)];
  const currentChoices = useMemo(
    () => buildEventChoiceViews(selectedBuild, currentEvent, runFlags),
    [selectedBuild, currentEvent, runFlags]
  );
  const availableChoices = currentChoices.filter((choice) => choice.kind !== 'locked');
  const lockedChoices = currentChoices.filter((choice) => choice.kind === 'locked');
  const runSummary = useMemo(
    () => buildDemoRunSummary(selectedBuild, choiceLog, runFlags, ending),
    [selectedBuild, choiceLog, runFlags, ending]
  );
  const comparisonSummaries = useMemo(
    () => BUILD_PRESETS.map((build) => buildInstrumentedSummary(build)),
    []
  );
  const runComplete = Boolean(ending);

  function resetRun(nextBuild = selectedBuild) {
    setRunStarted(false);
    setEventCursor(0);
    setRunFlags({});
    setResources(nextBuild.resources);
    setChoiceLog([]);
    setEnding(null);
  }

  function selectBuild(build) {
    setSelectedBuildId(build.id);
    resetRun(build);
  }

  function startRun() {
    setRunStarted(true);
    setEventCursor(0);
    setRunFlags({});
    setResources(selectedBuild.resources);
    setChoiceLog([]);
    setEnding(null);
  }

  function handleChooseOption(choice) {
    const nextFlags = { ...runFlags, ...choice.flagsSet };
    const nextResources = applyEffects(resources, choice.effects);
    const nextEntry = {
      eventId: currentEvent.id,
      eventTitle: EVENT_TITLES[currentEvent.id] || currentEvent.id,
      choiceId: choice.id,
      choiceLabel: choice.label,
      consequence: choice.consequencePreview,
      kind: choice.kind,
      flagsSet: choice.flagsSet,
      flagsRequired: choice.flagsRequired,
      lockedSeen: lockedChoices.map((lockedChoice) => lockedChoice.id),
      effects: choice.effects,
      endingId: choice.endingId,
    };
    const nextLog = [...choiceLog, nextEntry];

    setRunFlags(nextFlags);
    setResources(nextResources);
    setChoiceLog(nextLog);

    if (eventCursor >= EVENT_PAYLOADS.length - 1) {
      setEnding({
        endingId: choice.endingId || 'vault_entry_costly_survival',
        reason: choice.consequencePreview,
      });
      return;
    }

    setEventCursor(eventCursor + 1);
  }

  const sceneTitle = EVENT_TITLES[currentEvent.id] || currentEvent.id;
  const endingCopy = ending ? ENDING_COPY[ending.endingId] || ENDING_COPY.vault_entry_costly_survival : null;

  return (
    <div className="bd-shell">
      <header className="bd-header">
        <div>
          <div className="bd-kicker">Steam Demo Web Prototype Flow</div>
          <h1>Ashfall Build 驗證台</h1>
          <p>選一個 build，走完同一條五事件路線，直接看哪些選項被打開、哪些誘惑被鎖住，以及最後的結局歸因。</p>
        </div>
        <button className="bd-back-button" onClick={onBack}>返回</button>
      </header>

      <main className="bd-workbench">
        <aside className="bd-build-rail">
          <div className="bd-rail-heading">
            <span>選擇 Build</span>
            <strong>{runStarted ? 'Run 中' : '可開始'}</strong>
          </div>
          <section className="bd-build-select" aria-label="選擇 Build">
            {BUILD_PRESETS.map((build) => (
              <button
                key={build.id}
                className={`bd-build-card ${build.id === selectedBuildId ? 'is-active' : ''}`}
                onClick={() => selectBuild(build)}
                type="button"
              >
                <span>{build.name}</span>
                <small>{build.fantasy}</small>
              </button>
            ))}
          </section>

          <section className="bd-panel bd-identity-panel">
            <div className="bd-panel-heading">
              <h2>身分</h2>
              <Badge tone="primary">{selectedBuild.id}</Badge>
            </div>
            <p className="bd-build-fantasy">{selectedBuild.fantasy}</p>
            <div className="bd-stat-grid">
              {Object.entries(selectedBuild.special).map(([key, value]) => (
                <div key={key} className="bd-stat">
                  <span>{key}</span>
                  <strong>{value}</strong>
                </div>
              ))}
            </div>
            <div className="bd-traits">
              {selectedBuild.traitLabels.map((trait) => (
                <Badge key={trait} tone="neutral">{trait}</Badge>
              ))}
            </div>
          </section>

          <section className="bd-panel">
            <div className="bd-panel-heading">
              <h2>Run 路徑</h2>
              <span>{runComplete ? '已完成' : `${eventCursor + 1} / ${EVENT_PAYLOADS.length}`}</span>
            </div>
            <ol className="bd-timeline">
              {EVENT_PAYLOADS.map((event, index) => {
                const isCurrent = runStarted && !runComplete && index === eventCursor;
                const isComplete = index < choiceLog.length;
                return (
                  <li key={event.id} className={`${isCurrent ? 'is-current' : ''} ${isComplete ? 'is-complete' : ''}`}>
                    <span>{index + 1}</span>
                    <div>
                      <strong>{EVENT_TITLES[event.id] || event.id}</strong>
                      <small>{isComplete ? '已選擇' : isCurrent ? '目前事件' : '尚未抵達'}</small>
                    </div>
                  </li>
                );
              })}
            </ol>
          </section>
        </aside>

        <section className="bd-event-column">
          {!runStarted && (
            <section className="bd-demo-start bd-panel">
              <div className="bd-kicker">Demo Start</div>
              <h2>同一條路，先選你要怎麼活。</h2>
              <p>{selectedBuild.name}：{selectedBuild.fantasy}</p>
              <div className="bd-start-actions">
                <button className="bd-primary-action" onClick={startRun} type="button">開始 Steam Demo Flow</button>
                <span>約 5 個事件，適合 PC/Web 原型驗證。</span>
              </div>
            </section>
          )}

          {runStarted && !runComplete && (
            <>
              <div className="bd-scene-panel">
                <div className="bd-scene-visual">
                  <img src={EVENT_IMAGES[currentEvent.id] || clinicScene} alt={`${sceneTitle}場景概念圖`} />
                  <div className="bd-scene-overlay" aria-hidden="true">
                    <div className="bd-map-line"></div>
                    <div className="bd-map-node is-complete">01</div>
                    <div className="bd-map-node is-current">{String(eventCursor + 1).padStart(2, '0')}</div>
                    <div className="bd-map-node">05</div>
                  </div>
                </div>
                <div className="bd-scene-copy">
                  <div className="bd-kicker">事件 {eventCursor + 1} / {EVENT_PAYLOADS.length}</div>
                  <h2>{sceneTitle}</h2>
                  <p>{EVENT_SCENES[currentEvent.id] || currentEvent.description}</p>
                  <div className="bd-test-focus">
                    <span>驗證焦點</span>
                    <strong>{selectedBuild.testFocus}</strong>
                  </div>
                </div>
              </div>

              <section className="bd-evidence-strip">
                <article>
                  <span>可用路線</span>
                  <strong>{availableChoices.length}</strong>
                </article>
                <article>
                  <span>鎖定誘惑</span>
                  <strong>{lockedChoices.length}</strong>
                </article>
                <article>
                  <span>已觸發旗標</span>
                  <strong>{Object.keys(runFlags).length}</strong>
                </article>
              </section>

              <section className="bd-panel">
                <div className="bd-panel-heading">
                  <h2>可用選項</h2>
                  <span>點選後進入下一事件</span>
                </div>
                <div className="bd-choice-grid">
                  {availableChoices.map((choice) => (
                    <ChoiceCard key={choice.id} choice={choice} onChoose={() => handleChooseOption(choice)} />
                  ))}
                </div>
              </section>

              <section className="bd-panel">
                <div className="bd-panel-heading">
                  <h2>鎖定誘惑</h2>
                  <span>{lockedChoices.length} 個重玩提示</span>
                </div>
                <div className="bd-choice-grid">
                  {lockedChoices.map((choice) => (
                    <ChoiceCard key={choice.id} choice={choice} />
                  ))}
                </div>
              </section>
            </>
          )}

          {runComplete && (
            <section className="bd-ending-panel">
              <div className="bd-kicker">Demo Ending</div>
              <h2>{endingCopy.title}</h2>
              <p>{endingCopy.body}</p>
              <div className="bd-ending-id">{ending.endingId}</div>
              <div className="bd-start-actions">
                <button className="bd-primary-action" onClick={startRun} type="button">用同一 Build 重跑</button>
                <button className="bd-secondary-action" onClick={() => resetRun()} type="button">回到選 Build</button>
              </div>
            </section>
          )}
        </section>

        <aside className="bd-proof-column">
          <section className="bd-panel">
            <div className="bd-panel-heading">
              <h2>資源</h2>
              <span>Run 狀態</span>
            </div>
            <div className="bd-resource-grid">
              {Object.entries(resources).map(([key, value]) => (
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
              {choiceLog.length === 0 && <li>尚未做出選擇。</li>}
              {choiceLog.map((item) => (
                <li key={`${item.eventId}-${item.choiceId}`}>
                  <strong>{item.eventTitle}</strong>：{item.choiceLabel}。{item.consequence}
                </li>
              ))}
            </ul>
          </section>

          <section className="bd-panel">
            <div className="bd-panel-heading">
              <h2>Machine Summary</h2>
              <span>目前 run</span>
            </div>
            <dl className="bd-summary">
              <dt>build_id</dt>
              <dd>{runSummary.build_id}</dd>
              <dt>build_options_taken</dt>
              <dd>{runSummary.build_options_taken.join(', ') || '無'}</dd>
              <dt>locked_options_seen</dt>
              <dd>{runSummary.locked_options_seen.join(', ') || '無'}</dd>
              <dt>flags_triggered</dt>
              <dd>{runSummary.flags_triggered.join(', ') || '無'}</dd>
              <dt>flags_consumed</dt>
              <dd>{runSummary.flags_consumed.join(', ') || '無'}</dd>
              <dt>ending_id</dt>
              <dd>{runSummary.ending_id}</dd>
            </dl>
          </section>
        </aside>

        <section className="bd-compare-row">
          <div className="bd-panel-heading">
            <h2>三 Build Instrumented Summary</h2>
            <span>比較 opened / locked / flags / ending</span>
          </div>
          <div className="bd-comparison-grid">
            {comparisonSummaries.map((summary) => (
              <InstrumentedSummaryCard key={summary.build_id} summary={summary} />
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}

export default BuildDrivenPrototype;
