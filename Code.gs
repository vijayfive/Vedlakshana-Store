/**
 * Vedlakshana Store — Google Apps Script backend.
 * Turns a Google Sheet into a free JSON read/write API for the app.
 *
 * SETUP (see SETUP.md for the full walkthrough):
 * 1. Create a Google Sheet with 5 tabs named exactly:
 *      Settings, Products, Sales, Purchases, Expenses
 * 2. Extensions > Apps Script, paste this whole file in as Code.gs
 * 3. Change WRITE_TOKEN below to your own secret string
 * 4. Deploy > New deployment > Web app
 *      Execute as: Me
 *      Who has access: Anyone
 * 5. Copy the Web app URL into the app's index.html (SCRIPT_URL) and
 *    put the same WRITE_TOKEN value into WRITE_TOKEN there too.
 */

var WRITE_TOKEN = 'siddhnathmahadevkijay';

function doGet(e) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  ensureSheets(ss);
  return jsonOut(readState(ss));
}

function doPost(e) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  ensureSheets(ss);
  var body;
  try {
    body = JSON.parse(e.postData.contents);
  } catch (err) {
    return jsonOut({ ok: false, error: 'bad_request' });
  }
  if (body.token !== WRITE_TOKEN) {
    return jsonOut({ ok: false, error: 'unauthorized' });
  }
  writeState(ss, body.state);
  return jsonOut({ ok: true });
}

function ensureSheets(ss) {
  ['Settings', 'Products', 'Sales', 'Purchases', 'Expenses'].forEach(function (name) {
    if (!ss.getSheetByName(name)) ss.insertSheet(name);
  });
}

function readState(ss) {
  var settingsRows = ss.getSheetByName('Settings').getDataRange().getValues();
  var settings = {};
  settingsRows.forEach(function (row) {
    if (row[0]) settings[row[0]] = row[1];
  });

  var productRows = ss.getSheetByName('Products').getDataRange().getValues();
  var products = productRows.slice(1).filter(function (r) { return r[0]; }).map(function (r) {
    return { id: String(r[0]), name: String(r[1]), price: Number(r[2]) || 0, costPrice: Number(r[3]) || 0, stock: Number(r[4]) || 0 };
  });

  var saleRows = ss.getSheetByName('Sales').getDataRange().getValues();
  var sales = saleRows.slice(1).filter(function (r) { return r[0]; }).map(function (r) {
    var items = [];
    try { items = JSON.parse(r[2]); } catch (err) { items = []; }
    return {
      id: String(r[0]), ts: Number(r[1]) || 0, items: items, total: Number(r[3]) || 0,
      paymentMethod: String(r[4] || 'Cash'), customerName: String(r[5] || ''), customerPhone: String(r[6] || '')
    };
  });

  var purchaseRows = ss.getSheetByName('Purchases').getDataRange().getValues();
  var purchases = purchaseRows.slice(1).filter(function (r) { return r[0]; }).map(function (r) {
    return {
      id: String(r[0]), ts: Number(r[1]) || 0, productId: String(r[2]), productName: String(r[3]),
      qty: Number(r[4]) || 0, costPrice: Number(r[5]) || 0, total: Number(r[6]) || 0
    };
  });

  var expenseRows = ss.getSheetByName('Expenses').getDataRange().getValues();
  var expenses = expenseRows.slice(1).filter(function (r) { return r[0]; }).map(function (r) {
    return { id: String(r[0]), ts: Number(r[1]) || 0, description: String(r[2] || ''), amount: Number(r[3]) || 0, category: String(r[4] || 'Misc') };
  });

  return {
    storeName: settings.storeName || 'Vedlakshana Store',
    pin: String(settings.pin || '1234'),
    lowStockThreshold: Number(settings.lowStockThreshold) || 5,
    products: products,
    sales: sales,
    purchases: purchases,
    expenses: expenses
  };
}

function writeState(ss, state) {
  state = state || {};
  var products = state.products || [];
  var sales = state.sales || [];
  var purchases = state.purchases || [];
  var expenses = state.expenses || [];

  var settingsSheet = ss.getSheetByName('Settings');
  settingsSheet.clearContents();
  settingsSheet.appendRow(['key', 'value']);
  settingsSheet.appendRow(['storeName', state.storeName || 'Vedlakshana Store']);
  settingsSheet.appendRow(['pin', state.pin || '1234']);
  settingsSheet.appendRow(['lowStockThreshold', state.lowStockThreshold || 5]);

  var productsSheet = ss.getSheetByName('Products');
  productsSheet.clearContents();
  productsSheet.appendRow(['id', 'name', 'price', 'costPrice', 'stock']);
  products.forEach(function (p) {
    productsSheet.appendRow([p.id, p.name, p.price, p.costPrice || 0, p.stock]);
  });

  var salesSheet = ss.getSheetByName('Sales');
  salesSheet.clearContents();
  salesSheet.appendRow(['id', 'timestamp', 'items', 'total', 'paymentMethod', 'customerName', 'customerPhone']);
  sales.forEach(function (s) {
    salesSheet.appendRow([s.id, s.ts, JSON.stringify(s.items), s.total, s.paymentMethod || 'Cash', s.customerName || '', s.customerPhone || '']);
  });

  var purchasesSheet = ss.getSheetByName('Purchases');
  purchasesSheet.clearContents();
  purchasesSheet.appendRow(['id', 'timestamp', 'productId', 'productName', 'qty', 'costPrice', 'total']);
  purchases.forEach(function (x) {
    purchasesSheet.appendRow([x.id, x.ts, x.productId, x.productName, x.qty, x.costPrice, x.total]);
  });

  var expensesSheet = ss.getSheetByName('Expenses');
  expensesSheet.clearContents();
  expensesSheet.appendRow(['id', 'timestamp', 'description', 'amount', 'category']);
  expenses.forEach(function (x) {
    expensesSheet.appendRow([x.id, x.ts, x.description, x.amount, x.category || 'Misc']);
  });
}

function jsonOut(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
