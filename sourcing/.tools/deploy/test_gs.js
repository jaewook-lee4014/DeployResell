// Code.gs 의 발굴 함수를 가짜 SpreadsheetApp 으로 실행해 보는 검증 스크립트
const fs = require('fs');
const vm = require('vm');

class Range {
  constructor(sh, r, c, nr, nc) { Object.assign(this, { sh, r, c, nr, nc }); }
  getValues() { const o = []; for (let i = 0; i < this.nr; i++) { const row = this.sh.rows[this.r - 1 + i] || []; o.push(Array.from({ length: this.nc }, (_, j) => row[this.c - 1 + j] ?? '')); } return o; }
  setValues(v) { v.forEach((row, i) => { const t = this.sh.rows[this.r - 1 + i] = this.sh.rows[this.r - 1 + i] || []; row.forEach((x, j) => t[this.c - 1 + j] = x); }); }
  getValue() { return this.getValues()[0][0]; }
  setValue(x) { this.setValues([[x]]); }
}
class Sheet {
  constructor() { this.rows = []; }
  getLastRow() { return this.rows.length; }
  getRange(r, c, nr = 1, nc = 1) { if (typeof r === 'string') { const m = r.match(/^([A-Z])(\d+)$/); return new Range(this, +m[2], m[1].charCodeAt(0) - 64, 1, 1); } return new Range(this, r, c, nr, nc); }
  appendRow(r) { this.rows.push(r.slice()); }
  setFrozenRows() {}
}
const sheets = {};
const ss = { getSheetByName: n => sheets[n] || null, insertSheet: n => (sheets[n] = new Sheet()) };
const props = {};
const ctx = {
  SpreadsheetApp: { openById: () => ss },
  LockService: { getScriptLock: () => ({ waitLock() {}, releaseLock() {} }) },
  PropertiesService: { getScriptProperties: () => ({ getProperty: k => props[k] ?? null, setProperty: (k, v) => props[k] = v, getProperties: () => props, setProperties: o => Object.assign(props, o) }) },
  ScriptApp: { getService: () => ({ getUrl: () => 'https://example/exec' }) },
  HtmlService: { createHtmlOutput: h => ({ html: h, setTitle() { return this; } }) },
  ContentService: { createTextOutput: t => ({ t, setMimeType() { return this; } }), MimeType: { JSON: 'json' } },
  console,
};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(process.argv[2], 'utf8').replace("'__WORKER_TOKEN__'", "'tok'"), ctx);
const run = s => vm.runInContext(s, ctx);
let fail = 0;
const ok = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fail++; };

// 1) 작업기 전송 (doPost op=sourcing): 새 글 2개 + 1개 덮어쓰기 + 상태
const rules = [{ rule: '최저가보다 싸다', ok: true, pts: 2, why: 'x' }, { rule: '경쟁 약함', ok: true, pts: 1, why: '추정' }, { rule: '리뷰 많음', ok: true, pts: 1, why: 'r' }];
const item = (id, nv, stars, points) => ({ articleId: id, postedAt: '2026-11-09T10:00:00+09:00', mall: '쿠팡', name: '=상품' + id, dealPrice: 1000, dealPriceNorm: 1000, status: 'ok', nvMid: nv, catTitle: 'c', catPrice: 2000, sellers: 5, reviews: 500, near: 1, offers: 4, gap12: 100, compSource: '검색결과 근사', matchConf: '높음', points, stars, rules, histLow: null, catLink: 'https://search.shopping.naver.com/catalog/' + nv, articleUrl: 'u', checkedAt: 't', subject: 's' });
const post = body => JSON.parse(run(`doPost({postData:{contents:${JSON.stringify(JSON.stringify(body))}}})`).t);
let r = post({ token: 'tok', op: 'sourcing', items: [item(1, '111', 4, 4), item(2, '222', 3, 3), { ...item(3, '', 1, 0), status: 'no_catalog' }] });
ok(r.ok && r.added === 3, 'sourcing 저장: ' + JSON.stringify(r));
r = post({ token: 'tok', op: 'sourcing', items: [item(2, '222', 2, 2)], status: { at: 'now' } });
ok(r.updated === 1 && sheets['발굴'].rows.length === 4, '같은 글번호는 덮어쓰기');
ok(post({ token: 'bad', op: 'sourcing', items: [] }).error === 'unauthorized', '토큰 틀리면 거부');
ok(String(sheets['발굴'].rows[1][3]).startsWith("'"), '= 로 시작하는 상품명은 수식 방지');

