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
vm.runInContext(code + '\n;globalThis.__t={S,renderSrc,renderShots,set tab(v){tab=v},set shotIt(v){shotIt=v},set shotKind(v){shotKind=v}};', ctx);
const T = ctx.__t;
const now = new Date().toISOString();
T.S.src = { status: { at: now, nextAt: now, error: '' }, noCatalog: 1, items: [
  { articleId: '1', postedAt: now, mall: '쿠팡', name: '빼빼로 <b>48개</b>', dealPrice: 38300, dealPriceNorm: 7979, catTitle: '빼빼로 10개', catPrice: 12180, reviews: 18762, near: 1, offers: 2, matchConf: '보통', stars: 4, points: 4,
    rules: [{ rule: '최저가보다 싸다', ok: true, pts: 2, why: 'a' }, { rule: '역대 최저가 수준', ok: null, pts: 0, why: '기록 없음' }], catLink: 'https://x/catalog/1', articleUrl: 'https://cafe/1' },
  { articleId: '2', postedAt: now, mall: '', name: '크리넥스', dealPrice: 21400, dealPriceNorm: 21400, catTitle: 'c', catPrice: 14530, reviews: 10, near: 1, offers: 1, matchConf: '낮음', stars: 1, points: 1,
    rules: [], catLink: 'https://x/catalog/2', articleUrl: 'https://cafe/2', exact: { near: 4, offers: 9 } },
] };
T.S.srcStar = null; T.renderSrc();  // 처음엔 카드가 있는 가장 높은 별(★4)
const out = els.srcList.innerHTML;
let fail = 0;
const ok = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fail++; };
const cards = h => (h.match(/<article class="si c"/g) || []).length;
// 1) 기본 목록: 예시 카드가 맨 위, 그 아래 간결 카드
ok(out.indexOf('(예시) 카드 읽는 법') === out.indexOf('<details class="si ex"') + out.slice(out.indexOf('<details class="si ex"')).indexOf('(예시)') && out.indexOf('si ex') < out.indexOf('si c'), '예시 카드가 맨 위');
ok(out.includes('★★★★☆') && out.includes('빼빼로 &lt;b&gt;48개'), '★4 카드 + 상품명 이스케이프');
ok(cards(out) === 1 && !out.includes('크리넥스') && T.S.srcStar === 4, '처음엔 가장 높은 별(★4)만, ★1 숨김');
ok([5,4,3,2,1,0].every(n => els.srcFilter.innerHTML.includes(`aria-label="별 ${n}개"><span class="stb">${'★'.repeat(n)}<span class="off">${'☆'.repeat(5-n)}</span>`)) && !els.srcFilter.innerHTML.includes('이상'), '별 버튼: 실제 별 5~0개 그림 (이상 아님)');
ok(out.includes('<b>34%</b> 저렴') && out.includes('7,979 / 12,180'), '할인율 칩에 환산가/최저가 한 번만');
ok(out.includes('역대최저 –') && out.includes('리뷰 <b>18,762</b>') && out.includes('경쟁 <b>1/2</b>'), '역대최저·경쟁·리뷰 칩');
ok(out.includes('chip y') && out.includes('chip na') && out.includes('매칭주의') && !out.includes('매칭 보통'), '칩 색(받음/판단불가)과 매칭주의 표시');
ok(out.includes('data-ex="keep"') && out.includes('data-ex="exclude"'), '목록 카드에 [보관함] [쓰레기통]');
ok(!/핫딜 <b>|최저가 <b>/.test(out.split('si c')[1]), '간결 카드에 예전 가격 줄 중복 없음');
T.S.srcStar = 1; T.renderSrc();
const all = els.srcList.innerHTML;
ok(!all.includes('빼빼로') && all.includes('크리넥스') && all.includes('<b>47%</b> 비쌈') && all.includes('경쟁 <b>4/9</b> <span class="sm">실제'), '★1 만: ★4 안 겹침 + 비쌈 표시 + 실제 경쟁도');

// 2) 같은 카탈로그 글은 카드 하나로
T.S.src.items.push({ ...T.S.src.items[0], articleId: '5', dealPrice: 39000, stars: 3, postedAt: new Date(Date.now() - 3600e3).toISOString(), nvMid: undefined });
T.S.src.items.forEach(i => { i.nvMid = i.articleId === '2' ? '222' : '111'; });
T.S.srcStar = 4; T.renderSrc();
ok(cards(els.srcList.innerHTML) === 1 && els.srcList.innerHTML.includes('글 2개') && els.srcFilter.innerHTML.includes('★★★<span class="off">☆☆</span></span> <span class="muted">0'), '중복 글 합치기 (글 2개, ★3 글은 대표에 묻힘)');

// 3) 보관함 / 쓰레기통 (음식 자동 제외 포함)
T.S.src.items.push({ articleId: '3', nvMid: '333', postedAt: now, mall: '', name: '한우 등심', dealPrice: 30000, dealPriceNorm: 30000, catTitle: '한우', catPrice: 50000, reviews: 900, near: 1, offers: 1,
  matchConf: '높음', stars: 5, points: 6, rules: [], catLink: 'https://x/catalog/3', articleUrl: 'u', autoExclude: true, excluded: true, excludeWhy: "상품명 '한우' (정육)", manual: null });
