# Campaign Scene Return Bug Analysis

## Issue Description

The user reports that sometimes when trying to return from the campaign scene, all units on both sides get cleared but the scene doesn't actually return - they remain stuck in the campaign scene. The user also suspects it might be changing to another esper world instead.

## Root Cause Analysis

After examining the codebase, I've identified the likely root cause of this issue. The problem appears to be a race condition or timing issue in the interaction between:

1. **Scene Manager Cleanup Process** (`src/scenes/scene_manager.py`)
2. **Esper World Management** in WorldMapView (`src/world_map_view.py`)
3. **Campaign Scene's Return Handling** (`src/scenes/campaign.py`)

### Key Code Paths

#### 1. Return Button Handler in Campaign Scene

```python
# src/scenes/campaign.py:218
if event.ui_element == self.return_button:
    pygame.event.post(PreviousSceneEvent().to_event())
```

#### 2. Scene Manager's Previous Scene Handling

```python
# src/scenes/scene_manager.py:160-170
if event.type == PREVIOUS_SCENE_EVENT:
    validated_event = PreviousSceneEvent.model_validate(event.dict)
    for _ in range(validated_event.n):
        previous_state = self.scene_stack.pop()
    self.cleanup(add_to_stack=False)
    self.current_scene = previous_state.scene_type(
        **previous_state.params
    )
    if previous_state.camera_state:
        previous_state.camera_state.restore_position()
```

#### 3. Scene Manager's Cleanup Method

```python
# src/scenes/scene_manager.py:148-155
# Clean up UI and ECS
if self.manager:
    self.manager.clear_and_reset()
emit_event(STOP_ALL_SOUNDS, event=StopAllSoundsEvent())
```

#### 4. WorldMapView's Cleanup and Rebuild

```python
# src/world_map_view.py:269-275
def _cleanup(self) -> None:
    esper.switch_world(self.default_world)
    for battle in self.battles.values():
        if battle.id in esper.list_worlds():
            esper.delete_world(battle.id)

# src/world_map_view.py:280-300
def rebuild(self, battles: List[Battle], cleanup: bool = True) -> None:
    if cleanup:
        self._cleanup()
    
    self.battles = {
        battle.id: battle.model_copy(deep=True)
        for battle in battles
        if battle.hex_coords is not None
    }
    
    self.reset_hex_states()
    reload_game_constants()

    for battle in self.battles.values():
        self._initialize_battle_world(battle)
```

## Potential Issues Identified

### 1. Esper World State Inconsistency

The campaign scene uses `esper.switch_world()` operations throughout its update cycle, particularly in:

- `world_map_view.update_battles()` - switches to each battle's world
- `use_world()` context manager in scene_utils.py
- Direct world switches in various methods

When the scene manager's cleanup process runs, it calls `self.manager.clear_and_reset()` which might interfere with ongoing esper world operations.

### 2. WorldMapView Shared State

The `world_map_view` object is passed between scenes and contains the esper world state. If the cleanup process occurs while the WorldMapView is in the middle of updating battles or switching worlds, it could leave the esper system in an inconsistent state.

### 3. Timing of Cleanup vs. World Operations

The sequence is:
1. Return button clicked → PreviousSceneEvent posted
2. Scene manager catches event
3. Scene manager calls `cleanup(add_to_stack=False)`
4. UI manager is reset (`self.manager.clear_and_reset()`)
5. New scene is created with the preserved `world_map_view`

If step 4 happens while the campaign scene is in the middle of `update_battles()` (which switches between multiple esper worlds), it could corrupt the world state.

### 4. Missing World State Recovery

There's no explicit mechanism to ensure the esper world state is properly restored if the cleanup process interrupts world operations. The `use_world()` context manager tries to restore the original world, but if cleanup happens during this process, the restoration might fail.

## Symptoms Explained

- **Units disappear**: This happens because `esper.delete_world()` is called for battle worlds during cleanup, removing all entities
- **Scene doesn't change**: The scene transition fails because the esper world state is corrupted, but the scene manager doesn't detect this failure
- **Possible world switching**: The esper system might default to a different world if the expected world state is corrupted

## Recommended Fixes

### 1. Synchronize World Operations (Immediate Fix)

Add a flag to prevent cleanup during world operations:

```python
class WorldMapView:
    def __init__(self, ...):
        self._updating_battles = False
    
    def update_battles(self, time_delta: float) -> None:
        self._updating_battles = True
        try:
            # existing update logic
        finally:
            self._updating_battles = False
```

Then modify scene manager cleanup to wait for this flag.

### 2. Defensive World State Management

Ensure esper world state is explicitly managed during scene transitions:

```python
def cleanup(self, add_to_stack: bool = True) -> None:
    # Store current world before cleanup
    current_world = esper.current_world
    
    # ... existing cleanup logic ...
    
    # Restore world state if needed
    if current_world in esper.list_worlds():
        esper.switch_world(current_world)
```

### 3. Deferred Cleanup (Best Practice)

Instead of immediate cleanup during scene transitions, defer cleanup to a safe point:

```python
class SceneManager:
    def __init__(self):
        self._pending_cleanup = []
    
    def cleanup(self, scene, deferred=False):
        if deferred:
            self._pending_cleanup.append(scene)
        else:
            # immediate cleanup
    
    def update(self, time_delta, events):
        # Process deferred cleanup when safe
        if not self._is_world_operations_active():
            for scene in self._pending_cleanup:
                self._do_cleanup(scene)
            self._pending_cleanup.clear()
```

### 4. Explicit World State Validation

Add validation to detect corrupted world state and recover:

```python
def validate_world_state(self) -> bool:
    """Validate that esper world state is consistent."""
    try:
        current = esper.current_world
        # Check if current world exists and is valid
        return current in esper.list_worlds()
    except:
        return False

def recover_world_state(self):
    """Attempt to recover from corrupted world state."""
    esper.switch_world("__default__")
    # Rebuild world state as needed
```

## Testing Strategy

To reproduce and verify the fix:

1. **Stress Test**: Rapidly click the return button while the campaign scene is updating
2. **Timing Test**: Add logging to track esper world switches during scene transitions
3. **State Validation**: Add assertions to verify world state consistency
4. **Edge Cases**: Test with different campaign states (corruption dialogs, battle selection, etc.)

## Priority

This should be treated as a **high priority** bug because:
- It breaks core game functionality (scene navigation)
- It can leave the game in an unrecoverable state
- It affects user experience significantly
- The root cause could affect other scene transitions

The recommended approach is to start with the defensive world state management fix (#2) as it's the least intrusive and most likely to resolve the immediate issue.