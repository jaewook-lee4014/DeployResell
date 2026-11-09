/**
 * 마마솔루션 재고 웹사이트 (Google Apps Script 웹앱)
 *
 * 데이터: 구글시트 '마마솔루션 재고 앱 (데이터)'
 *   재고     — id | 맛 | 수량 | 확인시각 | 확인자          (실제 창고 재고, 사람이 입력)
 *   기준     — 항목 | 값   (cost, cover, margin, win, coupon, undercut, minMargin, addonGap)
 *   기록     — 시각 | 코드네임 | 항목 | 이전 | 이후
 *   데이터   — A1에 판매 집계 JSON (build_app.py가 만든 data/app_data.json)
 *   상태     — A1에 최신 온라인 상태 JSON (VM 작업기가 30분마다 보냄: 판매가·페이지 재고·추가상품·경쟁사)
 *   가격이력 — 시각 | 맛 | 우리 판매가 | 우리 쿠폰가 | 페이지 재고 | 1~3위 판매처·가격 | 비고
 *   요청     — id | 종류(analyze/apply/refresh/crawl) | 맛 | 요청자 | 요청시각 | 상태 | 요청내용 | 결과 | 완료시각
 *   최저가     — 확인시각 | 검색어 | 순위 | 상품ID(nv_mid) | 상품명 | 최저가 | 배송비 | 판매처수 | 평점 | 리뷰수 | 링크
 *                (naver_price_monitor.py 가 1시간마다·[업데이트] 때 보냄. 예전 naver_price_history.csv 와 같은 열)
 *   최저가요약 — 확인시각 | 검색어 | 1위 상품ID | 1위 상품명 | 1위 최저가 | 전체 최저가 | 상품수  (추이 차트용, 사이클당 1줄)
 *
 * 코드네임은 서버에서만 확인한다. 틀리면 어떤 데이터도 내려가지 않는다.
 * 네이버 커머스 API는 고정 IP에서만 호출되므로 실제 가격 변경은 VM 작업기(worker.py)가 한다.
 * 작업기는 doPost로 이 웹앱과 통신하며 WORKER_TOKEN으로 확인한다.
 */
const SHEET_ID = '1clUARyqPIxpZ4_uQShk4vakD4NjxeLPPr4rHaRE3yus';
const CODES = { mk: true, jo: true }; // 들어올 수 있는 코드네임 (mk = 매니저)
const WORKER_TOKEN = '__WORKER_TOKEN__';
const SKU_IDS = ['grape', 'apple', 'calmadi'];
const PLAN_KEYS = {
  cost: '매입가', cover: '며칠치', margin: '목표 마진', win: '판매 기준',
  coupon: '쿠폰 금액', undercut: '최저가보다 싸게', minMargin: '최소 이익률', addonGap: '추가상품 할인',
};
const ANALYSIS_TTL_MIN = 15; // 분석 결과로 적용할 수 있는 시간

function doGet(e) {
  if (e && e.parameter && e.parameter.cap) return capture_(e.parameter.cap);
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('마마솔루션 재고')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

// ── 경쟁사 가져오기 (북마클릿) ────────────────────────────────
// 네이버 가격비교 페이지에서 북마클릿을 누르면 판매처·가격 목록을 ?cap=JSON 으로 보내온다.
const OUR_MALL = '마마솔루션';
const SKU_KW = { grape: '포도', apple: '사과', calmadi: '칼마디' };

function capturePage_(title, body) {
  return HtmlService.createHtmlOutput(
    '<meta name="viewport" content="width=device-width,initial-scale=1"><div style="font:16px/1.6 -apple-system,\'Malgun Gothic\',sans-serif;max-width:420px;margin:40px auto;padding:0 16px">' +
    '<h2 style="font-size:19px">' + title + '</h2>' + body +
    '<p style="color:#888;font-size:13px">이 창은 닫아도 돼요. 사이트의 온라인 탭에서 바로 보여요.</p></div>').setTitle('경쟁사 가져오기');
}

function esc_(s) {
  return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; });
}

function capture_(raw) {
  let d;
  try {
    d = JSON.parse(raw);
    check_(d.who);
  } catch (err) {
    return capturePage_('저장하지 못했어요', '<p>' + esc_(err.message || err) + '</p>');
  }
  const who = String(d.who).trim().toLowerCase();
  const title = String(d.title || '');
  const sku = Object.keys(SKU_KW).filter(function (k) { return title.indexOf(SKU_KW[k]) >= 0; })[0];
  if (!sku) return captureSourcing_(d, who); // 우리 상품이 아니면 신상품 발굴 후보의 정확한 경쟁도로 저장
  const items = (d.items || []).map(function (x) {
    return { mall: String(x.mall || '').slice(0, 30), price: Math.round(Number(x.price)) || 0, title: String(x.title || '').slice(0, 60) };
  }).filter(function (x) { return x.price > 0; }).sort(function (a, b) { return a.price - b.price; });
  const ours = items.filter(function (x) { return x.mall.indexOf(OUR_MALL) >= 0; })[0] || null;
  const comps = items.filter(function (x) { return x.mall.indexOf(OUR_MALL) < 0; });
  const at = new Date().toISOString();
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const ss = book_();
    const cs = ss.getSheetByName('경쟁사') || ss.insertSheet('경쟁사');
    if (cs.getLastRow() === 0) cs.appendRow(['시각', '맛', '가져온 사람', '우리 표시가', '판매처 목록(JSON)', '페이지']);
    cs.appendRow([at, sku, who, ours ? ours.price : '', JSON.stringify(items), String(d.url || '').slice(0, 200)]);
    const st = json_(ss.getSheetByName('상태').getRange('A1'));
    const s = st && st.skus && st.skus[sku];
    const c = comps;
    ss.getSheetByName('가격이력').appendRow([at, sku, s ? s.price : '', ours ? ours.price : (s ? s.couponPrice : ''), s ? s.stock : '',
      c[0] ? c[0].mall : '', c[0] ? c[0].price : '', c[1] ? c[1].mall : '', c[1] ? c[1].price : '', c[2] ? c[2].mall : '', c[2] ? c[2].price : '',
      who + ' 페이지에서 가져옴']);
  } finally {
    lock.releaseLock();
  }
  const rank = ours ? items.indexOf(ours) + 1 : null;
  return capturePage_(SKU_KW[sku] + ' 경쟁사 ' + comps.length + '곳 저장했어요',
    '<p>최저가 <b>' + (comps[0] ? esc_(comps[0].mall) + ' ' + comps[0].price.toLocaleString() + '원' : '-') + '</b></p>' +
    (ours ? '<p>우리 표시가 ' + ours.price.toLocaleString() + '원 · ' + rank + '위 / ' + items.length + '곳</p>' : '<p>목록에 우리 가게가 없어요</p>'));
}

