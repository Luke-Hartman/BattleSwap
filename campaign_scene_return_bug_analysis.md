# Campaign Scene Return Bug Analysis

## Issue Description

The user reports that sometimes when trying to return from the campaign scene, all units on both sides get cleared but the scene doesn't actually return - they remain stuck in the campaign scene. The user also suspects it might be changing to another esper world instead.

## Root Cause Analysis - CORRECTED

After thorough investigation, I found the actual root cause. This is **NOT** a race condition (as the game is single-threaded), but rather an issue with **multiple event processing**.

### The Real Problem: Multiple PreviousSceneEvent Processing

The bug occurs when multiple `PreviousSceneEvent` objects are processed in sequence, typically caused by:
- Rapid clicking of the return button
- UI responsiveness issues causing delayed event posting  
- Any condition that generates multiple button press events

### Sequence of Events

1. **User clicks return button** (possibly multiple times)
2. **Multiple `PreviousSceneEvent` objects get posted** to the event queue
3. **First event processes successfully:**
   - Pops `MainMenu` from `scene_stack` 
   - Calls `cleanup()` which deletes esper worlds → **units disappear**
   - Creates new `MainMenu` scene successfully
4. **Second event processes in the same frame:**
   - Tries to `scene_stack.pop()` from now-empty stack → **`IndexError`**
   - Exception terminates scene transition
   - BUT cleanup already happened from first event
   - Current scene remains `CampaignScene` but with no units

### Key Code Location

The vulnerability is in `src/scenes/scene_manager.py`:

```python
if event.type == PREVIOUS_SCENE_EVENT:
    validated_event = PreviousSceneEvent.model_validate(event.dict)
    for _ in range(validated_event.n):
        previous_state = self.scene_stack.pop()  # ← No protection against empty stack!
    self.cleanup(add_to_stack=False)  # ← This deletes units
    self.current_scene = previous_state.scene_type(**previous_state.params)
```

There's **no check** to ensure the scene stack has enough items before popping.

## Symptoms Explained

- **Units disappear**: `cleanup()` deletes esper worlds during first event processing
- **Scene doesn't change**: Second event fails with `IndexError`, leaving user in campaign scene
- **"Sometimes" behavior**: Only occurs when multiple events are queued
- **"Another esper world"**: Campaign scene now has no battle worlds, so switches to default world

## The Fix - IMPLEMENTED

Added protection against empty scene stack:

```python
if event.type == PREVIOUS_SCENE_EVENT:
    validated_event = PreviousSceneEvent.model_validate(event.dict)
    
    # Protect against empty scene stack
    if len(self.scene_stack) < validated_event.n:
        # Not enough scenes on stack to pop, ignore this event
        continue
        
    for _ in range(validated_event.n):
        previous_state = self.scene_stack.pop()
    # ... rest of processing
```

This ensures that if there aren't enough scenes on the stack to satisfy the event, the event is ignored rather than causing an `IndexError`.

## Why This Wasn't a Race Condition

The original analysis incorrectly assumed race conditions because:
- Multiple operations appeared to be happening "simultaneously"
- State corruption seemed to occur during transitions

However, in single-threaded Python with immediate event processing:
- All events are processed sequentially in the same thread
- The issue was actually multiple **sequential** events causing state corruption
- No concurrent access was involved

## Testing Strategy

To verify the fix:

1. **Rapid clicking test**: Rapidly click the return button multiple times
2. **UI lag simulation**: Test on slower systems where UI events might queue up
3. **Stress testing**: Test scene transitions under various load conditions
4. **Event logging**: Add logging to verify only one transition occurs per user action

## Priority

This was correctly identified as **high priority** because:
- Breaks core navigation functionality  
- Can leave game in unrecoverable state
- Affects user experience significantly
- Simple fix with major impact

The fix is **minimal and safe** - it simply ignores redundant events rather than allowing them to corrupt state.