# governance_tools - AI Governance Framework Tools

> Status: governance utilities are available; Ashfall Phase D is still in progress.
> Source of phase truth: root `PLAN.md` and `tasks/TASKS.md`.
> Last reviewed: 2026-03-09
> Runtime: Python 3.9+ (stdlib-first)


## å·¥å…·ä¸€è¦?

| å·¥å…· | ?Ÿèƒ½ | ä¸»è??¨é€?|
|------|------|---------|
| [memory_janitor.py](#memory_janitorpy) | è¨˜æ†¶å£“å???§?‡æ­¸æª?| ?²æ­¢ context ?è? |
| [contract_validator.py](#contract_validatorpy) | AI ?å??–å?è¦é?è­?| CI gate |
| [plan_freshness.py](#plan_freshnesspy) | PLAN.md ?°é®®åº¦æª¢??| CI gate / Git hook |
| [state_generator.py](#state_generatorpy) | .governance-state.yaml ?Ÿæ? | ?€?‹å¿«??|
| [linear_integrator.py](#linear_integratorpy) | PLAN.md ??Linear ?Œæ­¥ | ä»»å?è¿½è¹¤ |
| [notion_integrator.py](#notion_integratorpy) | PLAN.md ??Notion ?Œæ­¥ | ä»»å?è¿½è¹¤ |

---

## memory_janitor.py

è¨˜æ†¶å£“å???§å·¥å…·?‚å???`memory/` ?®é?ä¸­ç??±è??¶é?è¡Œæ•¸ï¼Œåˆ¤?·æ˜¯?¦é?è¦æ­¸æª”ã€?

**?€?‹é–¾??*:

| ?€??| è¡Œæ•¸ | è¡Œå? |
|------|------|------|
| SAFE | ??150 | ?¡é??•ä? |
| WARNING | 151??80 | è¨ˆç•«æ¸…ç? |
| CRITICAL | 181??00 | ?¡å¿«?·è? `--execute` |
| EMERGENCY | > 200 | ç«‹å³?œæ­¢ä¸¦æ??•æ•´??|

```bash
# æª¢æŸ¥?€??
python governance_tools/memory_janitor.py --check

# ?¥ç?æ­¸æ?è¨ˆç•«
python governance_tools/memory_janitor.py --plan

# ?·è?æ­¸æ?ï¼ˆcopy+pointer æ¨¡å?ï¼Œå?æª”ä???pointerï¼?
python governance_tools/memory_janitor.py --execute

# ?¥ç?æ­¸æ?ç´€??
python governance_tools/memory_janitor.py --manifest

# JSON è¼¸å‡ºï¼ˆCI/dashboard ?¨ï?
python governance_tools/memory_janitor.py --check --format json
```

**æ­¸æ?è¡Œç‚º**: `--execute` ?¡ç”¨ copy+pointer æ¨¡å? ???§å®¹è¤‡è£½??`memory/archive/`ï¼Œå?ä½ç½®?™ä? pointer ?€å¡Šï?`manifest.json` è¨˜é?æ¯æ¬¡?ä???

---

## contract_validator.py

é©—è? AI ?å??–æ˜¯?¦ç¬¦?ˆæ²»?†è?ç¯„ï?Governance Contractï¼‰ã€‚æª¢??8 å¤§æ??¸æ˜¯?¦å·²è¼‰å…¥??

```bash
# ?ºæœ¬é©—è?
python governance_tools/contract_validator.py

# ?‡å? memory ?®é?
python governance_tools/contract_validator.py --memory-root ./memory

# JSON è¼¸å‡ºï¼ˆCI ?¨ï?
python governance_tools/contract_validator.py --format json
```

**?€?ºç¢¼**:
- `0` = ?ˆè?
- `1` = ä¸å?è¦ï??‰ç¼ºå¤±é?ï¼?

---

## plan_freshness.py

æª¢æŸ¥ PLAN.md ??`?€å¾Œæ›´?°` æ¬„ä??¯å¦?¨æ??ˆæ??§ã€‚ç”¨??CI gate ??Git hook??

```bash
# ?ºæœ¬æª¢æŸ¥ï¼ˆè??–ç•¶?ç›®??PLAN.mdï¼?
python governance_tools/plan_freshness.py

# ?‡å? PLAN.md è·¯å?
python governance_tools/plan_freshness.py --file /path/to/PLAN.md

# è¦†å¯«?¾å€¼ï?å¤©ï?
python governance_tools/plan_freshness.py --threshold 14

# JSON è¼¸å‡ºï¼ˆCI ?¨ï?
python governance_tools/plan_freshness.py --format json
```

**?€?ºç¢¼**:
- `0` = FRESHï¼ˆè?ä»???thresholdï¼?
- `1` = STALEï¼ˆè?ä»?> thresholdï¼Œâ‰¤ 2?thresholdï¼?
- `2` = CRITICALï¼ˆè?ä»?> 2?thresholdï¼‰æ?æ¬„ä?ç¼ºå¤±

**PLAN.md å¿…è?æ¬„ä?**ï¼ˆblockquote ?¼å?ï¼?
```markdown
> **?€å¾Œæ›´??*: 2026-03-06
> **Owner**: GavinWu
> **Freshness**: Sprint (7d)
```

---

## state_generator.py

è®€??PLAN.md headerï¼Œç???`.governance-state.yaml` ?€?‹å¿«?§ï?ä¾?AI session ?å??–ä½¿?¨ã€?

```bash
# ?Ÿæ??€?‹å¿«??
python governance_tools/state_generator.py

# ?‡å?ä¾†æ??‡è¼¸?ºè·¯å¾?
python governance_tools/state_generator.py \
  --plan PLAN.md \
  --output .governance-state.yaml
```

**è¼¸å‡ºç¯„ä?ï¼?governance-state.yamlï¼?*:
```yaml
last_updated: "2026-03-06"
owner: "GavinWu"
freshness_policy: "Sprint (7d)"
generated_at: "2026-03-06T10:00:00"
```

---

## linear_integrator.py

å°?`memory/01_active_task.md` ä¸­ç??ªå??ä»»?™å?æ­¥åˆ° Linearï¼Œä¸¦å°?Issue ID å¯«å??¬åœ°??

**?ç½®**:
```bash
export LINEAR_API_KEY='your_linear_api_key'
```

```bash
# ?—å‡º?¯ç”¨ Teams
python governance_tools/linear_integrator.py --list-teams

# ?Œæ­¥?ªå??ä»»?™åˆ°?‡å? Team
python governance_tools/linear_integrator.py --sync --team-id <TEAM_ID>

# ?‡å??ªå?ç´šï?0=?? 1=ç·Šæ€? 2=é«? 3=ä¸? 4=ä½ï?
python governance_tools/linear_integrator.py --sync --team-id <TEAM_ID> --priority 2

# JSON è¼¸å‡ºï¼ˆCI/dashboard ?¨ï?
python governance_tools/linear_integrator.py --sync --team-id <TEAM_ID> --format json
```

**?Œæ­¥å¾?*ï¼šä»»?™å??¢æ?? ä? `[LINEAR:ENG-123]` æ¨™è?ï¼Œé˜²æ­¢é?è¤‡å»ºç«‹ã€?

**ç­–ç•¥?‡ä»¶**: [docs/linear-source-of-truth.md](../docs/linear-source-of-truth.md)

---

## notion_integrator.py

å°?`memory/01_active_task.md` ä¸­ç??ªå??ä»»?™å?æ­¥åˆ° Notion Databaseï¼Œä¸¦å°‡çŸ­ ID å¯«å??¬åœ°??

**?ç½®**:
```bash
export NOTION_API_KEY='secret_xxxx'        # Notion Integration Token
export NOTION_DATABASE_ID='<DB_ID>'        # ?¯é¸ï¼Œä??¯ç”¨ --database-id ?³å…¥
```

> ?–å? Tokenï¼šhttps://www.notion.so/my-integrations ??å»ºç? Integration
> å»ºç?å¾Œé??¨ç›®æ¨?Database ?é¢? å…¥æ­?Integrationï¼ˆå³ä¸Šè? `...` ??Add connectionsï¼?

```bash
# ?—å‡º Integration ?¯å??–ç? Database
python governance_tools/notion_integrator.py --list-databases

# ?Œæ­¥?ªå??ä»»?™åˆ°?‡å? Database
python governance_tools/notion_integrator.py --sync --database-id <DB_ID>

# JSON è¼¸å‡ºï¼ˆCI/dashboard ?¨ï?
python governance_tools/notion_integrator.py --sync --database-id <DB_ID> --format json
```

**?Œæ­¥å¾?*ï¼šä»»?™å??¢æ?? ä? `[NOTION:XXXXXXXX]` æ¨™è?ï¼? å­—å???IDï¼‰ï??²æ­¢?è?å»ºç???

**ç­–ç•¥?‡ä»¶**: [docs/notion-source-of-truth.md](../docs/notion-source-of-truth.md)

---

## ?±é€šè¨­è¨ˆå???

- **?¶ä?è³?*: ?€?‰å·¥?·å?ä½¿ç”¨ Python stdlibï¼ˆurllib?re?json?pathlibï¼?
- **?æ?è³‡è??²è­·**: linear_integrator / notion_integrator ?å‡º?æ???title/descriptionï¼Œåµæ¸¬åˆ° API key?å?ç¢¼ã€private key ?‚æ?çµ•é€å‡º
- **--format json**: ?€?‰å·¥?·æ”¯??JSON è¼¸å‡ºï¼Œå¯??CI pipeline ??dashboard
- **--help**: ?€?‰å·¥?·æ?å®Œæ•´èªªæ?ï¼ˆ`python <tool>.py --help`ï¼?
- **?¯èª¤?ç?**: API å¤±æ??‚ä?å½±éŸ¿?¬åœ°å·¥ä?æµ?

---

## CI ?´å?

`.github/workflows/governance.yml` ??`.gitlab-ci.yml` å·²æ•´?ˆä»¥ä¸‹å…©?‹è‡ª?•æª¢?¥ï?

| Job | å·¥å…· | å¤±æ?æ¢ä»¶ |
|-----|------|---------|
| `plan-freshness` | plan_freshness.py | CRITICALï¼ˆæ? pushï¼?|
| `memory-pressure` | memory_janitor.py | EMERGENCYï¼ˆadvisoryï¼Œä??‹ï? |

---

## Git Hook

```bash
# ä¸€?µå?è£ï?PLAN.md ?æ???commitï¼?
bash scripts/install-hooks.sh
```

å®‰è?å¾Œï?`git commit` ?‚è‡ª?•åŸ·è¡?`plan_freshness.py`ï¼ŒCRITICAL ?€?‹æ??‹ä? commit??