/** 맛별로 가장 최근에 가져온 경쟁사 목록 */
function captures_(ss) {
  const cs = ss.getSheetByName('경쟁사');
  const out = {};
  if (!cs || cs.getLastRow() < 2) return out;
  const n = Math.min(cs.getLastRow() - 1, 60);
  cs.getRange(cs.getLastRow() - n + 1, 1, n, 5).getValues().forEach(function (r) {
    out[r[1]] = { at: iso_(r[0]), who: String(r[2]), ours: r[3] === '' ? null : Number(r[3]), items: JSON.parse(r[4] || '[]') };
  });
  return out;
}

function check_(code) {
  code = String(code || '').trim().toLowerCase();
  if (!Object.prototype.hasOwnProperty.call(CODES, code)) throw new Error('등록되지 않은 코드네임이에요');
  return code;
}

function iso_(v) {
  return v instanceof Date ? v.toISOString() : String(v || '');
}

function book_() {
  return SpreadsheetApp.openById(SHEET_ID);
}

function json_(range) {
  const v = range.getValue();
  return v ? JSON.parse(v) : null;
}

function plan_(ss) {
  const plan = {};
  ss.getSheetByName('기준').getDataRange().getValues().slice(1).forEach(function (r) {
    if (r[0]) plan[r[0]] = Number(r[1]);
  });
  return plan;
}

/** 화면에 필요한 전부: 재고, 기준, 최근 기록, 판매 집계, 온라인 상태와 가격 이력 */
function load(code) {
  code = check_(code);
  const ss = book_();
  const stock = {};
  ss.getSheetByName('재고').getDataRange().getValues().slice(1).forEach(function (r) {
    if (r[0]) stock[r[0]] = { qty: Number(r[2]) || 0, at: iso_(r[3]), by: String(r[4] || '') };
  });
  const logRows = ss.getSheetByName('기록').getDataRange().getValues().slice(1);
  const log = logRows.slice(-100).reverse().map(function (r) {
    return { at: iso_(r[0]), who: String(r[1]), item: String(r[2]), from: String(r[3]), to: String(r[4]) };
  });
  // 가격 이력: 최근 1500줄(약 10일)만
  const hs = ss.getSheetByName('가격이력');
  const n = hs.getLastRow() - 1;
  const hist = n > 0 ? hs.getRange(Math.max(2, hs.getLastRow() - 1499), 1, Math.min(n, 1500), 11).getValues().map(function (r) {
    return [iso_(r[0]), r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10]];
  }) : [];
  return {
    who: code, stock: stock, plan: plan_(ss), log: log,
    data: json_(ss.getSheetByName('데이터').getRange('A1')),
    online: json_(ss.getSheetByName('상태').getRange('A1')),
    hist: hist,
    caps: captures_(ss),
    lowBadge: lowestBadge_(ss),
    appUrl: ScriptApp.getService().getUrl(),
  };
}

function log_(ss, code, item, from, to) {
  ss.getSheetByName('기록').appendRow([new Date().toISOString(), code, item, String(from), String(to)]);
}

/** 실제 재고 수정. shown = 수정 전 화면에 보이던 값(기록용) */
function saveStock(code, id, qty, shown) {
  code = check_(code);
  qty = Math.round(Number(qty));
  if (!isFinite(qty) || qty < 0 || qty > 100000) throw new Error('재고 수량을 확인해 주세요');
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const ss = book_();
    const sh = ss.getSheetByName('재고');
    const rows = sh.getDataRange().getValues();
    for (let i = 1; i < rows.length; i++) {
      if (rows[i][0] === id) {
        sh.getRange(i + 1, 3, 1, 3).setValues([[qty, new Date().toISOString(), code]]);
        log_(ss, code, rows[i][1] + ' 실제 재고', isFinite(Number(shown)) ? Math.round(Number(shown)) : rows[i][2], qty);
        return load(code);
      }
    }
    throw new Error('없는 상품이에요');
  } finally {
    lock.releaseLock();
  }
}

/** 계산 기준 수정 */
function savePlan(code, key, value) {
  code = check_(code);
  if (!Object.prototype.hasOwnProperty.call(PLAN_KEYS, key)) throw new Error('없는 항목이에요');
  value = Number(value);
  if (!isFinite(value) || value < 0) throw new Error('값을 확인해 주세요');
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const ss = book_();
    const sh = ss.getSheetByName('기준');
    const rows = sh.getDataRange().getValues();
    const unit = key === 'win' ? '개월' : (key === 'margin' || key === 'minMargin') ? '%' : (key === 'cover' ? '일' : '원');
    for (let i = 1; i < rows.length; i++) {
      if (rows[i][0] === key) {
        const prev = rows[i][1];
        if (Number(prev) === value) return load(code);
        sh.getRange(i + 1, 2).setValue(value);
        log_(ss, code, PLAN_KEYS[key], prev + unit, value + unit);
        return load(code);
      }
    }
    sh.appendRow([key, value]);
    log_(ss, code, PLAN_KEYS[key], '-', value + unit);
    return load(code);
  } finally {
    lock.releaseLock();
  }
}

// ── 가격 맞추기 요청 (화면 → 시트 '요청' → VM 작업기) ─────────────

function newRequest_(ss, type, sku, code, params) {
  const id = Utilities.getUuid().slice(0, 8);
  ss.getSheetByName('요청').appendRow([id, type, sku, code, new Date().toISOString(), 'pending', params ? JSON.stringify(params) : '', '', '']);
  return id;
}

function findRequest_(ss, id) {
  const sh = ss.getSheetByName('요청');
  const rows = sh.getDataRange().getValues();
  for (let i = rows.length - 1; i >= 1; i--) {
    if (String(rows[i][0]) === String(id)) return { sh: sh, row: i + 1, r: rows[i] };
  }
  return null;
}

