# Enhanced Hand Gesture Steering Controller

A real-time hand gesture recognition system that converts natural hand movements into Xbox controller inputs for racing games. Features advanced stabilization, distance-based throttle control, and smooth gameplay experience optimized for VDrift and BeamNG.drive!

## Features

### Enhanced Gesture Controls
- **Steering**: Use both hands like a real steering wheel - index fingertips control direction
- **Throttle**: Distance between hands controls acceleration (farther apart = more speed)
- **Brake/Reverse**: Close both hands into fists to release throttle, one hand visible for light reverse
- **Boost**: Bring hands close together (but not touching) to trigger boost
- **Auto-Calibration**: Touch hands together to reset neutral steering position

### Advanced Technical Features
- Stabilized steering using both hands' index fingertips with distance-based jitter reduction
- Distance-mapped throttle control for natural acceleration feel
- Exponential moving average (EMA) smoothing with alpha=0.3 for jitter-free control
- Automatic calibration when hands touch
- Fist detection for precise throttle release
- 30 FPS optimized update rate to prevent CPU overload
- Deadzone system for micro-movement filtering

## Installation

### Prerequisites
1. **Windows 10/11** (required for vGamepad)
2. **Python 3.8+**
3. **ViGEm Bus Driver** (for Xbox controller emulation)

### Step 1: Install ViGEm Bus Driver
1. Download from: https://github.com/ViGEm/ViGEmBus/releases
2. Run the installer as administrator
3. Restart your computer

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install opencv-python mediapipe vgamepad numpy
```

### Step 3: Test Camera
Ensure your webcam is working and positioned to capture your hands clearly.

## Usage

### Starting the Controller
```bash
python main.py
```

### Keyboard Controls
- `c` - Calibrate neutral steering position (hold both hands straight for 1.2s)
- `s` - Toggle smoothing on/off (EMA with alpha=0.3)
- `d` - Toggle debug display on/off
- `q` or `ESC` - Quit application

### Enhanced Gesture Setup
1. **Position yourself**: Sit 2-3 feet from camera with good lighting, both hands visible
2. **Auto-calibrate**: Touch your hands together to set neutral steering position
3. **Manual calibrate**: Press `c` and hold both hands in neutral steering position
4. **Start gaming**: The controller will appear as "Xbox 360 Controller" in games

### Enhanced Gesture Tips
- **Steering**: Hold both hands like a steering wheel, rotate together naturally
- **Throttle**: Spread hands apart for acceleration (distance = speed)
- **Brake**: Close both hands into fists to coast/brake
- **Reverse**: Show only one hand for light reverse
- **Boost**: Bring hands close together (not touching) for boost activation
- **Calibration**: Touch hands together anytime to reset neutral position

## Configuration

### Adjustable Parameters (in main.py)
```python
# Enhanced steering parameters
STEERING_DEADZONE = 0.05    # deadzone for micro-movements (0-1)
SMOOTH_ALPHA = 0.3          # EMA smoothing factor (0-1)
MAX_STEERING_RANGE = 1.0    # maximum steering output (-1 to +1)

# Distance-based throttle control
MIN_HAND_DISTANCE = 0.1     # minimum distance between hands
MAX_HAND_DISTANCE = 0.6     # distance for full throttle
BOOST_DISTANCE_THRESHOLD = 0.15  # hands close together for boost

# Auto-calibration
CALIBRATION_TOUCH_THRESHOLD = 0.05  # very close hands for calibration

# Performance
FPS_TARGET = 30.0           # optimized 30 FPS for smooth performance
```

## Troubleshooting

### Controller Not Detected
- Ensure ViGEm Bus Driver is installed and system is restarted
- Check Windows Device Manager for "Virtual HID Framework" devices
- Try running as administrator

### Poor Hand Detection
- Improve lighting conditions
- Ensure hands are clearly visible against background
- Adjust camera angle and distance
- Clean camera lens

### Jittery Controls
- Increase smoothing values (SMOOTH_ALPHA, GESTURE_SMOOTHING)
- Ensure stable hand positions
- Reduce camera shake/vibration

### Calibration Issues
- Hold steady poses during calibration
- Recalibrate in your actual gaming position
- Adjust deadzone if needed

## Game Compatibility

This controller emulates a standard Xbox 360 controller and works with:
- Most PC racing games (Forza, Need for Speed, etc.)
- Steam games with controller support
- Any game that accepts XInput controllers

### Recommended Games
- Forza Horizon series
- Need for Speed series  
- Dirt Rally series
- F1 series
- Burnout Paradise

## Performance Notes

- Runs at 60 FPS for smooth control
- Uses ~10-15% CPU on modern systems
- Requires decent webcam (720p+ recommended)
- Works best with consistent lighting

## License

MIT License - Feel free to modify and distribute!