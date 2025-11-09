# Bug Fixes Summary

## Issues Fixed

### 1. ✅ Double File Upload Dialog

**Problem**: Clicking "Choose File" button opened file dialog twice

**Root Cause**:
- Button click triggered its own onclick handler
- Event bubbled up to parent `uploadArea` click handler
- File dialog opened twice

**Solution**:
```javascript
// Added event.stopPropagation() to button handler
chooseFileBtn.addEventListener('click', (e) => {
    e.stopPropagation(); // Prevent bubbling
    fileInput.click();
});

// Modified uploadArea handler to ignore button clicks
uploadArea.addEventListener('click', (e) => {
    if (e.target.id !== 'chooseFileBtn' && e.target.tagName !== 'BUTTON') {
        fileInput.click();
    }
});
```

**Files Modified**:
- [app/templates/index_dark.html](app/templates/index_dark.html)

---

### 2. ✅ NaN/Infinity JSON Serialization Error

**Problem**:
```
Unexpected token 'N', ..."CY_UNIT": NaN, "AGEN"... is not valid JSON
```

**Root Cause**:
- Pandas DataFrames can contain NaN (Not a Number) values
- When converting to JSON, `NaN` is not valid JSON
- JavaScript `NaN` and `Infinity` are also not valid JSON values

**Solution**:

Added `_clean_data_for_json()` method:

```python
def _clean_data_for_json(self, data: List[Dict]) -> List[Dict]:
    """Clean data to make it JSON-serializable (replace NaN with null)"""
    cleaned_data = []
    for row in data:
        cleaned_row = {}
        for key, value in row.items():
            # Check for NaN, Infinity, etc.
            if isinstance(value, float):
                if math.isnan(value) or math.isinf(value):
                    cleaned_row[key] = None  # Convert to null
                else:
                    cleaned_row[key] = value
            else:
                cleaned_row[key] = value
        cleaned_data.append(cleaned_row)
    return cleaned_data
```

**Applied in**:
1. Dashboard generation: `json.dumps(self._clean_data_for_json(data_sample))`
2. Prompt creation: Sample data cleaned before JSON serialization
3. Fallback dashboard: Sample data cleaned

**Behavior**:
- `NaN` → `null` (valid JSON)
- `Infinity` → `null` (valid JSON)
- `-Infinity` → `null` (valid JSON)
- Normal numbers → unchanged

**Files Modified**:
- [app/agents/viz_generator.py](app/agents/viz_generator.py)

---

## Testing

### Test 1: Double Upload Fixed
```
1. Open http://localhost:8000
2. Click "Choose File" button
3. ✅ File dialog opens ONCE (not twice)
```

### Test 2: NaN Handling
```python
# Test with NaN values
test_data = [
    {'name': 'A', 'value': 10.5, 'missing': float('nan')},
    {'name': 'B', 'value': float('inf'), 'missing': 20.0}
]

cleaned = gen._clean_data_for_json(test_data)
# Result: [
#   {'name': 'A', 'value': 10.5, 'missing': None},
#   {'name': 'B', 'value': None, 'missing': 20.0}
# ]

json_str = json.dumps(cleaned)  # ✅ Works!
```

---

## Summary

| Issue | Status | Impact |
|-------|--------|--------|
| Double file dialog | ✅ Fixed | Better UX, less confusing |
| NaN JSON error | ✅ Fixed | Dashboards work with real-world data |

Both issues are now resolved! Your platform can handle:
- Clean single-click file uploads
- Data with missing values (NaN)
- Data with infinite values