/** 가격 제안을 받아온다. comp = 사람이 네이버 쇼핑에서 보고 입력한 경쟁사 최저가 {price, mall} */
function requestAnalyze(code, sku, comp) {
  code = check_(code);
  if (SKU_IDS.indexOf(sku) < 0) throw new Error('없는 상품이에요');
  const price = Math.round(Number(comp && comp.price));
  if (!isFinite(price) || price < 5000 || price > 200000) throw new Error('경쟁사 최저가를 확인해 주세요');
  const mall = String((comp && comp.mall) || '').trim().slice(0, 30) || '직접 입력';
  const ss = book_();
  // 입력한 경쟁사 가격도 추이에 남긴다
  const st = json_(ss.getSheetByName('상태').getRange('A1'));
  const s = st && st.skus && st.skus[sku];
  ss.getSheetByName('가격이력').appendRow([new Date().toISOString(), sku, s ? s.price : '', s ? s.couponPrice : '', s ? s.stock : '',
    mall, price, '', '', '', '', code + ' 직접 입력']);
  // 실제 쿠폰 = 가져온 시점의 우리 판매가 - 가격비교 페이지에 보인 우리 가격 (6시간 이내 것만)
  const params = { comp: { mall: mall, price: price } };
  const cap = captures_(ss)[sku];
  if (cap && cap.ours && Date.now() - new Date(cap.at).getTime() < 6 * 3600e3) {
    const hs = ss.getSheetByName('가격이력').getDataRange().getValues();
    for (let i = hs.length - 1; i >= 1; i--) {
      if (hs[i][1] === sku && String(hs[i][11]).indexOf('페이지에서 가져옴') >= 0) {
        const eff = Number(hs[i][2]) - cap.ours;
        if (eff >= 0 && eff <= 10000) params.effCoupon = { value: eff, listing: Number(hs[i][2]), shown: cap.ours };
        break;
      }
    }
  }
  return newRequest_(ss, 'analyze', sku, code, params);
}

/** 지금 스토어 상태(판매가·페이지 재고·추가상품)를 바로 다시 읽어 달라고 요청한다 */
function requestRefresh(code) {
  code = check_(code);
  return newRequest_(book_(), 'refresh', 'all', code, null);
}

/** 분석 결과를 그대로 적용해 달라고 요청한다. 제안 내용은 서버에 저장된 분석 결과에서 가져온다 */
function requestApply(code, analysisId) {
  code = check_(code);
  const ss = book_();
  const f = findRequest_(ss, analysisId);
  if (!f || f.r[1] !== 'analyze' || f.r[5] !== 'done') throw new Error('먼저 분석을 끝내 주세요');
  const doneAt = new Date(f.r[8]);
  if (Date.now() - doneAt.getTime() > ANALYSIS_TTL_MIN * 60000) throw new Error('분석한 지 ' + ANALYSIS_TTL_MIN + '분이 지났어요. 다시 분석해 주세요');
  const p = JSON.parse(f.r[7]);
  const plan = plan_(ss);
  if (p.margin < plan.minMargin) throw new Error('이익률 ' + p.margin + '%가 최소 ' + plan.minMargin + '%보다 낮아요');
  return newRequest_(ss, 'apply', f.r[2], code, p);
}

/** 요청 진행 상태 */
function getRequest(code, id) {
  check_(code);
  const f = findRequest_(book_(), id);
  if (!f) throw new Error('요청을 찾지 못했어요');
  return { id: id, type: f.r[1], sku: f.r[2], status: f.r[5], result: f.r[7] ? JSON.parse(f.r[7]) : null, at: iso_(f.r[4]) };
}

// ── VM 작업기용 API (doPost, JSON) ─────────────────────────────

function out_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  let body;
  try {
    body = JSON.parse(e.postData.contents);
  } catch (err) {
    return out_({ ok: false, error: 'bad json' });
  }
  if (!body || body.token !== WORKER_TOKEN || WORKER_TOKEN.indexOf('__') === 0) return out_({ ok: false, error: 'unauthorized' });
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const ss = book_();
    if (body.op === 'pull') return out_(workerPull_(ss));
    if (body.op === 'result') return out_(workerResult_(ss, body));
    if (body.op === 'snapshot') return out_(workerSnapshot_(ss, body.state));
    if (body.op === 'crawlPull') return out_(crawlPull_(ss, body.status, body.taker));
    if (body.op === 'supPull') return out_(supPull_(ss, body.status, body.take !== false, body.taker));
    if (body.op === 'lowest') return out_(saveLowest_(ss, body.cycles));
    if (body.op === 'sourcing') return out_(saveSourcing_(ss, body.items || [], body.status));
    return out_({ ok: false, error: 'unknown op' });
  } catch (err) {
    return out_({ ok: false, error: String(err && err.message || err) });
  } finally {
    lock.releaseLock();
  }
}

function workerPull_(ss) {
  const sh = ss.getSheetByName('요청');
  const rows = sh.getDataRange().getValues();
  const reqs = [];
  for (let i = 1; i < rows.length; i++) {
    if (rows[i][5] === 'pending' && rows[i][1] !== 'crawl' && rows[i][1] !== 'monitor') { // crawl 은 최저가 모니터, monitor 는 관리 프로그램이 가져간다
      reqs.push({ id: String(rows[i][0]), type: rows[i][1], sku: rows[i][2], by: rows[i][3], params: rows[i][6] ? JSON.parse(rows[i][6]) : null });
      sh.getRange(i + 1, 6).setValue('running');
    }
  }
  // 수수료율 = 1 - 정산액/결제액 (최근 6개월 실제 주문 기준)
  const data = json_(ss.getSheetByName('데이터').getRange('A1'));
  const econ = {};
  data.skus.forEach(function (s) {
    econ[s.id] = { fee: s.payU ? 1 - s.settleU / s.payU : 0.04, ship: data.shipPerUnit };
  });
  return { ok: true, requests: reqs, settings: plan_(ss), econ: econ };
}

function workerResult_(ss, body) {
  const f = findRequest_(ss, body.id);
  if (!f) return { ok: false, error: 'no such request' };
  f.sh.getRange(f.row, 6).setValue(body.status);
  f.sh.getRange(f.row, 8).setValue(JSON.stringify(body.result || {}));
  f.sh.getRange(f.row, 9).setValue(new Date().toISOString());
  const names = { grape: '포도', apple: '사과', calmadi: '칼마디' };
  if (f.r[1] === 'monitor') {
    log_(ss, f.r[3], '최저가 모니터 ' + (MONITOR_ACTIONS[f.r[2]] || f.r[2]), body.status === 'done' ? '완료' : '실패',
      (body.result && (body.result.message || body.result.error)) || '');
  }
  if (f.r[1] === 'apply') {
    if (body.status === 'done') {
      (body.result.changed || []).forEach(function (c) { log_(ss, f.r[3], '가격 적용', names[f.r[2]], c); });
    } else {
      log_(ss, f.r[3], '가격 적용 실패', names[f.r[2]], (body.result && body.result.error) || '');
    }
  }
  return { ok: true };
}