T.S.src.items.find(i => i.articleId === '2').manual = { state: 'keep', who: 'mk', at: now };
T.S.srcView = 'list'; T.renderSrc();
const f = els.srcFilter.innerHTML;
ok(f.includes('보관함 <span class="muted">1') && f.includes('쓰레기통 <span class="muted">1') && f.includes('★★★★<span class="off">☆</span></span> <span class="muted">1') && f.includes('★★★★★<span class="off"></span></span> <span class="muted">0'), '탭 개수: ★4 1 / ★5 0(쓰레기통 한우 제외) / 보관함 1 / 쓰레기통 1');
ok(!els.srcList.innerHTML.includes('한우 등심') && !els.srcList.innerHTML.includes('크리넥스'), '보관·쓰레기 상품은 목록에서 사라짐');
T.S.srcView = 'keep'; T.renderSrc();
let k = els.srcList.innerHTML;
ok(k.includes('크리넥스') && k.includes('data-ex="auto"') && k.includes('목록으로') && k.includes('mk ·') && cards(k) === 1, '보관함: 카드 + [목록으로] + 누가 보관');
T.S.srcView = 'trash'; T.renderSrc();
k = els.srcList.innerHTML;
ok(k.includes('한우 등심') && k.includes('자동 제외') && k.includes('정육') && k.includes('data-ex="include"') && k.includes('되돌리기'), '쓰레기통: 음식 자동 제외 사유 + [되돌리기]=제외 해제');
// Apps Script 가 페이지를 내보낼 때 문자열 속 // 를 주석으로 잘라 스크립트 전체가 죽은 적이 있다 (v20, v21).
// 그래서 스크립트 코드 줄에 :// 를 쓰지 않는다 (문자열에서는 :\/\/ 로 쓰면 값은 같다)
const bad = code.split('\n').map((l, n) => [n + 1, l]).filter(([, l]) => !l.trim().startsWith('//') && l.includes('://'));
ok(!bad.length, '스크립트 코드에 :// 없음 (Apps Script 주석 제거 버그 대비)' + (bad.length ? ' -> 줄 ' + bad.map(x => x[0]).join(',') : ''));
// 4) 보관함 카드 [캡처 보기] + 캡처 창
T.S.srcView = 'keep'; T.renderSrc();
ok(els.srcList.innerHTML.includes('data-shot="2"') && els.srcList.innerHTML.includes('캡처 보기'), '보관함 카드에 [캡처 보기]');
T.S.srcView = 'list'; T.renderSrc();
ok(!els.srcList.innerHTML.includes('data-shot='), '목록 카드에는 캡처 버튼 없음');
const kit = T.S.src.items.find(i => i.articleId === '2');
T.shotIt = kit; T.S.shots = null; T.renderShots();
ok(els.shotBody.innerHTML.includes('불러오는 중'), '캡처 창: 불러오는 중');
T.S.shots = { key: '222', post: { at: now, who: 'auto', err: '', data: 'data:image/jpeg;base64,QUJD' }, catalog: null,
  sellers: { at: now, who: 'mk', near: 2, items: [{ mall: '가게<b>', price: 9000 }, { mall: 'B', price: 9500 }] } };
T.shotKind = 'catalog'; T.renderShots();
const sb = els.shotBody.innerHTML;
ok(sb.includes('<img src="data:image/jpeg;base64,QUJD"') && sb.includes('자동 캡처'), '카페 글 캡처 이미지 + 자동 캡처 표시');
ok(sb.includes('sh-drop on" data-kind="catalog"') && sb.includes('Ctrl+V') && sb.includes('type="file"'), '가격비교: 붙여넣기 칸(선택됨) + 파일 선택');
ok(sb.includes('판매처 2곳') && sb.includes('가게&lt;b&gt;') && sb.includes('9,000원'), '북마클릿 판매처 목록 표 (이스케이프)');
ok(sb.includes('href="https://x/catalog/2"') && sb.includes('href="https://cafe/2"'), '카페 글 열기 / 가격비교 열기 링크');
T.S.shots = { key: '222', post: { at: now, who: 'auto', err: '로그인이 필요한 글', data: '' }, catalog: { at: now, who: 'mk', err: '', data: 'data:image/png;base64,QQ==' } };
T.shotKind = 'post'; T.renderShots();
ok(els.shotBody.innerHTML.includes('자동 캡처를 못 했어요: 로그인이 필요한 글') && els.shotBody.innerHTML.includes('sh-drop on" data-kind="post"'), '자동 캡처 실패: 사유 + 직접 붙여넣기 칸');
ok(els.shotBody.innerHTML.includes('다른 캡처로 바꾸기') && els.shotBody.innerHTML.includes('mk'), '이미 있는 가격비교 캡처: 누가 넣었는지 + 바꾸기');
process.exit(fail ? 1 : 0);
