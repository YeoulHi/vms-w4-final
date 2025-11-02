# 002. Excel Upload - Test Guide

**Document Version:** 1.0
**Created:** 2025-11-03
**Scope:** UserFlow #02 - Admin Excel Upload Feature Testing

---

## 📋 Overview

This guide provides step-by-step instructions for testing the Excel/CSV upload feature in Django Admin.

**Objectives:**
- Verify file upload validation (extension, columns)
- Test data parsing and normalization
- Confirm database UPSERT functionality
- Validate error handling and partial commit

---

## 🔧 Prerequisites

### Required Setup
```bash
# Ensure SQLite is enabled
$env:USE_SQLITE="true"

# Start development server
python manage.py runserver
```

### Test Data & Accounts
- **Admin Account:** username=`admin`, password=`admin123!`
- **Test Database:** SQLite (db.sqlite3)
- **Existing Data:** 5 MetricRecord entries (from manual test)

---

## ✅ Test Cases

### TC-01: Valid Excel File Upload

**Objective:** Upload valid Excel file with correct data format

**Steps:**
1. Navigate to `/admin/`
2. Login as admin
3. Click **Ingest > Metric records** in sidebar
4. Click **Upload** button (top right or custom URL)
5. Select valid Excel file:
   ```
   year | department | metric_type | value
   2025 | computer-science | PAPER | 20
   2025 | computer-science | BUDGET | 70000
   2025 | electronics | PAPER | 15
   ```
6. Click **Submit**

**Expected Result:**
- ✅ Success message: "Upload complete: Total 3 rows: 3 success, 0 failed"
- ✅ Redirect to MetricRecord list
- ✅ New records visible in list view
- ✅ `updated_at` timestamp auto-updated

**Verification:**
```bash
# Check database
python manage.py shell
>>> from apps.ingest.models import MetricRecord
>>> MetricRecord.objects.filter(year=2025).count()
# Expected: 3
>>> exit()
```

---

### TC-02: UPSERT - Update Existing Records

**Objective:** Verify existing records are updated, not duplicated

**Steps:**
1. Upload same file twice with different values:
   ```
   year | department | metric_type | value
   2025 | computer-science | PAPER | 25  (was 20)
   ```
2. Check MetricRecord count before and after

**Expected Result:**
- ✅ No duplicate records created
- ✅ `metric_value` updated from 20 to 25
- ✅ `updated_at` timestamp changed
- ✅ Message: "Total 1 rows: 1 success, 0 failed"

**Verification:**
```bash
python manage.py shell
>>> MetricRecord.objects.filter(year=2025, department="computer-science", metric_type="PAPER").count()
# Expected: 1 (not 2)
>>> MetricRecord.objects.filter(year=2025, department="computer-science", metric_type="PAPER").first().metric_value
# Expected: 25
```

---

### TC-03: Invalid File Extension

**Objective:** Verify file type validation

**Steps:**
1. Try uploading `.txt` or `.pdf` file
2. Observe error message

**Expected Result:**
- ✅ Error message: "File format not allowed"
- ✅ File rejected before processing
- ✅ No database changes
- ✅ Redirect to upload page with error

---

### TC-04: Missing Required Columns

**Objective:** Test column validation

**File Content:**
```
year | department | metric_type
2025 | computer-science | PAPER
(missing 'value' column)
```

**Steps:**
1. Upload file without required columns
2. Observe error

**Expected Result:**
- ✅ Error message: "Missing required columns: value"
- ✅ Upload cancelled
- ✅ No database changes

---

### TC-05: Partial Failure - Invalid Row Data

**Objective:** Test partial commit (continue on individual row failures)

**File Content:**
```
year | department | metric_type | value
2025 | computer-science | PAPER | 30       # Valid
2025 | computer-science | BUDGET | invalid # Invalid (non-numeric)
2025 | electronics | PAPER | 18           # Valid
```

**Steps:**
1. Upload file with mixed valid/invalid rows
2. Check results

**Expected Result:**
- ✅ Success message: "Total 3 rows: 2 success, 1 failed"
- ✅ 2 valid rows saved
- ✅ 1 invalid row skipped (console error logged)
- ✅ Database contains 2 new/updated records

**Verification - Console Output:**
```
[Excel Upload Failures]
  Row 3: Value conversion failed: invalid
```

---

### TC-06: High Failure Rate (>= 20%)

**Objective:** Verify upload rejection when failure rate exceeds threshold

**File Content:**
```
year | department | metric_type | value
2025 | computer-science | PAPER | 35      # Valid (1 success)
2025 | computer-science | BUDGET | xxx    # Invalid
2025 | electronics | PAPER | yyy          # Invalid
2025 | electronics | BUDGET | zzz         # Invalid
(Total: 1 success, 3 failed = 75% failure)
```

**Steps:**
1. Upload file with >= 20% failure rate
2. Observe error handling

**Expected Result:**
- ✅ Error message: "Failure rate is 75.0%. Please review the file."
- ✅ Upload rejected (no data saved despite valid rows)
- ✅ Redirect to upload page

