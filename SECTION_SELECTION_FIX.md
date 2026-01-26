# Section Selection Fix

## Issues Fixed

### 1. **Limited Section Options**
**Problem**: Only 8 sections were available in the dropdown
**Solution**: Expanded `IEEE_SECTIONS` to include all 14 standard sections:
- Abstract
- Introduction
- Related Work
- Literature Review
- Methodology
- System Design
- Implementation
- Experimental Setup
- Results
- Evaluation
- Discussion
- Conclusion
- Future Work
- References

### 2. **Selected Sections Not Persisting**
**Problem**: When refreshing the page, selected sections would reset to default 3 sections
**Solution**: 
- Save selected sections to `localStorage` when moving to next step
- Load selected sections from `localStorage` on page load
- Fall back to generated sections if no saved selections
- Default to `['Abstract', 'Introduction', 'Methodology']` for new papers

### 3. **Sections After Methodology Not Showing**
**Problem**: Sections selected after Methodology weren't being displayed after refresh
**Solution**:
- Fixed the section loading logic to properly restore all selected sections
- Added localStorage persistence with paper-specific keys
- Load generated section names as selected sections if available

## Changes Made

### `frontend/src/config/constants.js`
```javascript
// Added 6 more sections to IEEE_SECTIONS
export const IEEE_SECTIONS = [
  'Abstract',
  'Introduction',
  'Related Work',          // NEW
  'Literature Review',
  'Methodology',
  'System Design',         // NEW
  'Implementation',        // NEW
  'Experimental Setup',    // NEW
  'Results',
  'Evaluation',            // NEW
  'Discussion',
  'Conclusion',
  'Future Work',           // NEW
  'References',
];
```

### `frontend/src/components/PaperWizard.jsx`

#### 1. Changed Initial State
```javascript
// Before
const [selectedSections, setSelectedSections] = useState(['Abstract', 'Introduction', 'Literature Review'])

// After
const [selectedSections, setSelectedSections] = useState([])
```

#### 2. Enhanced Loading Logic
```javascript
// Load selected sections from localStorage or use generated sections
const savedSelections = localStorage.getItem(`selectedSections_${existingPaper.paper_id}`)
if (savedSelections) {
  setSelectedSections(JSON.parse(savedSelections))
} else if (sectionNames.length > 0) {
  // If we have generated sections, use those as selected
  setSelectedSections(sectionNames)
} else {
  // Default to common sections
  setSelectedSections(['Abstract', 'Introduction', 'Methodology'])
}
```

#### 3. Added Persistence on Next Step
```javascript
// Save selected sections to localStorage when moving to step 4
if (paperId) {
  localStorage.setItem(`selectedSections_${paperId}`, JSON.stringify(selectedSections))
}
```

## How It Works Now

### New Paper Flow
1. User creates paper → `selectedSections` = `[]`
2. User uploads files → `selectedSections` = `['Abstract', 'Introduction', 'Methodology']` (default)
3. User selects sections → selections are stored in state
4. User clicks Next → selections saved to `localStorage`
5. User refreshes → selections loaded from `localStorage`

### Existing Paper Flow
1. User opens existing paper → Load from backend
2. Check `localStorage` for saved selections → Use if found
3. If no saved selections → Use generated section names
4. If no generated sections → Use default 3 sections
5. User can modify selections → Saved to `localStorage` on Next

## Testing

### Test Case 1: New Paper
1. Create new paper
2. Select sections including "Results", "Discussion", "Conclusion"
3. Click Next
4. Refresh page
5. ✅ All selected sections should still be selected

### Test Case 2: Existing Paper with Generated Sections
1. Open paper with generated sections
2. Should show all generated sections as selected
3. Can add/remove sections
4. Changes persist after refresh

### Test Case 3: Section Availability
1. Go to "Select Sections" step
2. ✅ Should see all 14 sections available
3. Can select any combination
4. No limit on number of selections

## Benefits

1. ✅ **More Section Options**: 14 sections instead of 8
2. ✅ **Persistent Selections**: Survives page refresh
3. ✅ **Better UX**: Remembers user choices
4. ✅ **Flexible**: Can select any sections, not just first 3
5. ✅ **Smart Defaults**: Uses generated sections when available

## Notes

- localStorage key format: `selectedSections_{paperId}`
- Selections are paper-specific (won't mix between papers)
- If localStorage is cleared, falls back to generated sections or defaults
- Works for both new and existing papers