function workerSnapshot_(ss, state) {
  if (!state) return { ok: false, error: 'no state' };
  ss.getSheetByName('상태').getRange('A1').setValue(JSON.stringify(state));
  const rows = [];
  Object.keys(state.skus || {}).forEach(function (id) {
    const s = state.skus[id];
    const c = s.comps || [];
    rows.push([state.at, id, s.price, s.couponPrice, s.stock,
      c[0] ? c[0].mall : '', c[0] ? c[0].price : '', c[1] ? c[1].mall : '', c[1] ? c[1].price : '',
      c[2] ? c[2].mall : '', c[2] ? c[2].price : '', '']);
  });
  if (rows.length) {
    const hs = ss.getSheetByName('가격이력');
    hs.getRange(hs.getLastRow() + 1, 1, rows.length, rows[0].length).setValues(rows);
  }
  return { ok: true };
}

// ── 네이버쇼핑 최저가 모니터 (naver_price_monitor.py) ─────────────
// 모니터는 PC/서버에서 돌며 1분마다 crawlPull 로 [업데이트] 요청을 가져가고,
// 1시간마다 또는 요청이 있을 때 크롤링해서 lowest 로 결과를 보낸다.
// 실패한 확인도 '최저가요약'에 상태=error 로 남겨서 화면이 "이전 가격이 그대로"인 상황을 알아챌 수 있게 한다.
const LOWEST_COLS = ['확인시각', '검색어', '순위', '상품ID(nv_mid)', '상품명', '최저가', '배송비', '판매처수', '평점', '리뷰수', '링크', '판매처', '수량', '관련'];
const LOWEST_SUM_COLS = ['확인시각', '검색어', '1개 최저 상품ID', '1개 최저 판매처', '1개 최저가', '개당 최저가', '상품수', '상태', '메시지'];
const LOWEST_KEEP_ROWS = 100000; // '최저가' 상세는 최근 이만큼만 (시트 1000만 칸 한도 대비, 약 2주치)
const LOWEST_DAYS = 30;          // 화면 추이 차트에 보여줄 기간
const ONLINE_MS = 3 * 60000;     // 모니터·관리 프로그램이 이만큼 연락이 없으면 끊김
const STUCK_MIN = 5;             // running 상태로 이만큼 지난 요청은 처리하던 프로그램이 죽은 것
const STALE_PRICE_H = 3;         // 마지막 성공 확인이 이만큼 지나면 가격이 오래됨
const LATE_MIN = 15;             // 다음 정기 확인 예정 시각을 이만큼 넘기면 늦음
const CLOCK_SKEW_MIN = 5;        // PC 시계 오차 허용

function sheet_(ss, name, header) {
  let sh = ss.getSheetByName(name);
  if (!sh) {
    sh = ss.insertSheet(name);
    sh.appendRow(header);
    sh.setFrozenRows(1);
  } else if (sh.getRange(1, 1, 1, header.length).getValues()[0].join('|') !== header.join('|')) { // 예전 머리글 → 새 머리글
    sh.getRange(1, 1, 1, header.length).setValues([header]);
  }
  return sh;
}

function ms_(v) {
  return v instanceof Date ? v.getTime() : new Date(String(v || '')).getTime();
}

function txt_(s) { // 상품명이 = + - @ 로 시작하면 수식으로 들어가지 않게
  s = String(s == null ? '' : s);
  return /^[=+\-@]/.test(s) ? "'" + s : s;
}

function blank_(v) {
  return v === null || v === undefined ? '' : v;
}

/** running 으로 STUCK_MIN 넘게 남은 요청을 실패로 정리 (처리하던 프로그램이 죽었거나 완료 표시를 못 보낸 것) */
function failStuck_(ss, type, why) {
  const sh = ss.getSheetByName('요청');
  const rows = sh.getDataRange().getValues();
  for (let i = 1; i < rows.length; i++) {
    if (rows[i][1] === type && rows[i][5] === 'running' && Date.now() - ms_(rows[i][4]) > STUCK_MIN * 60000) {
      sh.getRange(i + 1, 6, 1, 4).setValues([['error', rows[i][6], JSON.stringify({ error: why }), new Date().toISOString()]]);
    }
  }
}

function crawlPull_(ss, status, taker) {
  const props = { lowestSeen: new Date().toISOString() };
  if (status) props.lowestStatus = JSON.stringify(status).slice(0, 8000);
  PropertiesService.getScriptProperties().setProperties(props);
  failStuck_(ss, 'crawl', '모니터가 처리하다 멈췄어요 (그 사이 모니터가 다시 켜짐). 다시 눌러 주세요');
  return { ok: true, requests: takePending_(ss, 'crawl', taker).map(function (r) { return String(r[0]); }) };
}

/** 대기 중인 요청을 running 으로 바꾸며 가져온다.
 *  taker = 가져가는 쪽이 한 번 부를 때마다 새로 만드는 id. 응답이 중간에 끊겨 같은 호출을 다시 보내면
 *  (taker 가 같으면) 이미 running 으로 바꾼 요청을 다시 돌려준다 → 응답 유실로 요청이 사라지지 않음 */
function takePending_(ss, type, taker) {
  const sh = ss.getSheetByName('요청');
  const rows = sh.getDataRange().getValues();
  const out = [];
  for (let i = 1; i < rows.length; i++) {
    if (rows[i][1] !== type) continue;
    if (rows[i][5] === 'pending') {
      out.push(rows[i]);
      sh.getRange(i + 1, 6, 1, 3).setValues([['running', rows[i][6], taker ? JSON.stringify({ taker: String(taker) }) : '']]);
    } else if (taker && rows[i][5] === 'running' && String(rows[i][7]).indexOf('"taker":"' + taker + '"') >= 0) {
      out.push(rows[i]);
    }
  }
  return out;
}

// ── 모니터 관리 프로그램 (monitor_supervisor.py, PC 작업 스케줄러가 1분마다 실행) ──
const MONITOR_ACTIONS = { restart: '재시작', stop: '중지' };

function supPull_(ss, status, take, taker) {
  const props = { supSeen: new Date().toISOString() };
  if (status) props.supStatus = JSON.stringify(status).slice(0, 8000);
  PropertiesService.getScriptProperties().setProperties(props);
  if (!take) return { ok: true, requests: [] };
  failStuck_(ss, 'monitor', '관리 프로그램이 처리하다 멈췄어요. 다시 눌러 주세요');
  return { ok: true, requests: takePending_(ss, 'monitor', taker).map(function (r) { return { id: String(r[0]), action: r[2], by: r[3] }; }) };
}