// 2) 화면 데이터
let L = run(`loadSourcing('mk')`);
ok(L.items.length === 2 && L.noCatalog === 1 && L.status.at === 'now', 'loadSourcing: ok 2건, 카탈로그없음 1건, 상태');
ok(L.items[0].articleId === '2' && L.items[0].stars === 2, '최신 글이 먼저, 덮어쓴 값 반영');

// 3) 북마클릿: 발굴 상품 페이지 -> 정확한 경쟁도 (근처 4곳 -> 경쟁 심함 -> 1점 감소)
const cap = d => run(`capture_(${JSON.stringify(JSON.stringify(d))})`).html;
let h = cap({ who: 'mk', title: '아무 상품 : 네이버 쇼핑', url: 'https://search.shopping.naver.com/catalog/111', items: [{ mall: 'a', price: 10000 }, { mall: 'b', price: 10010 }, { mall: 'c', price: 10500 }, { mall: 'd', price: 10990 }, { mall: 'e', price: 15000 }] });
ok(h.includes('정확한 경쟁도') && h.includes('4곳'), '북마클릿 저장: ' + h.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').slice(0, 80));
L = run(`loadSourcing('mk')`);
const a = L.items.find(i => i.nvMid === '111');
ok(a.exact && a.exact.near === 4 && a.points === 3 && a.stars === 3, `실제 경쟁도로 재계산: points ${a.points} stars ${a.stars}`);
ok(a.rules.find(x => x.rule === '경쟁 약함').ok === false, '경쟁 규칙 실패로 표시');
h = cap({ who: 'mk', title: 'x', url: 'https://search.shopping.naver.com/catalog/999', items: [{ mall: 'a', price: 1 }] });
ok(h.includes('발굴 목록에 없는'), '발굴에 없는 카탈로그는 저장 안 함');
h = cap({ who: 'zz', title: 'x', url: 'https://search.shopping.naver.com/catalog/111', items: [] });
ok(h.includes('저장하지 못했어요'), '코드네임 틀리면 거부');
let threw = false; try { run(`loadSourcing('zz')`); } catch (e) { threw = true; }
ok(threw, 'loadSourcing 코드네임 확인');

// 4) 음식 자동 제외 + 사람이 제외/해제 (발굴제외 시트, 작업기가 다시 보내도 유지)
sheets['기록'] = new Sheet();
post({ token: 'tok', op: 'sourcing', items: [{ ...item(4, '444', 4, 4), name: '한우 등심', autoExclude: true, excludeWhy: "상품명 '한우' (정육)", category: '식품' }] });
L = run(`loadSourcing('mk')`);
let m = L.items.find(i => i.nvMid === '444');
ok(m.autoExclude === true && m.excluded === true && m.excludeWhy.includes('한우') && m.category === '식품', '자동 제외 표시');
ok(L.items.find(i => i.nvMid === '111').excluded === false, '음식 아니면 제외 아님');
r = run(`setSourcingExclude('mk', '444', '4', 'include')`);
ok(r.ok && r.manual.state === 'include' && r.manual.who === 'mk', '제외 해제 저장');
post({ token: 'tok', op: 'sourcing', items: [{ ...item(4, '444', 4, 4), name: '한우 등심', autoExclude: true, excludeWhy: 'x' }] });
m = run(`loadSourcing('mk')`).items.find(i => i.nvMid === '444');
ok(m.excluded === false && m.autoExclude === true, '작업기가 덮어써도 사람이 해제한 값 유지');
run(`setSourcingExclude('mk', '111', '1', 'exclude')`);
ok(run(`loadSourcing('mk')`).items.find(i => i.nvMid === '111').excluded === true, '직접 제외');
run(`setSourcingExclude('mk', '444', '4', 'auto')`);
m = run(`loadSourcing('mk')`).items.find(i => i.nvMid === '444');
ok(m.excluded === true && m.manual === null, '자동으로 되돌리면 자동 판단(제외)');
ok(sheets['발굴제외'].rows.length === 4 && sheets['기록'].rows.length === 3, '발굴제외 기록 3줄 + 수정 기록');
threw = false; try { run(`setSourcingExclude('mk', '999', '9', 'exclude')`); } catch (e) { threw = /없는 상품/.test(e.message); }
ok(threw, '발굴 목록에 없는 상품은 거부');
threw = false; try { run(`setSourcingExclude('zz', '444', '4', 'exclude')`); } catch (e) { threw = true; }
ok(threw, '코드네임 확인');
threw = false; try { run(`setSourcingExclude('mk', '444', '4', 'drop')`); } catch (e) { threw = true; }
ok(threw, '상태값 확인');

// 5) 보관함(keep): 목록·쓰레기통 아님, 작업기가 덮어써도 유지, 음식 자동 제외여도 보관함이 이긴다
r = run(`setSourcingExclude('mk', '222', '2', 'keep')`);
ok(r.ok && r.manual.state === 'keep', '보관함 저장');
post({ token: 'tok', op: 'sourcing', items: [item(2, '222', 3, 3)] });
m = run(`loadSourcing('mk')`).items.find(i => i.nvMid === '222');
ok(m.manual.state === 'keep' && m.excluded === false, '작업기가 덮어써도 보관함 유지');
run(`setSourcingExclude('mk', '444', '4', 'keep')`);
m = run(`loadSourcing('mk')`).items.find(i => i.nvMid === '444');
ok(m.manual.state === 'keep' && m.excluded === false && m.autoExclude === true, '음식 자동 제외 상품도 보관함 가능');
run(`setSourcingExclude('mk', '222', '2', 'auto')`);
ok(run(`loadSourcing('mk')`).items.find(i => i.nvMid === '222').manual === null, '보관함에서 목록으로');
ok(String(sheets['기록'].rows.slice(-1)[0][4]) === '목록으로', '기록 탭에 한글 상태');

// 6) 보관함 캡처: 작업기가 카페 글 캡처할 목록 -> 저장(여러 칸으로 나눔) -> 화면에서 읽기, 사람이 가격비교 붙여넣기
run(`setSourcingExclude('mk', '222', '2', 'keep')`);
r = post({ token: 'tok', op: 'shotPull' });
ok(r.ok && r.items.length === 2 && r.items.some(x => x.key === '222' && x.articleId === '2'), 'shotPull: 보관함 상품(카페 글 캡처 없음)');
const big = 'data:image/jpeg;base64,' + '+AbC/9'.repeat(20000) + '==';  // 12만 자 -> 3칸
r = post({ token: 'tok', op: 'shot', nvMid: '222', articleId: '2', kind: 'post', data: big });
ok(r.ok && sheets['발굴캡처'].rows.length === 4 && sheets['발굴캡처'].rows[1][5].startsWith("'"), '캡처 저장: 3칸 + 글자로 저장');
r = post({ token: 'tok', op: 'shotPull' });
ok(r.items.length === 1 && r.items[0].key === '444', '캡처한 상품은 다시 안 나옴');
post({ token: 'tok', op: 'shot', nvMid: '444', articleId: '4', kind: 'post', error: '로그인이 필요한 글' });
ok(post({ token: 'tok', op: 'shotPull' }).items.length === 0, '실패도 기록해서 계속 다시 시도하지 않음');
let S6 = run(`loadSourcingShots('mk', '222', '2')`);
ok(S6.post && S6.post.data === big && S6.post.who === 'auto' && S6.catalog === null, '화면: 카페 글 캡처 그대로 복원');
ok(run(`loadSourcingShots('mk', '444', '4')`).post.err.includes('로그인'), '화면: 자동 캡처 실패 사유');
const small = 'data:image/png;base64,iVBORw0KGgo=';
ok(run(`saveSourcingShot('mk', '111', '1', 'catalog', '${small}')`).ok, '사람이 가격비교 캡처 붙여넣기');
S6 = run(`loadSourcingShots('mk', '111', '1')`);
ok(S6.catalog.data === small && S6.catalog.who === 'mk' && S6.sellers && S6.sellers.near === 4 && S6.sellers.items.length === 5, '화면: 가격비교 캡처 + 북마클릿 판매처 목록');
run(`saveSourcingShot('mk', '111', '1', 'catalog', 'data:image/png;base64,QUJD')`);
ok(run(`loadSourcingShots('mk', '111', '1')`).catalog.data === 'data:image/png;base64,QUJD', '다시 붙여넣으면 최신 것');
threw = false; try { run(`saveSourcingShot('mk', '111', '1', 'catalog', 'javascript:alert(1)')`); } catch (e) { threw = /형식/.test(e.message); }
ok(threw, '이미지가 아니면 거부');
threw = false; try { run(`saveSourcingShot('zz', '111', '1', 'catalog', '${small}')`); } catch (e) { threw = true; }
ok(threw, '캡처 저장도 코드네임 확인');
ok(post({ token: 'bad', op: 'shotPull' }).error === 'unauthorized', 'shotPull 토큰 확인');
// 7) 온라인 경쟁사 자동 검색 저장 (op=onlineComps): 속성 저장 + 가격이력 추이 + load() 로 화면에
sheets['상태'] = new Sheet(); sheets['상태'].rows = [[JSON.stringify({ skus: { grape: { price: 23500, couponPrice: 21500, stock: 8 } } })]];
sheets['가격이력'] = new Sheet(); sheets['가격이력'].rows = [['시각']];
const autoState = { at: '2026-11-09T12:00:00+09:00', errors: [], skus: {
  grape: { comps: Array.from({ length: 12 }, (_, k) => ({ mall: '가게' + k, price: 23000 + k * 10, ship: k % 2 ? 3000 : 0, eff: 23000 + k * 10 + (k % 2 ? 3000 : 0), title: 'x' })), catalog: { id: '51929242376', low: 23480, sellers: 16 } },
  apple: { comps: [], catalog: null }, bogus: { comps: [{ mall: 'x', eff: 1 }] } } };
r = post({ token: 'tok', op: 'onlineComps', state: autoState });
ok(r.ok && r.history === 1, 'onlineComps 저장 + 가격이력 1줄 (판매처 있는 맛만)');
const au = JSON.parse(props.onlineAuto);
ok(au.skus.grape.comps.length === 8 && au.skus.grape.comps[0].eff === 23000 && au.skus.grape.comps[1].eff === 23020 && !au.skus.bogus, '맛마다 배송비 포함 싼 순 8곳, 모르는 맛 무시');
ok(props.onlineAuto.length < 9000, '스크립트 속성 9KB 한도 안');
const hr = sheets['가격이력'].rows[1];
ok(hr[1] === 'grape' && hr[2] === 23500 && hr[3] === 21500 && hr[5] === '가게0' && hr[6] === 23000 && String(hr[11]).includes('가격비교 최저 23480'), '가격이력: 우리 값 + 경쟁 1~3위 + 메모');
ok(post({ token: 'bad', op: 'onlineComps', state: autoState }).error === 'unauthorized', 'onlineComps 토큰 확인');
process.exit(fail ? 1 : 0);
