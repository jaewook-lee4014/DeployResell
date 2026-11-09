// Index.html 스크립트를 가짜 DOM 에서 실행하고 renderSrc 결과 HTML 을 확인한다
const fs = require('fs');
const vm = require('vm');
const html = fs.readFileSync(process.argv[2], 'utf8');
const code = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).join('\n');

const els = {};
const stub = () => new Proxy(function () {}, {
  get: (t, k) => k === Symbol.toPrimitive ? () => '' : k in t ? t[k] : (t[k] = stub()),
  set: (t, k, v) => (t[k] = v, true),
  apply: () => stub(),
});
const el = id => els[id] || (els[id] = Object.assign(stub(), { innerHTML: '', textContent: '', value: '', hidden: false, dataset: {} }));
const document = { getElementById: el, querySelectorAll: () => [], querySelector: () => null, documentElement: stub(), addEventListener() {}, hidden: false };
const ctx = { document, window: {}, localStorage: { getItem: () => null, setItem() {}, removeItem() {} }, getComputedStyle: () => ({ getPropertyValue: () => '' }),
  setInterval() {}, setTimeout() {}, clearTimeout() {}, Chart: stub(), google: { script: { run: stub() } }, location: stub(), matchMedia: () => ({ matches: false, addEventListener() {} }),
  console, Date, Math, JSON, encodeURIComponent, Object, String, Number, Array, Promise, isFinite, URLSearchParams, navigator: {} };
vm.createContext(ctx);
vm.runInContext(code + '\n;globalThis.__t={S,renderSrc,set tab(v){tab=v}};', ctx);
const T = ctx.__t;
const now = new Date().toISOString();
T.S.src = { status: { at: now, nextAt: now, error: '' }, noCatalog: 1, items: [
  { articleId: '1', postedAt: now, mall: '쿠팡', name: '빼빼로 <b>48개</b>', dealPrice: 38300, dealPriceNorm: 7979, catTitle: '빼빼로 10개', catPrice: 12180, reviews: 18762, near: 1, offers: 2, matchConf: '보통', stars: 4, points: 4,
    rules: [{ rule: '최저가보다 싸다', ok: true, pts: 2, why: 'a' }, { rule: '역대 최저가 수준', ok: null, pts: 0, why: '기록 없음' }], catLink: 'https://x/catalog/1', articleUrl: 'https://cafe/1' },
  { articleId: '2', postedAt: now, mall: '', name: '크리넥스', dealPrice: 21400, dealPriceNorm: 21400, catTitle: 'c', catPrice: 14530, reviews: 10, near: 1, offers: 1, matchConf: '낮음', stars: 1, points: 1,
    rules: [], catLink: 'https://x/catalog/2', articleUrl: 'https://cafe/2', exact: { near: 4, offers: 9 } },
] };
T.S.srcMin = 3;
T.renderSrc();
const out = els.srcList.innerHTML;
let fail = 0;
const ok = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fail++; };
ok(out.includes('★★★★☆') && out.includes('빼빼로 &lt;b&gt;48개'), '★4 카드 표시 + 상품명 이스케이프');
ok(!out.includes('크리넥스'), '★3 이상 필터로 ★1 숨김');
ok(out.includes('34% 쌈') && out.includes('환산 7,979'), '환산가와 할인율');
ok(els.srcFilter.innerHTML.includes('★3 이상') && els.srcUpdated.innerHTML.includes('마지막 확인'), '필터와 상태줄');
T.S.srcMin = 1; T.renderSrc();
const all = els.srcList.innerHTML;
ok(all.includes('크리넥스') && all.includes('매칭 낮음') && all.includes('실제</span> 근처 4곳'), '전체 보기: 매칭 낮음 태그, 실제 경쟁도 태그');
ok(all.includes('47% 비쌈'), '최저가보다 비싸면 비쌈 표시');
process.exit(fail ? 1 : 0);
