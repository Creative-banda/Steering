# 🎮 Enhanced Hand Steering Controller Guide

## 🚀 Quick Start

1. **Run the program**: `python main.py`
2. **Position yourself**: Sit 2-3 feet from camera, good lighting, both hands visible
3. **Auto-calibrate**: Touch your hands together to set neutral steering
4. **Start gaming**: Controller appears as "Xbox 360 Controller" in games

---

## 🖐️ Enhanced Hand Gesture Controls (Natural & Smooth!)

### 🏎️ **ENHANCED STEERING** (Stabilized Control)
**Gesture**: Both hands simulate holding a steering wheel using index fingertips

**How to do it**:
- Hold both hands as if gripping a steering wheel
- System tracks your index fingertips for precise control
- Rotate both hands together left/right naturally
- Distance between hands stabilizes small movements (closer = less sensitive)
- **Rotate LEFT (counterclockwise) = Car turns LEFT**
- **Rotate RIGHT (clockwise) = Car turns RIGHT**

**Enhanced Features**:
- Jitter reduction through distance-based stabilization
- Exponential smoothing (alpha=0.3) for fluid control
- Automatic deadzone for micro-movements
- Works like a real steering wheel with natural feel

---

### ⚡ **DISTANCE-BASED THROTTLE** (Natural Acceleration)
**Gesture**: Distance between both hands controls acceleration

**How to do it**:
- Spread hands apart for more throttle
- Bring hands closer together for less throttle
- **Farther apart = More speed**
- **Closer together = Less speed**
- Natural and intuitive like opening/closing a throttle

**Visual cues**:
- Debug display shows "Throttle: X.XXX" (0.0 to 1.0)
- Hand distance shown in real-time
- Smooth analog control for realistic acceleration

---

### 🛑 **SMART BRAKE/REVERSE** (Fist & Hand Detection)
**Gesture**: Close both hands into fists OR show only one hand

**Fist Brake (Both hands closed)**:
- Close both hands into fists
- Releases throttle immediately (coasting/braking)
- Steering still works while braking
- Natural "let go of throttle" feeling

**Light Reverse (One hand visible)**:
- Hide one hand (move out of camera view)
- Triggers light reverse using left trigger
- No steering control in reverse mode
- Emergency brake functionality

**Visual cues**:
- Debug display shows "Throttle: 0.000" for fist brake
- Debug display shows "Reverse: 0.300" for one-hand reverse

---

### 🚀 **PROXIMITY BOOST** (Close Hands Together)
**Gesture**: Bring both hands close together (but not touching)

**How to do it**:
- Bring hands close together quickly
- Don't let them touch (that's calibration)
- Triggers A button once for boost/nitro
- Can combine with steering for boost-steering
- Release and repeat for multiple boosts

**Visual cues**:
- Debug display shows "Boost: TRIGGERED"
- Xbox A button pressed in games
- One-time trigger (not held down)

---

### 🎯 **AUTO-CALIBRATION** (Touch Hands Together)
**Gesture**: Touch both hands together

**How to do it**:
- Bring both hands together until they touch
- System automatically resets neutral steering position
- Instant calibration without stopping gameplay
- Perfect for mid-game adjustments

**Visual cues**:
- Console message: "[AUTO-CALIBRATION] Neutral steering reset"
- Immediate steering adjustment
- No interruption to gameplay

---

## ⌨️ Keyboard Controls

### 🎯 **Calibration Controls**
- **`c`** - **Calibrate Center Position**
  - Press `c` and hold your hand in neutral/straight position for 1.2 seconds
  - This sets your "straight ahead" steering position
  - Do this in your normal gaming posture

- **`m`** - **Set Maximum Steering Angle**
  - Press `m` and hold your hand at maximum comfortable rotation for 1.2 seconds
  - This defines your steering sensitivity range
  - Choose an angle that feels natural and not straining

### ⚙️ **System Controls**
- **`c`** - **Manual Calibration**
  - Hold both hands in neutral position for 1.2 seconds
  - Alternative to auto-calibration (touching hands)
  - Use when you want precise neutral position

- **`s`** - **Toggle Smoothing On/Off**
  - EMA smoothing with alpha=0.3 reduces jitter
  - Turn off for more responsive but potentially jittery control
  - Default: ON (recommended for racing games)

- **`d`** - **Toggle Debug Display On/Off**
  - Shows real-time steering, throttle, and distance values
  - Displays FPS and hand detection status
  - Essential for fine-tuning your setup

- **`q` or `ESC`** - **Quit Program**
  - Safely exits the application
  - Releases camera and cleans up resources

---

## 🎯 Enhanced Control Summary

| Hand State | Steering | Right Trigger | Left Trigger | Left Stick Y | Boost | Mode |
|------------|----------|---------------|--------------|--------------|-------|------|
| **2 hands (open, apart)** | ✅ Distance-stabilized | 🚗 Distance-based (0-1.0) | 0.0 | 0.0 | ❌ Off | Normal Driving |
| **2 hands (fists closed)** | ✅ Active | ⏹️ 0.0 (Coast/Brake) | 0.0 | 0.0 | ❌ Off | Coasting |
| **2 hands (close together)** | ✅ Active | 🚗 Distance-based | 0.0 | 0.0 | 🚀 TRIGGER | Boost Mode |
| **2 hands (touching)** | 🎯 Calibrating | 🚗 Distance-based | 0.0 | 0.0 | ❌ Off | Auto-Calibration |
| **1 hand only** | ❌ Neutral | ⏹️ 0.0 | 🔄 0.3 (Light Reverse) | 0.3 | ❌ Off | Reverse Mode |
| **0 hands** | ❌ Neutral | ⏹️ 0.0 | 0.0 | 0.0 | ❌ Off | Idle |

