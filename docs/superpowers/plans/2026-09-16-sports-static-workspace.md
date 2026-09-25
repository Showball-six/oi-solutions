# Sports Static Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone static sports workspace that scales source-backed fat-loss meals by bodyweight and presents a three-way training plan with animated exercise diagrams and safety cues.

**Architecture:** `sports/index.html` is a no-framework ES module page. `sports/app.js` exports deterministic calculation helpers for Node tests and initializes browser rendering by fetching two JSON data files. Nutrition and training source content stay in `sports/data/`, while original SVG/CSS animations render from per-exercise parameters instead of copied video media.

**Tech Stack:** HTML5, CSS3, vanilla JavaScript ES modules, JSON, Node built-in test runner.

**Spec:** `docs/superpowers/specs/2026-09-16-sports-static-workspace-design.md`

## Global Constraints

- Keep the project completely inside `sports/`; do not edit OI-site entry points, shared assets, or existing data.
- Do not add a framework, backend, account system, persistence layer, tracking feature, or external media dependency.
- Use only source-backed automatic conversion rules for the fat-loss goal; gain and maintenance are browse-only categories with an explicit unavailable-rule state.
- Use original SVG movement diagrams and source links, never downloaded or embedded Bilibili footage.
- Show all recorded food quantities as raw/pre-cooking weights and label the 85 kg / male / 2–3 hour weekly activity limits of the meal scaling example.
- Respect keyboard navigation and `prefers-reduced-motion`; all non-decorative controls need visible labels and focus states.

---

### Task 1: Build and test calculation primitives

**Files:**
- Create: `sports/package.json`
- Create: `sports/tests/app.test.mjs`
- Create: `sports/app.js`

**Interfaces:**
- Produces: `normalizeWeight(value: unknown): number`, `calculateTargets(rule: MacroRule, weightKg: unknown): MacroTargets`, `scaleRawWeight(baseGrams: number, weightKg: unknown): number`.
- `MacroRule` shape: `{ carbs: number, protein: number, fat: number }` with all values in g/kg.
- `MacroTargets` shape: `{ weightKg: number, carbs: number, protein: number, fat: number }`, with macro outputs rounded to one decimal.

- [ ] **Step 1: Create the test runner definition**

Create `sports/package.json`:

```json
{
  "name": "sports-static-workspace",
  "private": true,
  "type": "module",
  "scripts": {
    "test": "node --test tests/*.test.mjs"
  }
}
```

- [ ] **Step 2: Write failing calculation tests**

Create `sports/tests/app.test.mjs`:

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { calculateTargets, normalizeWeight, scaleRawWeight } from '../app.js';

const maleLowActivity = { carbs: 2.2, protein: 1.4, fat: 0.8 };
const femaleHighActivity = { carbs: 3, protein: 1.8, fat: 1.2 };

test('calculates 85 kg male low-activity targets from the source rule', () => {
  assert.deepEqual(calculateTargets(maleLowActivity, 85), {
    weightKg: 85, carbs: 187, protein: 119, fat: 68
  });
});

test('calculates the female high-activity target and rounds one decimal', () => {
  assert.deepEqual(calculateTargets(femaleHighActivity, 62.5), {
    weightKg: 62.5, carbs: 187.5, protein: 112.5, fat: 75
  });
});

test('clamps invalid bodyweights and scales raw ingredients from the 85 kg baseline', () => {
  assert.equal(normalizeWeight('invalid'), 65);
  assert.equal(normalizeWeight(12), 30);
  assert.equal(normalizeWeight(300), 250);
  assert.equal(scaleRawWeight(93, 85), 93);
  assert.equal(scaleRawWeight(93, 62.5), 68.4);
});
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `npm test` from `sports/`.

Expected: FAIL with `ERR_MODULE_NOT_FOUND` for `sports/app.js`.

- [ ] **Step 4: Implement the pure helper exports**

Start `sports/app.js` with these exports before adding browser-only code:

