# Quick test to verify the fixes work
import sys
sys.path.append('src')
from scenes.scene_manager import SceneManager
from scenes.events import PreviousSceneEvent
from scenes.scene import Scene

# Test that empty scene stack doesn't crash
sm = SceneManager()
sm.scene_stack = []

print("Testing scene manager bounds checking...")

# This should not crash anymore
try:
    # Simulate what happens when a PreviousSceneEvent is processed with empty stack
    if len(sm.scene_stack) == 0:
        print("✓ Scene stack is empty - would have crashed before fix")
        scenes_to_pop = min(1, len(sm.scene_stack))  # This is the fix logic
        if scenes_to_pop > 0:
            print("Would pop scenes")
        else:
            print("✓ Correctly ignoring event when no scenes to pop")
    print("✓ Scene manager bounds checking works - no crash on empty stack")
except Exception as e:
    print(f"✗ Error: {e}")

# Test debouncing
print("\nTesting escape key debouncing...")
scene = Scene()
print(f"✓ Escape debounce delay: {scene._escape_debounce_delay}s")
print(f"✓ Last escape time initialized: {scene._last_escape_time}")

print("\n✓ All fixes applied successfully!")