function busy_(ss, type, minutes) {
  const rows = ss.getSheetByName('요청').getDataRange().getValues();
  for (let i = rows.length - 1; i >= 1; i--) {
    if (rows[i][1] === type && (rows[i][5] === 'pending' || rows[i][5] === 'running') &&
        Date.now() - ms_(rows[i][4]) < minutes * 60000) return String(rows[i][0]);
  }
  return null;
}

/** 모니터를 다시 켜거나(restart) 끄라고(stop) 관리 프로그램에 요청한다 */
function requestMonitor(code, action) {
  code = check_(code);
  if (!Object.prototype.hasOwnProperty.call(MONITOR_ACTIONS, action)) throw new Error('없는 동작이에요');
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const ss = book_();
    return busy_(ss, 'monitor', STUCK_MIN) || newRequest_(ss, 'monitor', action, code, null);
  } finally {
    lock.releaseLock();
  }
}

function prop_(p, k) {
  try { return JSON.parse(p[k] || 'null'); } catch (e) { return null; }
}

function ago_(t) {
  const m = Math.round((Date.now() - t) / 60000);
  return m < 60 ? m + '분' : m < 2880 ? Math.round(m / 60) + '시간' : Math.round(m / 1440) + '일';
}

/** 모니터·관리 프로그램 상태와 '최저가요약' 최근 기록을 한 번에 읽는다 (화면 여러 곳이 같이 씀) */
function lowestState_(ss) {
  const p = PropertiesService.getScriptProperties().getProperties();
  const st = {
    now: Date.now(),
    mon: { seen: p.lowestSeen || '', status: prop_(p, 'lowestStatus') || {} },
    sup: { seen: p.supSeen || '', status: prop_(p, 'supStatus') || {} },
    Q: {}, reqs: ss.getSheetByName('요청').getDataRange().getValues(),
  };
  st.mon.on = !!st.mon.seen && st.now - ms_(st.mon.seen) < ONLINE_MS;
  st.sup.on = !!st.sup.seen && st.now - ms_(st.sup.seen) < ONLINE_MS;
  const sum = ss.getSheetByName('최저가요약');
  if (sum && sum.getLastRow() > 1) {
    const n = Math.min(sum.getLastRow() - 1, 3000);
    sum.getRange(sum.getLastRow() - n + 1, 1, n, LOWEST_SUM_COLS.length).getValues().forEach(function (r) {
      const q = st.Q[r[1]] = st.Q[r[1]] || [];
      q.push({ t: ms_(r[0]), top: r[4] === '' ? null : Number(r[4]), min: r[5] === '' ? null : Number(r[5]),
        count: Number(r[6]) || 0, status: String(r[7] || 'ok'), msg: String(r[8] || '') });
    });
    Object.keys(st.Q).forEach(function (k) { st.Q[k].sort(function (a, b) { return a.t - b.t; }); });
  }
  // 모니터가 지금 감시하는 검색어 (목록에서 빠진 검색어 카드는 숨긴다)
  const watched = st.mon.status.queries && st.mon.status.queries.length ? st.mon.status.queries : Object.keys(st.Q);
  st.watched = watched.slice().sort();
  return st;
}

/** 검색어 하나의 상태: ok | warn | crit 와 화면에 보일 설명 */
function queryHealth_(st, rows) {
  if (!rows || !rows.length) return { level: 'warn', title: '아직 기록 없음', detail: '모니터가 첫 확인을 하면 보여요', fails: 0 };
  const last = rows[rows.length - 1];
  let ok = null, fails = 0;
  for (let i = rows.length - 1; i >= 0; i--) {
    if (rows[i].status !== 'error') { ok = rows[i]; break; }
    fails++;
  }
  const h = { fails: fails, lastOkAt: ok ? new Date(ok.t).toISOString() : null, lastAttemptAt: new Date(last.t).toISOString(),
    level: 'ok', title: '정상', detail: '' };
  if (last.status === 'error') {
    h.level = 'crit';
    h.title = '확인 실패' + (fails > 1 ? ' ' + fails + '회 연속' : '');
    h.detail = last.msg + (ok ? ' · 화면의 가격은 ' + ago_(ok.t) + ' 전 마지막 성공 기준이에요' : ' · 성공한 기록이 아직 없어요');
  } else if (last.status === 'warn') {
    h.level = 'warn';
    h.title = '결과 확인 필요';
    h.detail = last.msg;
  }
  if (ok && st.now - ok.t > STALE_PRICE_H * 3600e3 && h.level !== 'crit') {
    h.level = 'crit';
    h.title = '가격이 ' + ago_(ok.t) + '째 갱신 안 됨';
    h.detail = '마지막 성공 확인 ' + ago_(ok.t) + ' 전' + (st.mon.on ? '' : ' · 모니터가 끊겨 있어요');
  }
  return h;
}