```js
export function normalizeWeight(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return 65;
  return Math.min(250, Math.max(30, numeric));
}

const oneDecimal = value => Math.round(value * 10) / 10;

export function calculateTargets(rule, weightKg) {
  const weight = normalizeWeight(weightKg);
  return {
    weightKg: weight,
    carbs: oneDecimal(weight * rule.carbs),
    protein: oneDecimal(weight * rule.protein),
    fat: oneDecimal(weight * rule.fat)
  };
}

export function scaleRawWeight(baseGrams, weightKg) {
  return oneDecimal(Number(baseGrams) * normalizeWeight(weightKg) / 85);
}
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `npm test` from `sports/`.

Expected: PASS with three passing subtests.

- [ ] **Step 6: Commit the testable calculation foundation**

```powershell
git add sports/package.json sports/tests/app.test.mjs sports/app.js
git commit -m "feat: add sports calculation helpers"
```

### Task 2: Add source-backed nutrition and training JSON

**Files:**
- Create: `sports/data/nutrition.json`
- Create: `sports/data/training.json`
- Modify: `sports/tests/app.test.mjs`

**Interfaces:**
- Consumes: `calculateTargets()` and `scaleRawWeight()` from Task 1.
- Produces: `nutrition.json.rules.fatLoss[sex][activityBand]` entries and `training.json.days` with exactly `push`, `pull`, `legs` keys.

- [ ] **Step 1: Add failing data-integrity tests**

Append to `sports/tests/app.test.mjs`:

```js
import { readFile } from 'node:fs/promises';

const loadJson = name => readFile(new URL(`../data/${name}`, import.meta.url), 'utf8').then(JSON.parse);

test('nutrition data preserves all eight video-backed fat-loss rules', async () => {
  const nutrition = await loadJson('nutrition.json');
  assert.deepEqual(nutrition.rules.fatLoss.male['2-3'], maleLowActivity);
  assert.deepEqual(nutrition.rules.fatLoss.female['8-9'], femaleHighActivity);
  assert.equal(nutrition.meals.length, 3);
  assert.equal(nutrition.meals.find(meal => meal.id === 'lunch').ingredients[0].baseRawGrams, 93);
});

