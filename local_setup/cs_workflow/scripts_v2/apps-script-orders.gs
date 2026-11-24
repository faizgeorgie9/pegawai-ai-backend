// Colorbox demo — order writer (no Google Cloud / service account needed).
// Paste this into the Orders sheet: Extensions -> Apps Script, replace all code, Save.
// Then Deploy -> New deployment -> Web app:
//   Description: colorbox-orders
//   Execute as: Me
//   Who has access: Anyone
// Deploy, authorize, and copy the Web app URL (ends with /exec). Send me that URL.

function doPost(e) {
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(10000);
  } catch (err) {
    return json({ ok: false, error: "busy" });
  }
  try {
    var body = JSON.parse(e.postData.contents);
    var values = body.row; // array in the sheet's own column order
    if (!values || !values.length) {
      return json({ ok: false, error: "empty row" });
    }
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
    sheet.appendRow(values);
    return json({ ok: true, row: values });
  } catch (err) {
    return json({ ok: false, error: String(err) });
  } finally {
    lock.releaseLock();
  }
}

function doGet() {
  return json({ ok: true, service: "colorbox-orders" });
}

function json(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