/** 지금 알아야 할 문제 목록 (crit 먼저). 최저가 탭·모니터 탭·탭 배지가 같이 쓴다 */
function issues_(st) {
  const out = [];
  const add = function (level, title, detail, where) { out.push({ level: level, title: title, detail: detail || '', where: where || 'monitor' }); };
  const ms = st.mon.status, sp = st.sup.status;
  if (!st.mon.on) {
    const since = st.mon.seen ? ' (' + ago_(ms_(st.mon.seen)) + ' 전 마지막 연락)' : '';
    if (!st.mon.seen) add('crit', '최저가 모니터가 아직 연결된 적이 없어요', 'PC에서 naver_price_monitor.py 와 .env 설정을 확인해 주세요');
    else if (st.sup.on && sp.stoppedByUser && !sp.alive) add('warn', '최저가 모니터를 [중지]로 꺼 두었어요', '정기 확인과 [업데이트]가 멈춰 있어요. 모니터 탭에서 [시작]을 누르면 다시 켜져요');
    else if (st.sup.on && sp.alive) add('crit', '최저가 모니터가 멈췄어요' + since, '프로세스는 있는데 웹사이트에 연락이 없어요. [재시작]을 눌러 주세요');
    else if (st.sup.on) add('crit', '최저가 모니터가 꺼져 있어요' + since, '관리 프로그램이 1~5분 안에 자동으로 켜요. 계속 꺼지면 로그를 확인해 주세요');
    else add('crit', '최저가 모니터와 PC 연결이 모두 끊겼어요' + since, 'PC가 꺼짐·절전·로그아웃 상태이거나 인터넷이 끊겼어요');
  }
  if (!st.sup.on) {
    add(st.mon.on ? 'warn' : 'crit', '관리 프로그램(PC) 연결이 끊겼어요' + (st.sup.seen ? ' (' + ago_(ms_(st.sup.seen)) + ' 전)' : ''),
      '재시작·자동 시작을 할 수 없어요. PC가 켜져 있는지, 작업 스케줄러의 "AI_resell 최저가 모니터 관리"가 살아 있는지 확인해 주세요');
  } else {
    if (sp.autoStartsLastHour >= 2) add('crit', '모니터가 계속 꺼져요 (최근 1시간 자동 시작 ' + sp.autoStartsLastHour + '회)',
      sp.lastStartError || '모니터 탭의 최근 로그에서 오류를 확인해 주세요');
    else if (sp.lastStartError) add('crit', '모니터를 켜지 못했어요', sp.lastStartError);
    if (sp.pids && sp.pids.length > 1) add('warn', '모니터가 ' + sp.pids.length + '개 실행 중이에요', '관리 프로그램이 1분 안에 하나만 남기고 꺼요');
  }
  if (st.mon.on) {
    (ms.errors || []).filter(function (e) { return e.indexOf('모니터 내부 오류') === 0; })
      .forEach(function (e) { add('crit', '모니터 내부 오류', e + ' · 로그를 확인해 주세요'); });
    if (ms.unsent > 0) add('warn', '웹사이트로 못 보낸 확인 결과 ' + ms.unsent + '개', '모니터가 다음 확인 때 다시 보내요. 계속되면 구글 시트 용량·Apps Script 할당량을 확인해 주세요');
    if (ms.now) {
      const skew = Math.round((ms_(st.mon.seen) - ms_(ms.now)) / 60000);
      if (Math.abs(skew) > CLOCK_SKEW_MIN) add('warn', 'PC 시계가 ' + Math.abs(skew) + '분 ' + (skew > 0 ? '느려요' : '빨라요'), '확인 시각이 틀리게 기록돼요. Windows 시간 동기화를 확인해 주세요');
    }
    if (ms.nextDueAt && st.now - ms_(ms.nextDueAt) > LATE_MIN * 60000) {
      add('warn', '정기 확인이 예정보다 ' + ago_(ms_(ms.nextDueAt)) + ' 늦어요', '모니터가 한 확인에서 멈춰 있을 수 있어요. 계속되면 [재시작]해 주세요');
    }
  }
  st.watched.forEach(function (q) {
    const h = queryHealth_(st, st.Q[q]);
    if (h.level !== 'ok') add(h.level, q + ' · ' + h.title, h.detail, q);
  });
  [['crawl', st.mon.on, '최저가 업데이트'], ['monitor', st.sup.on, '모니터 재시작/중지']].forEach(function (x) {
    const stuck = st.reqs.filter(function (r) { return r[1] === x[0] && (r[5] === 'running' || r[5] === 'pending') && st.now - ms_(r[4]) > STUCK_MIN * 60000; });
    if (stuck.length) add('warn', x[2] + ' 요청 ' + stuck.length + '건이 처리되지 않고 있어요', x[1] ? '곧 자동으로 정리돼요' : '처리할 프로그램이 끊겨 있어요');
  });
  const rank = { crit: 0, warn: 1 };
  return out.sort(function (a, b) { return rank[a.level] - rank[b.level]; });
}

/** load() 에 붙는 짧은 요약 (탭 배지용) */
function lowestBadge_(ss) {
  try {
    const is = issues_(lowestState_(ss));
    return { crit: is.filter(function (i) { return i.level === 'crit'; }).length, warn: is.filter(function (i) { return i.level === 'warn'; }).length };
  } catch (e) {
    return null;
  }
}

/** 모니터 탭: 모니터·관리 프로그램 연결 상태, 마지막 확인, 문제 목록, 최근 요청 */
function loadMonitor(code) {
  check_(code);
  const ss = book_();
  const st = lowestState_(ss);
  let last = null;
  Object.keys(st.Q).forEach(function (k) { const r = st.Q[k][st.Q[k].length - 1]; if (r && (!last || r.t > last)) last = r.t; });
  const reqs = [];
  for (let i = st.reqs.length - 1; i >= 1 && reqs.length < 15; i--) {
    const r = st.reqs[i];
    if (r[1] !== 'crawl' && r[1] !== 'monitor') continue;
    let res = null;
    try { res = r[7] ? JSON.parse(r[7]) : null; } catch (e) {}
    reqs.push({ id: String(r[0]), type: r[1], action: r[1] === 'monitor' ? r[2] : 'crawl', by: String(r[3]), at: iso_(r[4]),
      status: r[5], message: res && (res.message || res.error) || '', doneAt: iso_(r[8]) });
  }
  return {
    now: new Date(st.now).toISOString(),
    monitor: { seen: st.mon.seen, status: st.mon.status },
    sup: { seen: st.sup.seen, status: st.sup.status },
    lastCycle: last ? new Date(last).toISOString() : null,
    busy: busy_(ss, 'monitor', STUCK_MIN),
    issues: issues_(st),
    requests: reqs,
  };
}

/** cycles = [{at, query, items:[...], status: ok|warn|error, message}]. 같은 시각·검색어는 건너뛴다.
 *  status=error 는 items 없이 요약에만 남긴다 (화면이 "확인 실패"를 보여줄 수 있게) */
