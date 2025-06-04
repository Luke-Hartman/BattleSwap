# Drag Selection and Multi-Unit Movement Implementation

## Overview
Added drag selection and multi-unit pickup functionality to the setup_battle scene, working exactly like the existing single unit pickup system but for groups of units.

## New Features

### 1. Drag Selection
- **Rectangle Selection**: Click and drag in empty areas to create a selection rectangle
- **Visual Feedback**: Green rectangle with semi-transparent fill during selection
- **Unit Filtering**: Only selects units that can be moved (Team 1 units or all units in sandbox mode)
- **Automatic Pickup**: Selected units are immediately "picked up" as transparent previews

### 2. Group Unit Pickup (Like Single Unit Pickup)
- **Transparent Previews**: Selected units become transparent and follow the mouse cursor
- **Relative Positioning**: Units maintain their relative positions from the group center
- **Centered on Mouse**: The group is centered on the mouse cursor for easy positioning
- **Formation Preservation**: Units maintain their relative formation during movement

### 3. Group Placement & Cancellation
- **Left Click to Place**: Places all units in the group at their relative positions
- **Right Click to Cancel**: Cancels the pickup and returns units to barracks inventory
- **Legal Placement**: All units are constrained to legal placement areas when placed
- **Escape to Cancel**: Press Escape to cancel group pickup

## Controls

### Mouse Controls
- **Left Click + Drag (empty area)**: Create selection rectangle and pick up selected units
- **Left Click (while holding group)**: Place all units in the group
- **Left Click (on unit)**: Pick up single unit (unchanged behavior)
- **Left Click (from barracks)**: Select unit type for placement (unchanged)
- **Right Click (while holding group)**: Cancel group pickup and return units to barracks
- **Right Click (while holding single unit)**: Cancel single unit pickup (unchanged)
- **Right Click (on placed unit)**: Remove individual unit (unchanged)

### Keyboard Controls
- **Escape**: Cancel any active pickup (group or single unit)

### Visual Elements
- **Green Selection Rectangle**: Shows during drag selection (only for rectangles > 5px)
- **Transparent Unit Previews**: Selected units become semi-transparent and follow mouse
- **Legal Placement Area**: Gray outlined area shows where units can be placed

## Technical Implementation

### New State Variables
- `selected_group_partial_units`: List of transparent preview unit entity IDs
- `group_unit_offsets`: Relative positions of each unit from group center
- `group_unit_types`: Unit types for each unit in the group
- `group_placement_team`: Team assignment for the group

### Key Methods
- `pickup_group_of_units()`: Creates transparent previews and removes original units
- `clear_group_pickup()`: Cleans up group pickup state and deletes preview units
- `place_group_units()`: Places all units from group pickup at mouse position
- `cancel_group_pickup()`: Cancels pickup and returns units to barracks inventory
- `select_units_in_rect()`: Finds units in rectangle and immediately picks them up
- `update_group_partial_units_position()`: Updates preview positions to follow mouse

### Workflow
1. **Drag Selection**: User drags to create selection rectangle
2. **Automatic Pickup**: Units in rectangle are immediately picked up as transparent previews
3. **Movement**: Preview units follow mouse cursor maintaining relative positions
4. **Placement**: Left click places all units, right click cancels and returns to barracks

## Usage Examples

1. **Select and Move Multiple Units**: 
   - Click and drag to create a rectangle around units
   - Units immediately become transparent and follow your mouse
   - Left click to place them in the new position
   - Right click to cancel and return them to barracks

2. **Single Unit Interaction** (unchanged):
   - Left click on a unit to pick it up
   - Left click to place, right click to cancel

3. **Barracks Interaction** (unchanged):
   - Click unit types in barracks to select for placement
   - Left click to place, right click to cancel

## Key Improvements from Previous Version

1. **Fixed Normal Unit Placement**: Single unit pickup and placement works exactly as before
2. **Consistent Interaction Model**: Group pickup works exactly like single unit pickup
3. **Immediate Feedback**: Units are picked up immediately when selected, not just highlighted
4. **Proper Cancellation**: Right click properly returns units to barracks instead of deleting them
5. **Simplified Controls**: No complex multi-state interaction, just pickup → place/cancel

## Compatibility
- **Fully Compatible**: Works alongside existing single unit pickup system
- **Team Restrictions**: Respects team limitations (can only pickup Team 1 units in normal mode)
- **Barracks Integration**: Properly updates barracks inventory when units are picked up/placed/cancelled
- **Grid Snapping**: Compatible with Shift+grid snapping for precise placement
- **Legal Placement**: All units are constrained to legal placement areas