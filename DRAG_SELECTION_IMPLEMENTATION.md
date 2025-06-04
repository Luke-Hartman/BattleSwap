# Drag Selection and Multi-Unit Movement Implementation

## Overview
Added drag selection and multi-unit movement functionality to the setup_battle scene, allowing players to efficiently manage multiple units at once.

## New Features

### 1. Drag Selection
- **Rectangle Selection**: Click and drag in empty areas to create a selection rectangle
- **Visual Feedback**: Green rectangle with semi-transparent fill during selection
- **Unit Filtering**: Only selects units that can be moved (Team 1 units or all units in sandbox mode)
- **Additive Selection**: Hold Ctrl while dragging to add to existing selection

### 2. Multi-Unit Movement
- **Group Movement**: Click on any selected unit to start moving the entire group
- **Relative Positioning**: Units maintain their relative positions during movement
- **Legal Placement**: All units are constrained to legal placement areas
- **Visual Feedback**: Green circles highlight selected units

### 3. Selection Management
- **Clear Selection**: Press Escape to clear all selected units
- **Auto-Clear**: Clicking on non-selected units clears the current selection
- **Visual Indicators**: Selected units are highlighted with green circles

## Controls

### Mouse Controls
- **Left Click + Drag (empty area)**: Create selection rectangle
- **Ctrl + Left Click + Drag**: Add to selection rectangle
- **Left Click (selected unit)**: Start moving all selected units
- **Left Click (non-selected unit)**: Clear selection and handle normally
- **Right Click**: Remove individual units (unchanged)
- **Escape**: Clear selection

### Visual Elements
- **Green Selection Rectangle**: Shows during drag selection
- **Green Unit Highlights**: Circles around selected units
- **Semi-transparent Fill**: Inside selection rectangle during drag

## Technical Implementation

### New Component
- **Selected**: Component to mark units as part of the current selection group

### Key Methods
- `clear_selection()`: Removes Selected component from all units
- `select_units_in_rect()`: Selects units within screen rectangle
- `start_moving_selected_units()`: Begins multi-unit movement with offset tracking
- `update_selected_units_position()`: Updates positions maintaining relative offsets
- `draw_selection_rectangle()`: Renders selection rectangle during drag
- `draw_selected_units_highlight()`: Renders highlights around selected units

### State Management
- `selected_units`: Set of entity IDs for currently selected units
- `is_drag_selecting`: Boolean flag for drag selection state
- `is_moving_selected`: Boolean flag for multi-unit movement state
- `unit_offsets`: Dictionary storing relative positions for group movement

## Usage Examples

1. **Select Multiple Units**: 
   - Click and drag to create a rectangle around units
   - Units within the rectangle will be highlighted in green

2. **Move Selected Group**:
   - Click on any highlighted unit
   - Drag to move the entire group while maintaining formation

3. **Add to Selection**:
   - Hold Ctrl and drag to add more units to existing selection

4. **Clear Selection**:
   - Press Escape or click on a non-selected unit

## Compatibility
- Works in both normal and sandbox modes
- Respects team restrictions (can only select/move Team 1 units in normal mode)
- Integrates with existing unit placement and removal functionality
- Compatible with grid snapping when Shift is held