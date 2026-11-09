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
  getRange(r, c, nr = 1, nc = 1) { return new Range(this, r, c, nr, nc); }
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
process.exit(fail ? 1 : 0);
