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
- **Sequential Preview**: Preview calculates positions sequentially, where each unit considers previously calculated positions
- **Perfect Accuracy**: Preview shows exactly where units will be placed, including mutual collision avoidance

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
- **Sequential Preview Positions**: Preview units show exactly where they'll be placed, considering each other

## Technical Implementation

### New Functions in scene_utils.py
- `get_legal_placement_area_with_simulated_units()`: Calculates legal placement area considering additional simulated unit positions

### New State Variables
- `selected_group_partial_units`: List of transparent preview unit entity IDs
- `group_unit_offsets`: Relative positions of each unit from group center
- `group_unit_types`: Unit types for each unit in the group
- `group_placement_team`: Team assignment for the group

### Key Methods
- `pickup_group_of_units()`: Creates transparent previews and removes original units from battlefield
- `clear_group_pickup()`: Cleans up group pickup state and deletes preview units
- `place_group_units()`: Places all units from group pickup at mouse position
- `cancel_group_pickup()`: Cancels pickup and returns units to barracks inventory
- `select_units_in_rect()`: Finds units in rectangle and immediately picks them up
- `update_group_partial_units_position()`: Sequentially calculates preview positions, where each unit considers previously calculated positions

### Sequential Position Calculation
The preview system now perfectly matches the actual placement behavior:

1. **Unit 1**: Considers only existing battlefield units
2. **Unit 2**: Considers existing units + Unit 1's calculated position
3. **Unit 3**: Considers existing units + Unit 1 + Unit 2's positions
4. **And so on...**

This ensures the preview is 100% accurate to where units will actually be placed.

### Workflow
1. **Drag Selection**: User drags to create selection rectangle
2. **Automatic Pickup**: Units in rectangle are immediately picked up as transparent previews
3. **Sequential Preview**: Preview units calculate positions one by one, considering each other
4. **Placement**: Left click places all units exactly where previewed

### Inventory Management
- **Pickup**: Units are removed from battlefield but not added to barracks (they're "carried")
- **Placement**: Units are placed directly without barracks interaction
- **Cancellation**: Units are returned to barracks inventory

## Usage Examples

1. **Select and Move Multiple Units**: 
   - Click and drag to create a rectangle around units
   - Units immediately become transparent and follow your mouse
   - Preview shows exactly where units will be placed (considering mutual collisions)
   - Left click to place them in the new position
   - Right click to cancel and return them to barracks

2. **Single Unit Interaction** (unchanged):
   - Left click on a unit to pick it up
   - Left click to place, right click to cancel

3. **Barracks Interaction** (unchanged):
   - Click unit types in barracks to select for placement
   - Left click to place, right click to cancel

## Recent Bug Fixes

### Fixed: Infinite Unit Placement
- **Issue**: Could place units even when barracks showed 0 remaining
- **Cause**: Group pickup was adding units to barracks inventory but placement wasn't removing them
- **Fix**: Group units are now in a "carried" state - removed from battlefield but not added to barracks until canceled

### Fixed: Inaccurate Preview Positions
- **Issue**: Preview showed ideal positions but units were placed at different (clipped) positions
- **Cause**: Preview used ideal offsets while placement used clipped positions for collision avoidance
- **Fix**: Preview now calculates and shows the actual clipped positions where units will be placed

### Fixed: Preview Units Not Respecting Each Other
- **Issue**: Preview units calculated positions independently, not considering where other preview units would be placed
- **Cause**: Each preview unit only considered existing battlefield units, not other preview positions
- **Fix**: Preview now calculates positions sequentially, where each unit considers the positions of previously calculated preview units

## Compatibility
- **Fully Compatible**: Works alongside existing single unit pickup system
- **Team Restrictions**: Respects team limitations (can only pickup Team 1 units in normal mode)
- **Barracks Integration**: Properly updates barracks inventory when units are picked up/placed/cancelled
- **Grid Snapping**: Compatible with Shift+grid snapping for precise placement
- **Legal Placement**: All units are constrained to legal placement areas
- **Perfect Preview Accuracy**: Shows exactly where units will be placed, including all collision avoidance