# Game ECS Architecture

## 1. Components

Components are the data containers that represent different attributes or properties of entities in your game. Here's an updated list based on our discussion:

- **HealthComponent**
  - Attributes: `current_health`, `max_health`
  - Purpose: Tracks the unit’s health and determines when it transitions to the `DEAD` state.

- **PositionComponent**
  - Attributes: `x`, `y`
  - Purpose: Represents the position of the unit or projectile in the game world.

- **TargetComponent**
  - Attributes: `target_entity` (reference to the target entity or null)
  - Purpose: Tracks the current target for the unit when in combat or pursuit.

- **StateComponent**
  - Attributes: `current_state` (e.g., `IDLE`, `PURSUING`, `ATTACKING`, `DEAD`)
  - Purpose: Represents the current behavior/state of the unit, determining what actions it should perform.

- **AnimationComponent**
  - Attributes: `current_animation`, `animation_frame`, `animation_speed`
  - Purpose: Tracks and controls the animation that should be playing based on the unit’s state and the attack speed.

- **AttackComponent**
  - Attributes: `attack_range`, `attack_damage`, `attack_speed`, `attack_type` (e.g., `melee`, `ranged`), `projectile_type` (for ranged attacks)
  - Purpose: Defines the unit’s combat capabilities, including attack range, damage, speed, and type of attack.

- **MovementComponent**
  - Attributes: `movement_speed`
  - Purpose: Governs how fast the unit moves when pursuing a target.

- **ProjectileComponent**
  - Attributes: `direction`, `speed`, `damage`, `target_entity`
  - Purpose: For ranged attacks, controls the movement and impact of projectiles.

- **CollisionComponent**
  - Purpose: Allows the unit or projectile to participate in collision detection.

- **TargetableComponent**
  - Purpose: Indicates whether a unit can be targeted by other entities. This will be removed or disabled when the unit is dead.

---

## 2. Events

Events are used to signal important interactions or state transitions in the game. They decouple systems, allowing them to react to changes independently.

- **TargetAcquiredEvent**
  - Triggered when a unit identifies an enemy target.
  - Causes: The unit transitions from `IDLE` to `PURSUING`.

- **TargetInRangeEvent**
  - Triggered when a unit gets within attack range of its target.
  - Causes: The unit transitions from `PURSUING` to `ATTACKING`.

- **AttackEvent**
  - Triggered during the attack animation to apply damage (for melee attacks) or create a projectile (for ranged attacks).

- **DamageEvent**
  - Triggered when a unit takes damage. If the unit’s health reaches 0, it transitions to `DEAD`.

- **DeathEvent**
  - Triggered when a unit dies. The unit transitions to the `DEAD` state and becomes untargetable and non-collidable.

- **AttackCompletedEvent**
  - Triggered when the attack animation finishes. The unit transitions to `IDLE` unless conditions dictate otherwise.

- **ProjectileCollisionEvent**
  - Triggered when a projectile collides with an enemy or obstacle, causing damage and potentially destroying the projectile.

- **AnimationCompletedEvent**
  - Triggered when an animation sequence completes. For instance, the death animation stops and holds the last frame.

---

## 3. Processors (Systems)

Processors handle the actual logic that drives your game by responding to events and modifying components. Below is a description of each processor's role.

### StateProcessor
- **Purpose:** Handles state transitions based on events and conditions.
- **How it works:** 
  - Listens for events like `TargetAcquiredEvent`, `TargetInRangeEvent`, and `DamageEvent`.
  - Transitions units between states (`IDLE -> PURSUING -> ATTACKING -> DEAD`) based on conditions (e.g., health, proximity to targets).
  - If a unit is attacking, this processor sends out the appropriate event to trigger damage or projectiles at the right moment (via `AttackEvent`).
  - Always transitions back to `IDLE` after an attack completes (`AttackCompletedEvent`).

### MovementProcessor
- **Purpose:** Moves entities (like units and projectiles) in the game world.
- **How it works:** 
  - Listens for the unit’s state transitions to `PURSUING`, causing it to move toward its target.
  - Continuously updates the `PositionComponent` as the unit moves.
  - Checks if the unit has reached its target. When it does, it fires a `TargetInRangeEvent` to start the attack.

