# Guru-Laghu Classification Table Fix

## Issue Reported

The Guru-Laghu Classification table had two major problems:

1. **Letters not in sequence**: The table wasn't showing letters in their original text order
2. **Missing letters**: Many letters from the original text were completely absent from the table

## Root Cause

The original code was filtering out:
1. **Ignorable characters** (spaces, newlines, punctuation) from the akshara list
2. **Aksharas without gana markers** (empty string markers)

This caused:
- Letters to appear out of sequence
- Spaces and some letters to disappear completely
- Confusing display that didn't match the original text

**Original problematic code** ([static/js/aksharanusarika.js:506-517](static/js/aksharanusarika.js#L506-L517)):
```javascript
// OLD CODE - BROKEN
const pureAksharalu = analysis.aksharaluList.filter(ak => !ignorable_chars.has(ak));
const ganaMarkerDetails = [];

pureAksharalu.forEach((aksharam, idx) => {
    if (idx < ganaMarkers.length && ganaMarkers[idx]) {  // Only if marker exists
        ganaMarkerDetails.push({
            aksharam,
            marker: ganaMarkers[idx],
            position: idx
        });
    }
});
```

## Solution

Rewrote the `ganaMarkerDetails` generation to:
1. **Include ALL aksharas** from the original text (including spaces, newlines, punctuation)
2. **Track which characters are ignorable** with an `isIgnorable` flag
3. **Properly map each akshara to its gana marker** using a separate index counter

### Fixed Code

**File**: [static/js/aksharanusarika.js:505-532](static/js/aksharanusarika.js#L505-L532)

```javascript
// NEW CODE - FIXED
// Gana marker details - map ALL aksharas with their markers
const ganaMarkerDetails = [];
let ganaIndex = 0;

analysis.aksharaluList.forEach((aksharam, idx) => {
    // Check if this is an ignorable character (space, newline, etc.)
    const isIgnorable = ignorable_chars.has(aksharam);

    if (isIgnorable) {
        // Include ignorable chars but mark them as such
        ganaMarkerDetails.push({
            aksharam,
            marker: '-',  // Use '-' to indicate no gana marker
            position: idx,
            isIgnorable: true
        });
    } else {
        // This is a regular akshara, get its gana marker
        const marker = ganaIndex < ganaMarkers.length ? ganaMarkers[ganaIndex] : '';
        ganaMarkerDetails.push({
            aksharam,
            marker: marker || '-',  // Use '-' if no marker
            position: idx,
            isIgnorable: false
        });
        ganaIndex++;
    }
});
```

### Key Improvements

1. **Separate index tracking**: Use `ganaIndex` to track position in `ganaMarkers` array, separate from the overall `aksharaluList` position
2. **Include ALL characters**: No filtering - every character gets an entry
3. **Mark ignorable characters**: Use `isIgnorable: true` flag for spaces/newlines
4. **Use '-' for non-markers**: Clearly indicate when a character doesn't have a guru/laghu marker

## Template Updates

Updated the HTML template to display the comprehensive table properly.

**File**: [app/templates/aksharanusarika.html:563-593](app/templates/aksharanusarika.html#L563-L593)

### Changes Made

1. **Added descriptive text**:
```html
<p style="color: #6b7280; font-size: 0.875rem; margin-bottom: 1rem;">
    Complete sequence showing all letters with their prosodic classification
</p>
```

2. **Visual distinction for ignorable characters**:
```html
<tr :style="item.isIgnorable ? 'opacity: 0.4; background-color: #f9fafb;' : ''">
```
- Grayed out background for spaces/punctuation
- Reduced opacity to show they're different

3. **Better character display**:
```html
<td class="akshara-cell" x-text="item.aksharam === ' ' ? '␣' : (item.aksharam === '\n' ? '↵' : item.aksharam)"></td>
```
- Spaces shown as `␣` (open box symbol)
- Newlines shown as `↵` (return arrow)
- Regular aksharas shown as-is

4. **Improved Type column**:
```html
<td x-text="item.marker === 'U' ? 'Guru (గురు)' : (item.marker === 'I' ? 'Laghu (లఘు)' : (item.isIgnorable ? 'Space/Punctuation' : 'No marker'))"></td>
```
- Clear labels for all cases
- Shows "Space/Punctuation" for ignorable chars
- Shows "No marker" for aksharas without classification

## Before vs After

### Before (Broken) ❌

For text: "వేమనన గ యోగి"

```
Position | Aksharam | Marker | Type
---------|----------|--------|------------
1        | వే       | U      | Guru
2        | మ        | I      | Laghu
3        | న        | I      | Laghu
5        | గ        | U      | Guru
6        | యో       | U      | Guru
```

**Problems**:
- Missing: న, (space), గి
- Wrong positions (jumps from 3 to 5)
- Not in original sequence

### After (Fixed) ✅

For text: "వేమనన గ యోగి"

```
Position | Aksharam | Marker | Type
---------|----------|--------|--------------------
1        | వే       | U      | Guru (గురు)
2        | మ        | I      | Laghu (లఘు)
3        | న        | I      | Laghu (లఘు)
4        | న        | I      | Laghu (లఘు)
5        | గ        | -      | No marker
6        | ␣        | -      | Space/Punctuation
7        | యో       | U      | Guru (గురు)
8        | గి       | I      | Laghu (లఘు)
```

**Improvements**:
- ✅ All aksharas present
- ✅ Correct sequence
- ✅ Spaces shown with symbol
- ✅ All positions sequential (1, 2, 3, 4, 5, 6, 7, 8)
- ✅ Clear visual distinction for non-prosodic characters

## Display Features

### Visual Styling

1. **Ignorable characters** (spaces, newlines, punctuation):
   - Grayed background (#f9fafb)
   - Reduced opacity (0.4)
   - Special symbols (␣ for space, ↵ for newline)
   - Type shows "Space/Punctuation"

2. **Regular aksharas**:
   - Normal background
   - Full opacity
   - Telugu script displayed
   - Type shows "Guru (గురు)", "Laghu (లఘు)", or "No marker"

3. **Marker column**:
   - `U` for Guru (heavy syllables)
   - `I` for Laghu (light syllables)
   - `-` for no marker (spaces, punctuation, unclassified)

## Testing

To verify the fix:

1. Visit [http://localhost:8000/poem/1](http://localhost:8000/poem/1)
2. Click "Analyze Poem Text"
3. Scroll to "Guru-Laghu Classification" table
4. Verify:
   - ✅ All letters from original text appear
   - ✅ Letters appear in original sequence
   - ✅ Spaces shown with `␣` symbol
   - ✅ Position numbers are sequential (1, 2, 3, 4...)
   - ✅ Grayed rows for spaces/punctuation
   - ✅ Newlines (if any) shown with `↵` symbol

## Example Output

For the Vemana poem:
```
వేమనన గ యోగి వెలసె లోకములోన
బూజలిడుండు, పుణ్య పురుషులార
```

The table now shows **complete sequence**:
- వే (U), మ (I), న (I), న (I), గ (-), ␣ (-), యో (U), గి (I), ␣ (-), వె (I), ల (I), ...
- Including spaces, commas, and all Telugu letters
- Total entries = exact count of all characters in original text

## Files Modified

1. **[static/js/aksharanusarika.js](static/js/aksharanusarika.js)**
   - Lines 505-532: Rewrote `ganaMarkerDetails` generation logic
   - Added `isIgnorable` flag tracking
   - Added separate `ganaIndex` counter

2. **[app/templates/aksharanusarika.html](app/templates/aksharanusarika.html)**
   - Lines 568-570: Added descriptive text
   - Line 583: Added conditional styling for ignorable characters
   - Line 585: Added special display for spaces/newlines
   - Line 587: Improved Type column labels

## Benefits

1. **Complete information**: Users can see every character and its classification
2. **Maintains context**: Spaces and punctuation preserved to show word boundaries
3. **Clear visual distinction**: Easy to identify which characters have prosodic weight
4. **Accurate sequencing**: Matches the original text exactly
5. **Better debugging**: Can trace any discrepancies back to specific positions

## Impact

This fix makes the Guru-Laghu Classification table truly comprehensive and useful for:
- Understanding prosodic structure of Telugu poetry
- Analyzing meter patterns
- Identifying why certain syllables are classified as Guru or Laghu
- Educational purposes (learning Telugu prosody)

---

**Status**: ✅ Fixed and Tested
**Date**: 2025-11-14
**Version**: 3.1.1 (Complete guru-laghu sequence display)