function saveLowest_(ss, cycles) {
  if (!cycles || !cycles.length) return { ok: false, error: 'no cycles' };
  const det = sheet_(ss, '최저가', LOWEST_COLS);
  const sum = sheet_(ss, '최저가요약', LOWEST_SUM_COLS);
  const have = {};
  if (sum.getLastRow() > 1) {
    sum.getRange(2, 1, sum.getLastRow() - 1, 2).getValues().forEach(function (r) { have[ms_(r[0]) + '|' + r[1]] = true; });
  }
  const dRows = [], sRows = [];
  let skipped = 0;
  cycles.forEach(function (c) {
    const key = ms_(c.at) + '|' + c.query;
    const items = c.items || [];
    const status = c.status === 'error' || c.status === 'warn' ? c.status : (items.length ? 'ok' : 'error');
    if (!c.query || !isFinite(ms_(c.at)) || have[key]) { skipped++; return; }
    have[key] = true;
    if (status === 'error' || !items.length) {
      sRows.push([c.at, c.query, '', '', '', '', 0, 'error', txt_(String(c.message || '결과 없음').slice(0, 500))]);
      return;
    }
    items.forEach(function (p, i) {
      dRows.push([c.at, c.query, i + 1, String(p.nv_mid), txt_(p.title), blank_(p.price), txt_(p.shipping), blank_(p.sellers),
        blank_(p.rating), blank_(p.review_count), String(p.link || ''), txt_(p.mall || ''), Number(p.qty) || 1, p.rel === false ? 'N' : 'Y']);
    });
    // 요약: 같은 상품(관련)만, 1개짜리 최저가와 묶음 포함 개당 최저가 (수량이 의심스러운 건 개당 계산에서 뺀다)
    const ok = items.filter(function (p) { return p.rel !== false && p.price > 0; });
    const one = ok.filter(function (p) { return (Number(p.qty) || 1) === 1; }).sort(function (a, b) { return a.price - b.price; })[0];
    const units = ok.filter(function (p) { return p.qty_ok !== false; }).map(function (p) { return Math.round(p.price / (Number(p.qty) || 1)); });
    sRows.push([c.at, c.query, one ? String(one.nv_mid) : '', one ? txt_(one.mall || '가격비교') : '', one ? one.price : '',
      units.length ? Math.min.apply(null, units) : '', items.length, status, txt_(String(c.message || '').slice(0, 500))]);
  });
  if (dRows.length) det.getRange(det.getLastRow() + 1, 1, dRows.length, LOWEST_COLS.length).setValues(dRows);
  if (det.getLastRow() > LOWEST_KEEP_ROWS * 1.2) det.deleteRows(2, det.getLastRow() - 1 - LOWEST_KEEP_ROWS); // 오래된 상세부터 정리
  if (sRows.length) sum.getRange(sum.getLastRow() + 1, 1, sRows.length, LOWEST_SUM_COLS.length).setValues(sRows);
  return { ok: true, added: sRows.length, skipped: skipped };
}

/** 지금 최저가를 다시 확인해 달라고 요청한다. 이미 진행 중인 요청이 있으면 그걸 돌려준다 */
function requestCrawl(code) {
  code = check_(code);
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const ss = book_();
    const busy = crawlBusy_(ss);
    return busy || newRequest_(ss, 'crawl', 'all', code, null);
  } finally {
    lock.releaseLock();
  }
}

function crawlBusy_(ss) {
  return busy_(ss, 'crawl', STUCK_MIN);
}

/** 최저가 탭: 검색어별 마지막 성공 목록(직전 성공 대비 변동)과 추이, 확인 실패·이상 상태 */
function loadLowest(code) {
  check_(code);
  const ss = book_();
  const st = lowestState_(ss);
  const res = { seen: st.mon.seen, monOn: st.mon.on, busy: crawlBusy_(ss), issues: issues_(st), queries: [] };
  const det = ss.getSheetByName('최저가');
  const byCycle = {};
  if (det && det.getLastRow() > 1) { // 상세는 최근 3000줄 안에서
    const m = Math.min(det.getLastRow() - 1, 3000);
    det.getRange(det.getLastRow() - m + 1, 1, m, LOWEST_COLS.length).getValues().forEach(function (r) {
      const k = ms_(r[0]) + '|' + r[1];
      (byCycle[k] = byCycle[k] || []).push(r);
    });
  }
  const since = st.now - LOWEST_DAYS * 864e5;
  st.watched.forEach(function (name) {
    const rows = st.Q[name] || [];
    const okRows = rows.filter(function (r) { return r.status !== 'error'; });
    const cur = okRows[okRows.length - 1], prv = okRows[okRows.length - 2];
    const prev = {};
    (prv && byCycle[prv.t + '|' + name] || []).forEach(function (r) { if (r[5] !== '') prev[String(r[3])] = Number(r[5]); });
    res.queries.push({
      query: name,
      health: queryHealth_(st, rows),
      at: cur ? new Date(cur.t).toISOString() : null,
      prevAt: prv ? new Date(prv.t).toISOString() : null,
      warn: cur && cur.status === 'warn' ? cur.msg : '',
      // 추이: 성공한 확인만 점으로, 실패한 확인은 시각만 (차트에 빨간 표시)
      series: rows.filter(function (r) { return r.t >= since; }).map(function (r) {
        return [new Date(r.t).toISOString(), r.status === 'error' ? null : r.top, r.status === 'error' ? null : r.min, r.status === 'error' ? 1 : 0];
      }),
      items: (cur && byCycle[cur.t + '|' + name] || []).map(function (r) {
        const id = String(r[3]);
        return {
          rank: Number(r[2]), id: id, title: String(r[4]), price: r[5] === '' ? null : Number(r[5]),
          prev: Object.prototype.hasOwnProperty.call(prev, id) ? prev[id] : null,
          ship: String(r[6]), sellers: r[7] === '' ? null : Number(r[7]), rating: r[8] === '' ? null : Number(r[8]),
          reviews: r[9] === '' ? null : Number(r[9]), link: String(r[10]),
          mall: String(r[11] || ''), qty: Number(r[12]) || null, rel: r[13] !== 'N',
        };
      }),
    });
  });
  return res;
}

// ── 신상품 발굴 (sourcing/daemon.py) ─────────────────────────────
// 작업기가 맘이베베 핫딜 -> 네이버쇼핑 카탈로그 매칭 -> 추천도를 계산해 op=sourcing 으로 보낸다 (글 번호로 덮어쓰기).
// 경쟁도는 처음엔 검색결과 근사치. 사람이 가격비교 페이지에서 북마클릿을 누르면 '발굴경쟁'에 실제 판매처 목록이 쌓이고
// 화면에서는 그 값으로 경쟁 규칙을 다시 매긴다.
const SRC_COLS = ['글번호', '작성시각', '쇼핑몰', '상품명', '핫딜가', '환산핫딜가', '상태', '카탈로그ID', '카탈로그명', '카탈로그최저가',
  '판매처수', '리뷰수', '근처판매처', '비교판매처', '1-2위차', '경쟁출처', '매칭', '점수', '별', '규칙(JSON)', '기록최저가',
  '카탈로그링크', '글링크', '확인시각', '원제목'];
const SRC_KEYS = ['articleId', 'postedAt', 'mall', 'name', 'dealPrice', 'dealPriceNorm', 'status', 'nvMid', 'catTitle', 'catPrice',
  'sellers', 'reviews', 'near', 'offers', 'gap12', 'compSource', 'matchConf', 'points', 'stars', 'rules', 'histLow',
  'catLink', 'articleUrl', 'checkedAt', 'subject'];