---

### TC-07: Data Normalization - Department Mapping

**Objective:** Test department name normalization

**File Content:**
```
year | department | metric_type | value
2025 | computer-science | PAPER | 40
2025 | Computer-Science | BUDGET | 75000   (different case)
2025 | COMPUTER-SCIENCE | STUDENT | 150    (different case)
```

**Steps:**
1. Upload file with various department name formats
2. Check database

**Expected Result:**
- ✅ All variants normalized to same value
- ✅ Verify in database:
  ```bash
  >>> MetricRecord.objects.filter(year=2025, department="computer-science").count()
  # Expected: 3 (all variants merged)
  ```

---

### TC-08: Data Normalization - Metric Type Mapping

**Objective:** Test metric type normalization

**File Content:**
```
year | department | metric_type | value
2025 | computer-science | paper | 45        (lowercase)
2025 | computer-science | PAPER | 46        (uppercase)
2025 | computer-science | Paper | 47        (mixed)
```

**Steps:**
1. Upload file with various metric type formats
2. Check if all mapped to "PAPER"

**Expected Result:**
- ✅ All variants normalized to "PAPER"
- ✅ UPSERT correctly updates same record (latest value: 47)
- ✅ Database shows 1 record with value=47

---

### TC-09: Large File Performance (Optional)

**Objective:** Verify performance with 1000+ rows

**Steps:**
1. Generate Excel with 1000 rows
2. Upload and time completion
3. Check success rate

**Expected Result:**
- ✅ Completes within 3 seconds (per spec)
- ✅ All rows processed successfully
- ✅ No timeout errors

---

### TC-10: Permission Check - Non-Admin User

**Objective:** Verify non-admin users cannot access upload

**Steps:**
1. Login as `user1` (non-admin)
2. Try to access `/admin/ingest/metricrecord/upload/`

**Expected Result:**
- ✅ 403 Forbidden error
- ✅ Redirect to login or permission denied page
- ✅ No upload form displayed

---

## 📊 Test Results Recording

| # | Test Case | Expected | Actual | Status | Notes |
|---|-----------|----------|--------|--------|-------|
| 1 | Valid Excel upload | 3 success, 0 failed | | ☐ Pass | |
| 2 | UPSERT update | 1 record, value=25 | | ☐ Pass | |
| 3 | Invalid extension | Error message | | ☐ Pass | |
| 4 | Missing columns | Error message | | ☐ Pass | |
| 5 | Partial failure | 2 success, 1 failed | | ☐ Pass | |
| 6 | High failure rate | Upload rejected | | ☐ Pass | |
| 7 | Department normalization | 3 records merged | | ☐ Pass | |
| 8 | Metric type normalization | 1 record, value=47 | | ☐ Pass | |
| 9 | Large file (1000 rows) | Complete in 3s | | ☐ Pass | |
| 10 | Non-admin access | 403 Forbidden | | ☐ Pass | |

---

## 🔧 Troubleshooting

### Issue: "File format not allowed" for valid Excel

**Solution:**
- Check file extension is `.xlsx` or `.xls`
- Verify file is not corrupted
- Try re-saving in Excel format

### Issue: "Missing required columns"

**Solution:**
- Ensure column names exactly match: `year`, `department`, `metric_type`, `value`
- Check for typos or extra spaces in headers

### Issue: Upload button not visible

**Solution:**
- Ensure logged in as admin user
- Check URL: `/admin/ingest/metricrecord/upload/`
- Verify `MetricRecordAdmin.get_urls()` is registered

### Issue: Data not appearing in database

**Solution:**
- Check browser console for JavaScript errors
- Verify server logs for stack traces
- Ensure `USE_SQLITE="true"` environment variable set

---

## 📝 Test Execution Checklist

- ☐ Environment setup (SQLite enabled, server running)
- ☐ Admin account created (`admin` / `admin123!`)
- ☐ Test Excel files prepared
- ☐ TC-01 through TC-10 executed
- ☐ All test results recorded
- ☐ Database verified with shell commands
- ☐ No errors in server logs
- ☐ Documentation updated with findings

---

## 🎯 Success Criteria

**All tests must pass to consider feature complete:**
- ✅ File validation works
- ✅ Data normalization functions correctly
- ✅ UPSERT prevents duplicates
- ✅ Partial commit supported (individual row failures don't block others)
- ✅ High failure rate rejection works
- ✅ Permission checks enforced
- ✅ Performance acceptable (< 3 seconds for 1000 rows)
- ✅ Error messages clear and helpful

---

## 📚 Related Documentation

- [PRD](../3.prd.md) - Product requirements
- [UserFlow #02](../4.userflow.md) - Admin Excel upload flow
- [DataFlow](../5.dataflow.md) - Database design
- [Spec 002](../spec/002-spec-excel-upload.md) - Feature specification
- [Implementation Plan](../spec/002-plan-excel-upload.md) - Implementation details

---

**Test Guide Author:** Claude Code
**Last Updated:** 2025-11-03
**Status:** Ready for Testing