### AttackProcessor
- **Purpose:** Manages the application of damage and the creation of projectiles during attacks.
- **How it works:** 
  - Listens for `AttackEvent`. If the attack is melee, it applies damage immediately to the target. If it’s ranged, it creates a new entity with a `ProjectileComponent` that starts moving toward the target.
  - For projectiles, this processor handles damage when a `ProjectileCollisionEvent` is triggered.

### ProjectileProcessor
- **Purpose:** Moves projectiles and handles their collisions.
- **How it works:** 
  - Moves the projectile based on its `speed` and `direction`.
  - Detects collisions with units or obstacles. When a collision occurs, it fires a `ProjectileCollisionEvent` to apply damage and destroy the projectile.

### HealthProcessor
- **Purpose:** Handles health reduction and death.
- **How it works:** 
  - Listens for `DamageEvent` to reduce the `HealthComponent`.
  - If the unit’s health reaches 0, it fires a `DeathEvent` to transition the unit to `DEAD`.

### AnimationProcessor
- **Purpose:** Manages animations for units and handles the completion of animations.
- **How it works:** 
  - Plays the appropriate animation based on the unit’s `StateComponent` (e.g., idle, attacking, dying).
  - Adjusts animation speed based on the unit’s `attack_speed`.
  - Listens for `AnimationCompletedEvent` to stop or loop animations (e.g., hold the final frame for a death animation).

### CollisionProcessor
- **Purpose:** Handles collision detection between units, projectiles, and the environment.
- **How it works:**
  - Continuously checks for intersections between entities with `CollisionComponent`.
  - Triggers `ProjectileCollisionEvent` for projectiles and ensures dead units do not participate in collision detection by removing or disabling their `CollisionComponent` after they die.

### RenderingProcessor
- **Purpose:** Draws units, projectiles, and animations to the screen.
- **How it works:**
  - Uses the `PositionComponent` to know where to draw the entity.
  - Uses the `AnimationComponent` to know which animation frame to render for each entity based on its state.

---

## 4. State Transitions and Event Flow

To illustrate how everything fits together, here’s an example of a full sequence for a unit attacking an enemy:

1. **IDLE → PURSUING:**
   - The unit is in the `IDLE` state.
   - The **StateProcessor** receives a `TargetAcquiredEvent` (perhaps from an AI system), transitioning the unit to the `PURSUING` state.
   - The **MovementProcessor** starts moving the unit toward its target, updating its position.

2. **PURSUING → ATTACKING:**
   - When the unit is in range of the target, the **MovementProcessor** fires a `TargetInRangeEvent`.
   - The **StateProcessor** transitions the unit to `ATTACKING`.
   - The **AnimationProcessor** starts playing the attack animation.

3. **ATTACKING (Attack Event):**
   - During the attack animation, at a key frame, the **AnimationProcessor** triggers an `AttackEvent`.
   - The **AttackProcessor** checks whether the unit is melee or ranged:
     - If melee, it applies damage directly to the target.
     - If ranged, it creates a projectile entity with a `ProjectileComponent`.

4. **Projectile Movement and Collision:**
   - The **ProjectileProcessor** moves the projectile.
   - If it collides with an enemy, the **CollisionProcessor** triggers a `ProjectileCollisionEvent`.
   - The **AttackProcessor** handles applying damage to the enemy and destroying the projectile.

5. **Attack Completed → IDLE:**
   - Once the attack animation finishes, the **AnimationProcessor** triggers an `AttackCompletedEvent`.
   - The **StateProcessor** transitions the unit back to `IDLE`.

6. **DEAD State (Death Event):**
   - If at any point the unit’s health reaches 0 (due to a `DamageEvent`), the **HealthProcessor** triggers a `DeathEvent`.
   - The **StateProcessor** transitions the unit to `DEAD`, and the **AnimationProcessor** plays the death animation.
   - The **CollisionProcessor** removes the unit’s `CollisionComponent`, and the **TargetableComponent** is disabled to ensure the dead unit isn’t targetable.