## 🎯 Advanced Usage Tips

### 🤝 **Hand Detection Modes**

**Two Hands Detected**:
- **Steering**: Angle between left and right hands
- **Speed**: Full forward throttle (default driving)
- **Boost**: Both hands raised above boost line
- **Mode**: Normal steering wheel operation

**One Hand Detected**:
- **Steering**: Disabled (no steering input)
- **Speed**: Full brake/reverse
- **Boost**: Not available
- **Mode**: Emergency brake mode

**No Hands Detected**:
- **Steering**: Neutral (0)
- **Speed**: Neutral (0)
- **Boost**: Off
- **Mode**: Idle/stopped

### 🎮 **Optimal Gaming Setup**

1. **Camera Position**: 
   - Eye level or slightly above
   - 2-3 feet distance
   - Stable mount (no shaking)

2. **Lighting**:
   - Even lighting on hands
   - Avoid backlighting
   - No harsh shadows

3. **Background**:
   - Contrasting background behind hands
   - Avoid cluttered backgrounds
   - Solid colors work best

4. **Posture**:
   - Comfortable seated position
   - Hands clearly visible
   - Natural arm position

### 🔧 **Fine-Tuning Controls**

**If steering is too sensitive**:
- Recalibrate with smaller max angle (`m` key)
- Increase `DEADZONE_DEG` in code
- Increase `SMOOTH_ALPHA` for more smoothing

**If throttle/brake is unresponsive**:
- Adjust `THROTTLE_DISTANCE_MIN/MAX` values
- Adjust `BRAKE_DISTANCE_THRESHOLD`
- Check hand detection with debug display

**If gestures are jittery**:
- Increase `GESTURE_SMOOTHING` value
- Ensure stable camera mount
- Improve lighting conditions

---

## 🎮 Game Integration

### 🏁 **Racing Games**
- **Forza Horizon**: Works perfectly with all controls
- **Need for Speed**: Full analog steering and throttle
- **F1 Series**: Precise steering control
- **Dirt Rally**: Excellent for rally racing

### ⚙️ **Controller Mapping (Matches Your Game Settings)**
- **Left Stick X-Axis**: Steering (-1.0 to +1.0)
- **Left Stick Y-Axis**: Brake/Reverse (+1.0 for brake, 0.0 for no brake)
- **Right Trigger**: Acceleration/Forward (1.0 for full throttle, 0.0 for no throttle)
- **A Button + Right Bumper (RB)**: Boost/Nitro

### 🔧 **Game Settings**
- Set controller to "Xbox 360 Controller"
- Adjust in-game deadzone if needed
- Disable steering assists for best experience
- Set steering to "Simulation" mode if available

---

## 🚨 Troubleshooting

### ❌ **Hand Not Detected**
- Ensure good lighting
- Keep hands clearly visible
- Check camera is working
- Move closer/further from camera

### ❌ **Steering Drift**
- Recalibrate center position (`c` key)
- Check hands are in neutral position during calibration
- Increase deadzone if needed

### ❌ **Steering Direction Feels Wrong**
- **Normal behavior**: Rotate hands left = car turns left, rotate hands right = car turns right
- If it feels backwards, edit `main.py` and change `INVERT_STEERING = False` to `INVERT_STEERING = True`
- This is very rare - the default should feel natural like a real steering wheel

### ❌ **Throttle/Brake Not Working**
- Check debug display for hand distance values
- Ensure hands are opening/closing properly
- Adjust distance thresholds in code if needed

### ❌ **Buttons Not Responding**
- Ensure hands are raised high enough
- Check shoulder threshold setting
- Verify ViGEm driver is installed

### ❌ **Controller Not Recognized in Game**
- Install ViGEm Bus Driver
- Restart computer after driver installation
- Check Windows Device Manager for virtual controller
- Try running as administrator

---

## 📊 Debug Information

When debug display is ON (`d` key), you'll see:
- **Steering**: Current steering value and angle
- **Throttle/Brake**: Real-time throttle and brake values
- **Boost/Horn**: Button states (ON/OFF)
- **Hands Detected**: Number of hands currently tracked

Use this information to:
- Verify gestures are being detected
- Fine-tune your movements
- Troubleshoot issues
- Optimize your setup

---

## 🏆 Pro Tips

1. **Practice without a game first** - Get comfortable with gestures
2. **Calibrate in your gaming position** - Don't calibrate standing then sit to play
3. **Use smooth movements** - Avoid jerky or rapid gestures
4. **Keep hands visible** - Don't let hands go off-screen
5. **Good lighting is crucial** - Invest in proper lighting setup
6. **Start with easier games** - Practice with arcade racers before simulation games
7. **Adjust sensitivity gradually** - Fine-tune settings over multiple sessions

Enjoy your immersive hand gesture gaming experience! 🎮✋