test('training data has three days and five source-backed actions per day', async () => {
  const training = await loadJson('training.json');
  assert.deepEqual(training.days.map(day => day.id), ['push', 'pull', 'legs']);
  assert.ok(training.days.every(day => day.exercises.length === 5));
  assert.ok(training.days.flatMap(day => day.exercises).every(exercise =>
    exercise.cues.length > 0 && exercise.animation?.path?.length > 1 && exercise.sourceUrl.includes('bilibili.com')
  ));
});
```

- [ ] **Step 2: Run the data tests to verify they fail**

Run: `npm test` from `sports/`.

Expected: FAIL because `sports/data/nutrition.json` and `sports/data/training.json` do not exist.

- [ ] **Step 3: Implement nutrition data with no invented formulas**

Create `sports/data/nutrition.json` with the following required structure and exact source coefficients:

```json
{
  "goals": ["fat-loss", "muscle-gain", "maintenance"],
  "rules": {
    "fatLoss": {
      "male": {
        "2-3": { "carbs": 2.2, "protein": 1.4, "fat": 0.8 },
        "4-5": { "carbs": 2.5, "protein": 1.6, "fat": 0.9 },
        "6-7": { "carbs": 3, "protein": 1.7, "fat": 1 },
        "8-9": { "carbs": 3.5, "protein": 1.8, "fat": 1 }
      },
      "female": {
        "2-3": { "carbs": 2, "protein": 1.4, "fat": 1 },
        "4-5": { "carbs": 2.2, "protein": 1.6, "fat": 1 },
        "6-7": { "carbs": 2.5, "protein": 1.7, "fat": 1.1 },
        "8-9": { "carbs": 3, "protein": 1.8, "fat": 1.2 }
      }
    }
  },
  "meals": [
    { "id": "breakfast", "label": "早餐", "ingredients": [{ "name": "燕麦", "baseRawGrams": 70, "scaleWithWeight": true }, { "name": "全蛋", "baseCount": 3, "scaleWithWeight": false }, { "name": "南瓜子", "baseRawGrams": 15, "scaleWithWeight": true }, { "name": "蓝莓", "baseRawGrams": 100, "scaleWithWeight": true }] },
    { "id": "lunch", "label": "午餐", "ingredients": [{ "name": "生米", "baseRawGrams": 93, "scaleWithWeight": true }, { "name": "鱼类 / 去皮鸡腿 / 鸡胸 / 虾仁", "baseRawGrams": 180, "scaleWithWeight": true }, { "name": "烹饪用油", "baseRawGrams": 25, "scaleWithWeight": true }, { "name": "蔬菜", "baseRangeGrams": [200, 300], "scaleWithWeight": true }] },
    { "id": "dinner", "label": "晚餐", "ingredients": [{ "name": "红薯 / 紫薯 / 土豆 / 贝贝南瓜", "baseRawGrams": 300, "scaleWithWeight": true }, { "name": "瘦牛肉", "baseRawGrams": 180, "scaleWithWeight": true }, { "name": "油", "baseRawGrams": 25, "scaleWithWeight": true }, { "name": "坚果", "baseRawGrams": 20, "scaleWithWeight": true }, { "name": "蔬菜", "baseRangeGrams": [200, 300], "scaleWithWeight": true }] }
  ]
}
```

Add a top-level `mealScalingNote` stating that this is the 85 kg male / 2–3 weekly-hour example and must not be presented as a universal meal allocation.

- [ ] **Step 4: Implement all fifteen training records**

Create `sports/data/training.json` with day ids `push`, `pull`, `legs`; each day uses the source URL `https://www.bilibili.com/video/BV17ooLBUEqS/`. Include the exact exercise names below, a concise `focus`, `prescription`, `effort`, at least two source-backed `cues`, a `warnings` string, `substitution` string (or `null`), and animation data in the form `{ "path": "vertical|diagonal|hinge|arc", "tempo": "slow|steady" }`.

```text
push: 杠铃卧推; 上斜哑铃卧推; 双杠臂屈伸; 仰卧杠铃臂屈伸; Y 姿侧平举
pull: 单臂绳索下拉; 对握下拉; 单臂器械划船; 坐姿开肘划船; 绳索弯举
legs: 单腿硬拉; 保加利亚分腿蹲; 颈前深蹲; 罗马尼亚硬拉; 山羊挺身
```

Use the prescriptions, RPE/RIR guidance, substitutions and cues transcribed in `sports/references/2026-09-16-三分化训练摘要.md`; do not add unsupported load targets, medical claims or additional movements.

- [ ] **Step 5: Run the full data test suite**

Run: `npm test` from `sports/`.

Expected: PASS with five passing subtests.

- [ ] **Step 6: Commit source-backed JSON**

```powershell
git add sports/data/nutrition.json sports/data/training.json sports/tests/app.test.mjs
git commit -m "feat: add sports nutrition and training data"
```

### Task 3: Create the standalone accessible interface and visual system

**Files:**
- Create: `sports/index.html`
- Create: `sports/styles.css`
- Create: `sports/tests/markup.test.mjs`

**Interfaces:**
- Consumes: `#goal-tabs`, `#sex-select`, `#weight-input`, `#activity-select`, `#macro-results`, `#meal-grid`, `#training-tabs`, and `#training-content` selectors from HTML.
- Produces: semantic regions and stable element ids consumed by the browser initializer in Task 4.

- [ ] **Step 1: Write a failing markup-contract test**

