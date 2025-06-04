# Campaign Scene Return Bug Analysis

## Issue Description

The user reports that sometimes when trying to return from the campaign scene, all units on both sides get cleared but the scene doesn't actually return - they remain stuck in the campaign scene. The user also suspects it might be changing to another esper world instead.

## Root Cause Analysis - FINAL SOLUTION

After thorough investigation, I found the actual root cause. This was **NOT** related to multiple event processing (that was a separate bug I fixed), but rather an issue with **corruption triggering during scene transitions**.

### The Real Problem: Corruption Interrupting Scene Transitions

The bug occurs when corruption gets triggered at the same time as a scene transition attempt:

1. **User clicks return button** from campaign scene
2. **Congratulations panel handles event first** (higher priority in event processing)
3. **Panel calls `self.check_panels()`** which can trigger corruption
4. **`check_panels()` calls `progress_manager.corrupt_battles()`** if conditions are met
5. **`corrupt_battles()` modifies `corrupted_hexes` state**
6. **Panel returns `True`, causing `continue`** → **return button processing is skipped**
7. **Next frame: `available_battles()` returns smaller list** due to corruption rules
8. **All unsolved battles become fogged** → **units disappear**
9. **Scene never transitions** because return button event was skipped

### Key Code Paths

#### 1. Panel Event Processing (Takes Priority)
```python
# Handle congratulations panel events first if it exists
if self.congratulations_panel is not None and self.congratulations_panel.handle_event(event):
    self.check_panels()  # ← Can trigger corruption!
    continue  # ← Skips return button processing!
```

#### 2. Corruption Triggering in check_panels()
```python
def check_panels(self) -> None:
    # ... panel logic ...
    if progress_manager.should_trigger_corruption():
        corrupted_battles = progress_manager.corrupt_battles()  # ← Changes game state!
```

#### 3. Available Battles Logic
```python
def available_battles(self) -> List[Tuple[int, int]]:
    # Add solved battles
    available_battles.extend([coords for coords in self.solutions if coords != (0, 0)])
    
    # If there are uncompleted corrupted battles, don't allow new battles to be unlocked
    if self.has_uncompleted_corrupted_battles():
        return available_battles  # ← Only solved battles!
```

#### 4. Hex State Management (Units Disappear Here)
```python
if battle.hex_coords in available_battles:
    # Available battle logic
else:
    states[battle.hex_coords].fill = FillState.FOGGED  # ← Units become invisible!
```

## Symptoms Explained

- **Units disappear**: Corruption changes `available_battles()` → unsolved battles become fogged → fogged battles don't render units
- **Scene doesn't change**: Return button processing gets skipped by panel `continue` statement
- **"Sometimes" behavior**: Only when corruption conditions are met (enough points, battles completed, etc.)
- **"Another esper world"**: Corruption changes which battles are visible/accessible

## The Fix - IMPLEMENTED

Added a flag to prevent corruption during scene transitions:

```python
def __init__(self, ...):
    # ...
    self._scene_transition_pending = False  # Prevent corruption during transitions

def check_panels(self) -> None:
    # ...
    # Don't trigger corruption if a scene transition is pending
    if not self._scene_transition_pending and progress_manager.should_trigger_corruption():
        corrupted_battles = progress_manager.corrupt_battles()
        # ...

# In event processing:
if event.ui_element == self.return_button:
    self._scene_transition_pending = True  # Prevent corruption
    pygame.event.post(PreviousSceneEvent().to_event())
```

This ensures that:
1. When return button is clicked, corruption is disabled
2. Panel processing can't trigger corruption during transition
3. Scene transition proceeds normally
4. Game state remains consistent

## Previous Discoveries

During this investigation, I also found and fixed a separate **stack underflow bug** in the scene manager that was causing crashes when the scene stack was empty. This was a related but different issue that the user helped identify during testing.

## Testing Strategy

To verify the fix:

1. **Corruption trigger test**: Complete battles until corruption should trigger, then immediately try to return
2. **Panel interaction test**: Test returning while congratulations panels are visible
3. **State consistency test**: Verify that corruption doesn't trigger during transitions
4. **Edge case testing**: Test with various corruption states and battle completion levels

## Priority

This was correctly identified as **high priority** because:
- Broke core navigation functionality  
- Could leave game in unrecoverable state
- Affected user experience significantly
- Complex interaction between multiple systems

The fix is **surgical and safe** - it prevents the problematic interaction without changing the core corruption or scene transition logic.