const SRC_EXACT_COLS = ['시각', '카탈로그ID', '가져온 사람', '근처판매처', '판매처수', '1-2위차', '최저가', '판매처 목록(JSON)', '페이지'];
const SRC_RULE = { gapWon: 1000, gapPct: 1, max: 3, pts: 1 }; // sourcing/config.py RULES 의 compete_* 와 같게
const SRC_STARS = [[5, 5], [4, 4], [3, 3], [2, 2], [0, 1]];
const SRC_SHOW_ROWS = 800;

function saveSourcing_(ss, items, status) {
  if (status) PropertiesService.getScriptProperties().setProperty('srcStatus', JSON.stringify(status));
  if (!items.length) return { ok: true, added: 0, updated: 0 };
  const sh = sheet_(ss, '발굴', SRC_COLS);
  const n = sh.getLastRow() - 1;
  const where = {};
  if (n > 0) sh.getRange(2, 1, n, 1).getValues().forEach(function (r, i) { where[String(r[0])] = i + 2; });
  let added = 0, updated = 0;
  const fresh = [];
  items.forEach(function (it) {
    const row = SRC_KEYS.map(function (k) {
      const v = it[k];
      if (k === 'rules') return JSON.stringify(v || []);
      if (v === null || v === undefined) return '';
      return typeof v === 'string' ? txt_(v) : v;
    });
    const at = where[String(it.articleId)];
    if (at) { sh.getRange(at, 1, 1, row.length).setValues([row]); updated++; }
    else { fresh.push(row); added++; }
  });
  if (fresh.length) sh.getRange(sh.getLastRow() + 1, 1, fresh.length, SRC_COLS.length).setValues(fresh);
  return { ok: true, added: added, updated: updated };
}

function srcStars_(p) {
  for (let i = 0; i < SRC_STARS.length; i++) if (p >= SRC_STARS[i][0]) return SRC_STARS[i][1];
  return 1;
}

function captureSourcing_(d, who) {
  const m = String(d.url || '').match(/catalog\/(\d+)/);
  if (!m) return capturePage_('가격비교 페이지가 아니에요', '<p>네이버 가격비교(카탈로그) 페이지에서 눌러 주세요.</p>');
  const id = m[1];
  const prices = (d.items || []).map(function (x) {
    return { mall: String(x.mall || '').slice(0, 30), price: Math.round(Number(x.price)) || 0 };
  }).filter(function (x) { return x.price > 0; }).sort(function (a, b) { return a.price - b.price; });
  if (!prices.length) return capturePage_('판매처 목록이 비었어요', '<p>페이지를 끝까지 연 뒤 다시 눌러 주세요.</p>');
  const low = prices[0].price;
  const gap = Math.max(SRC_RULE.gapWon, low * SRC_RULE.gapPct / 100);
  const near = prices.filter(function (x) { return x.price - low <= gap; }).length;
  const gap12 = prices.length > 1 ? prices[1].price - prices[0].price : '';
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  let known = false;
  try {
    const ss = book_();
    const src = ss.getSheetByName('발굴');
    if (src && src.getLastRow() > 1) {
      known = src.getRange(2, 8, src.getLastRow() - 1, 1).getValues().some(function (r) { return String(r[0]) === id; });
    }
    if (!known) return capturePage_('발굴 목록에 없는 상품이에요', '<p>신상품 발굴 탭에 있는 상품의 가격비교 페이지에서 눌러 주세요. (키즈데이 포도·사과·칼마디는 경쟁사로 저장돼요)</p>');
    sheet_(ss, '발굴경쟁', SRC_EXACT_COLS).appendRow([new Date().toISOString(), id, who, near, prices.length, gap12, low,
      JSON.stringify(prices.slice(0, 60)), String(d.url || '').slice(0, 200)]);
  } finally {
    lock.releaseLock();
  }
  const calm = near < SRC_RULE.max;
  return capturePage_('정확한 경쟁도를 저장했어요',
    '<p>최저가 <b>' + low.toLocaleString() + '원</b> · 판매처 ' + prices.length + '곳</p>' +
    '<p>최저가 근처(' + Math.round(gap).toLocaleString() + '원 이내) 판매처 <b>' + near + '곳</b> → ' + (calm ? '경쟁 약함 (+1점)' : '경쟁 심함 (0점)') + '</p>');
}

/** 신상품 발굴 탭: 최근 발굴 목록 + 사람이 가져온 정확한 경쟁도 반영 */
function loadSourcing(code) {
  check_(code);
  const ss = book_();
  const sh = ss.getSheetByName('발굴');
  const exact = {};
  const ex = ss.getSheetByName('발굴경쟁');
  if (ex && ex.getLastRow() > 1) {
    ex.getRange(2, 1, ex.getLastRow() - 1, 7).getValues().forEach(function (r) { // 아래쪽(최신)이 덮어쓴다
      exact[String(r[1])] = { at: iso_(r[0]), who: String(r[2]), near: Number(r[3]), offers: Number(r[4]), gap12: r[5] === '' ? null : Number(r[5]), low: Number(r[6]) };
    });
  }
  const items = [];
  let noCat = 0;
  if (sh && sh.getLastRow() > 1) {
    const n = Math.min(sh.getLastRow() - 1, SRC_SHOW_ROWS);
    sh.getRange(sh.getLastRow() - n + 1, 1, n, SRC_COLS.length).getValues().forEach(function (r) {
      const it = {};
      SRC_KEYS.forEach(function (k, i) { it[k] = r[i] === '' ? null : (r[i] instanceof Date ? r[i].toISOString() : r[i]); });
      if (it.status !== 'ok') { noCat++; return; }
      it.articleId = String(it.articleId); it.nvMid = String(it.nvMid);
      it.rules = JSON.parse(it.rules || '[]');
      const e = exact[it.nvMid];
      if (e) {
        it.exact = e;
        const calm = e.near < SRC_RULE.max;
        it.rules.forEach(function (x) {
          if (x.rule !== '경쟁 약함') return;
          it.points += (calm ? SRC_RULE.pts : 0) - (x.pts || 0);
          x.ok = calm; x.pts = calm ? SRC_RULE.pts : 0;
          x.why = '최저가 근처 판매처 ' + e.near + '곳 / 전체 ' + e.offers + '곳 (가격비교 페이지 실제값)';
        });
        it.stars = srcStars_(it.points);
      }
      items.push(it);
    });
  }
  items.reverse();
  const st = PropertiesService.getScriptProperties().getProperty('srcStatus');
  return { items: items, noCatalog: noCat, status: st ? JSON.parse(st) : null, appUrl: ScriptApp.getService().getUrl() };
}