Create `sports/tests/markup.test.mjs`:

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('sports page exposes all renderer mount points and accessible controls', async () => {
  const html = await readFile(new URL('../index.html', import.meta.url), 'utf8');
  for (const id of ['goal-tabs', 'sex-select', 'weight-input', 'activity-select', 'macro-results', 'meal-grid', 'training-tabs', 'training-content']) {
    assert.match(html, new RegExp(`id=["']${id}["']`));
  }
  assert.match(html, /aria-live=["']polite["']/);
  assert.match(html, /type=["']module["'] src=["']app\.js["']/);
});
```

- [ ] **Step 2: Run the markup test to verify it fails**

Run: `npm test` from `sports/`.

Expected: FAIL because `sports/index.html` does not exist.

- [ ] **Step 3: Implement semantic page structure**

Create `sports/index.html` with a `main` element containing these regions in order: introductory hero and safety note; goal tab buttons; a labelled calculator `section`; live macro result container with `aria-live="polite"`; three-meal grid; three training-day tab buttons; training renderer container. Use `button` elements for tabs and action disclosure, `label` elements for every input, and a visibly named source link in the footer. Add `<link rel="stylesheet" href="styles.css">` and `<script type="module" src="app.js"></script>`.

- [ ] **Step 4: Implement the independent dark training-log visual system**

Create `sports/styles.css` with custom properties for the specified warm-gray background, graphite surfaces, off-white text, and lime accent. Define responsive grids that collapse from three columns to one below 720 px. Implement distinct color custom properties for `data-day="push"`, `data-day="pull"`, and `data-day="legs"`.

Define `.movement-diagram` as a self-contained SVG card with a dashed path and `.motion-marker`; animate only the marker with `@keyframes motion-travel`. Add:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; scroll-behavior: auto !important; }
}
```

Add clear `:focus-visible` outlines, button pressed/selected states, readable error cards, and a no-JavaScript message.

- [ ] **Step 5: Run markup tests and inspect the static page contract**

Run: `npm test` from `sports/`.

Expected: PASS with six passing subtests.

- [ ] **Step 6: Commit the standalone interface shell**

```powershell
git add sports/index.html sports/styles.css sports/tests/markup.test.mjs
git commit -m "feat: add sports workspace interface"
```

### Task 4: Wire JSON rendering, interaction, movement diagrams, and error states

**Files:**
- Modify: `sports/app.js`
- Modify: `sports/tests/app.test.mjs`

**Interfaces:**
- Consumes: JSON schemas from Task 2 and mounts from Task 3.
- Produces: `renderNutrition(nutrition, state)`, `renderMeals(nutrition, weightKg)`, `renderTrainingDay(day)`, `renderExerciseAnimation(animation, label)`, `showLoadError(message)`, and browser-only `init()`.

- [ ] **Step 1: Add failing renderer-helper tests**

Append this test to `sports/tests/app.test.mjs` after exporting the helper:

```js
import { formatScaledIngredient } from '../app.js';

test('formats scaled raw-weight ingredients and fixed egg counts without false precision', () => {
  assert.equal(formatScaledIngredient({ name: '生米', baseRawGrams: 93, scaleWithWeight: true }, 62.5), '68.4 g 生重');
  assert.equal(formatScaledIngredient({ name: '全蛋', baseCount: 3, scaleWithWeight: false }, 62.5), '3 个');
  assert.equal(formatScaledIngredient({ name: '蔬菜', baseRangeGrams: [200, 300], scaleWithWeight: true }, 85), '200–300 g 生重');
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm test` from `sports/`.

Expected: FAIL because `formatScaledIngredient` is not exported.

- [ ] **Step 3: Implement the minimal formatting helper**

Add this export to `sports/app.js`:

```js
export function formatScaledIngredient(ingredient, weightKg) {
  if (ingredient.baseCount != null) return `${ingredient.baseCount} 个`;
  if (ingredient.baseRangeGrams) {
    const [min, max] = ingredient.baseRangeGrams.map(value => scaleRawWeight(value, weightKg));
    return `${min}–${max} g 生重`;
  }
  const grams = ingredient.scaleWithWeight ? scaleRawWeight(ingredient.baseRawGrams, weightKg) : ingredient.baseRawGrams;
  return `${grams} g 生重`;
}
```

- [ ] **Step 4: Implement browser initialization and renderers**

In `init()`, fetch both `data/nutrition.json` and `data/training.json` with `Promise.all`. Keep state as `{ goal: 'fat-loss', sex: 'male', weightKg: 85, activityBand: '2-3', day: 'push' }`. On every input or tab click, call the nutrition, meal and training renderers.

`renderNutrition()` must call `calculateTargets()` only when `state.goal === 'fat-loss'`; otherwise replace macro cards with the exact copy `该目标暂无来源支持的自动换算规则。`.

`renderMeals()` must render the 85 kg context note plus all three meals using `formatScaledIngredient()`. `renderTrainingDay()` must create an expandable `<details>` card per action; its summary contains name, focus and prescription. Expanded content includes an SVG returned by `renderExerciseAnimation()`, cues, warning, substitution when non-null, and `<a target="_blank" rel="noreferrer">查看来源视频</a>`.

`renderExerciseAnimation()` must output original inline SVG only: a head/body/limb stick figure plus an `aria-hidden="true"` path whose CSS class comes from `animation.path`. Set the surrounding figure `role="img"` and `aria-label` to `${label} 的运动方向示意`.

If either fetch fails, call `showLoadError('训练数据暂时无法加载，请通过 HTTP 本地服务器或静态站点打开此页面后重试。')` and leave no interactive result values visible.

- [ ] **Step 5: Run automated tests**

Run: `npm test` from `sports/`.

Expected: PASS with seven passing subtests.

- [ ] **Step 6: Perform browser verification over HTTP**

Run: `python -m http.server 4173 --directory sports` from the repository root, then open `http://localhost:4173`.

Verify all of the following:

1. 85 kg / male / 2–3 hours renders 187 g carbohydrate, 119 g protein and 68 g fat.
2. Changing to 62.5 kg scales raw rice from 93 g to 68.4 g.
3. Switching goal to muscle gain or maintenance removes macro output and shows the unavailable-rule copy.
4. Each of push, pull and legs displays five expandable actions with a movement diagram, cues and a source link.
5. At 390 px wide, cards are one column and no horizontal scroll appears.
6. Keyboard Tab reaches every control; opening a detail card works with Enter/Space; reduced-motion mode leaves diagrams static.

- [ ] **Step 7: Commit the functional static workspace**

```powershell
git add sports/app.js sports/tests/app.test.mjs
git commit -m "feat: render sports nutrition and training workspace"
```

### Task 5: Add maintainer documentation and final validation

**Files:**
- Create: `sports/README.md`
- Modify: `sports/index.html` only if browser review uncovers an accessibility or layout defect.
- Modify: `sports/styles.css` only if browser review uncovers an accessibility or layout defect.
- Modify: `sports/app.js` only if browser review uncovers a data, interaction or error-state defect.

**Interfaces:**
- Consumes: complete static workspace from Tasks 1–4.
- Produces: reproducible local preview directions and JSON maintenance rules.

- [ ] **Step 1: Write README content**

Create `sports/README.md` with: HTTP preview command `python -m http.server 4173 --directory sports`; test command `npm test` from `sports/`; the two JSON file responsibilities; supported goals; explicit restriction that only fat loss has source-backed conversion; raw-weight/85 kg scaling limitation; and a reminder to update both JSON and reference notes when replacing a source plan.

- [ ] **Step 2: Run final automated validation**

Run: `npm test` from `sports/`.

Expected: PASS with all tests passing.

- [ ] **Step 3: Run final repository-scope checks**

Run: `git diff --check` and `git status --short` from the repository root.

Expected: no whitespace errors; only files named in this plan are new or modified by this work, while pre-existing `memos/lec-*.html` changes and `AGENTS.md` remain untouched.

- [ ] **Step 4: Commit maintainer documentation**

```powershell
git add sports/README.md
git commit -m "docs: explain sports workspace maintenance"
```
