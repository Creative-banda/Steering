import time
import math
import cv2
import numpy as np
from collections import deque

try:
    import mediapipe as mp
except Exception as e:
    print("Missing mediapipe. Install with: pip install mediapipe")
    raise e

try:
    import vgamepad as vg
except Exception as e:
    print("Missing vgamepad. Install with: pip install vgamepad")
    raise e

try:
    import pydirectinput
except Exception as e:
    print("Missing keyboard. Install with: pip install pydirectinput")
    raise e

# Configuration constants
STEERING_SENSITIVITY = 1.5
COOLDOWN_GEAR = 1.0  # seconds
LOSS_TIMEOUT = 1.0   # seconds
BUFFER_SIZE = 10     # frames for stabilization

class HandGestureController:
    def __init__(self):
        # Mediapipe setup
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        
        # Virtual gamepad
        self.gamepad = vg.VX360Gamepad()
        
        # State tracking
        self.gesture_buffer = deque(maxlen=BUFFER_SIZE)
        self.last_gear_command = 0
        self.last_hands_detected = time.time()
        self.smoothed_steering = 0.0
        self.current_gesture = "no_hands"
        self.current_action = "IDLE"
        
        # Camera
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("Cannot open camera")
    
    def calculate_distance(self, point1, point2):
        """Calculate Euclidean distance between two points"""
        return math.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)
    
    def is_hand_open(self, hand_landmarks):
        """Detect if hand is open using thumb-index distance and finger tip positions"""
        # Get landmarks
        thumb_tip = hand_landmarks.landmark[4]
        index_tip = hand_landmarks.landmark[8]
        middle_tip = hand_landmarks.landmark[12]
        ring_tip = hand_landmarks.landmark[16]
        pinky_tip = hand_landmarks.landmark[20]
        
        # Get MCP joints (knuckles)
        index_mcp = hand_landmarks.landmark[5]
        middle_mcp = hand_landmarks.landmark[9]
        ring_mcp = hand_landmarks.landmark[13]
        pinky_mcp = hand_landmarks.landmark[17]
        
        # Check if fingertips are extended (above their MCP joints)
        fingers_extended = 0
        
        # Index finger
        if index_tip.y < index_mcp.y:
            fingers_extended += 1
        
        # Middle finger
        if middle_tip.y < middle_mcp.y:
            fingers_extended += 1
            
        # Ring finger
        if ring_tip.y < ring_mcp.y:
            fingers_extended += 1
            
        # Pinky finger
        if pinky_tip.y < pinky_mcp.y:
            fingers_extended += 1
        
        # Thumb distance from index (open hand has larger distance)
        thumb_index_distance = self.calculate_distance(thumb_tip, index_tip)
        
        # Hand is open if at least 3 fingers extended and thumb is away from index
        return fingers_extended >= 3 and thumb_index_distance > 0.05
    
    def get_steering_angle(self, left_hand, right_hand):
        """Calculate steering angle from hand positions"""
        # Use wrist points for steering calculation
        left_wrist = left_hand.landmark[0]
        right_wrist = right_hand.landmark[0]
        
        # Calculate vertical difference (y-axis)
        # When left hand is higher than right hand (rotating left), y_diff should be negative
        # When right hand is higher than left hand (rotating right), y_diff should be positive
        y_diff = left_wrist.y - right_wrist.y  # Inverted: left - right instead of right - left
        
        # Map to steering range (-1 to 1)
        steering = y_diff * STEERING_SENSITIVITY
        return max(-1.0, min(1.0, steering))
    
    def detect_gesture(self, results):
        """Detect current gesture from hand tracking results"""
        if not results.multi_hand_landmarks:
            return "no_hands", None, None
        
        num_hands = len(results.multi_hand_landmarks)
        
        if num_hands == 1:
            return "one_hand", results.multi_hand_landmarks[0], None
        
        elif num_hands == 2:
            # Identify left and right hands
            left_hand = None
            right_hand = None
            
            for i, (hand_landmarks, handedness) in enumerate(zip(results.multi_hand_landmarks, results.multi_handedness)):
                if handedness.classification[0].label == "Left":
                    left_hand = hand_landmarks
                else:
                    right_hand = hand_landmarks
            
            if left_hand and right_hand:
                left_open = self.is_hand_open(left_hand)
                right_open = self.is_hand_open(right_hand)
                
                if left_open and right_open:
                    return "both_open", left_hand, right_hand
                elif not left_open and not right_open:
                    return "both_fists", left_hand, right_hand
                else:
                    return "mixed", left_hand, right_hand
        
        return "unknown", None, None
    
    def apply_exponential_smoothing(self, new_value, alpha=0.3):
        """Apply exponential smoothing to steering"""
        self.smoothed_steering = alpha * new_value + (1 - alpha) * self.smoothed_steering
        return self.smoothed_steering
    
    def execute_gear_command(self, command):
        """Execute gear command with cooldown"""
        current_time = time.time()
        if current_time - self.last_gear_command >= COOLDOWN_GEAR:
            if command == "up":
                pydirectinput.press('s')
                print("GEAR UP")
            elif command == "down":
                pydirectinput.press('x')
                print("GEAR DOWN")
            self.last_gear_command = current_time
    
    def release_all_controls(self):
        """Release all controls and apply full brake"""
        self.gamepad.right_trigger_float(0.0)  # No throttle
        self.gamepad.left_trigger_float(1.0)   # Full brake
        self.gamepad.left_joystick_float(0.0, 0.0)  # Center steering
        self.gamepad.update()
        print("EMERGENCY BRAKE - No hands detected")
    
    def draw_info_overlay(self, frame, stable_gesture, steering_value=0.0):
        """Draw information overlay on the frame"""
        h, w = frame.shape[:2]
        
        # Create semi-transparent overlay
        overlay = frame.copy()
        
        # Draw gesture status box
        cv2.rectangle(overlay, (10, 10), (400, 200), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Text properties
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        
        # Title
        cv2.putText(frame, "Hand Gesture Car Controller", (20, 35), 
                   font, 0.7, (255, 255, 255), thickness)
        
        # Current gesture
        gesture_color = (0, 255, 0) if stable_gesture != "no_hands" else (0, 0, 255)
        cv2.putText(frame, f"Gesture: {stable_gesture.replace('_', ' ').title()}", 
                   (20, 65), font, font_scale, gesture_color, thickness)
        
        # Current action
        cv2.putText(frame, f"Action: {self.current_action}", 
                   (20, 95), font, font_scale, (255, 255, 0), thickness)
        
        # Steering value
        if stable_gesture == "both_open":
            steering_text = f"Steering: {steering_value:.2f}"
            steering_color = (0, 255, 255)
            cv2.putText(frame, steering_text, (20, 125), 
                       font, font_scale, steering_color, thickness)
            
            # Draw steering bar
            bar_x = 20
            bar_y = 140
            bar_width = 200
            bar_height = 20
            
            # Background bar
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), 
                         (100, 100, 100), -1)
            
            # Steering indicator
            center_x = bar_x + bar_width // 2
            indicator_x = int(center_x + (steering_value * bar_width // 4))
            indicator_x = max(bar_x, min(bar_x + bar_width, indicator_x))
            
            cv2.rectangle(frame, (indicator_x - 5, bar_y), (indicator_x + 5, bar_y + bar_height), 
                         (0, 255, 255), -1)
            
            # Center line
            cv2.line(frame, (center_x, bar_y), (center_x, bar_y + bar_height), 
                    (255, 255, 255), 1)
        
        # Instructions
        instructions = [
            "Controls:",
            "Both hands open = Accelerate + Steer",
            "One hand = Brake", 
            "Both fists = Gear Up",
            "Mixed = Gear Down",
            "Press 'q' to quit"
        ]
        
        start_y = h - 150
        for i, instruction in enumerate(instructions):
            color = (255, 255, 255) if i == 0 else (200, 200, 200)
            cv2.putText(frame, instruction, (20, start_y + i * 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    def process_frame(self):
        """Process single frame and execute controls"""
        ret, frame = self.cap.read()
        if not ret:
            return False
        
        # Flip frame horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        
        # Convert to RGB for Mediapipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        # Draw hand landmarks
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw landmarks and connections
                self.mp_drawing.draw_landmarks(
                    frame, 
                    hand_landmarks, 
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style()
                )
                
                # Highlight wrist points (landmark 0)
                h, w = frame.shape[:2]
                wrist = hand_landmarks.landmark[0]
                wrist_x = int(wrist.x * w)
                wrist_y = int(wrist.y * h)
                cv2.circle(frame, (wrist_x, wrist_y), 8, (255, 0, 0), -1)
        
        # Detect gesture
        gesture, left_hand, right_hand = self.detect_gesture(results)
        self.current_gesture = gesture
        
        # Add to buffer for stabilization
        self.gesture_buffer.append(gesture)
        
        # Get most common gesture from buffer
        if len(self.gesture_buffer) >= 3:
            gesture_counts = {}
            for g in list(self.gesture_buffer)[-5:]:  # Use last 5 frames
                gesture_counts[g] = gesture_counts.get(g, 0) + 1
            stable_gesture = max(gesture_counts, key=gesture_counts.get)
        else:
            stable_gesture = gesture
        
        current_time = time.time()
        steering_value = 0.0
        
        # Execute controls based on stable gesture
        if stable_gesture == "both_open" and left_hand and right_hand:
            # Both hands open - accelerate and steer
            self.last_hands_detected = current_time
            
            # Calculate steering
            steering = self.get_steering_angle(left_hand, right_hand)
            smoothed_steering = self.apply_exponential_smoothing(steering)
            steering_value = smoothed_steering
            
            # Apply controls
            self.gamepad.right_trigger_float(1.0)  # Full throttle
            self.gamepad.left_trigger_float(0.0)   # No brake
            self.gamepad.left_joystick_float(smoothed_steering, 0.0)
            self.gamepad.update()
            
            self.current_action = f"ACCELERATE + STEER ({smoothed_steering:.2f})"
            print(f"ACCELERATE + STEER: {smoothed_steering:.2f}")
            
        elif stable_gesture == "one_hand":
            # One hand - brake
            self.last_hands_detected = current_time
            
            self.gamepad.right_trigger_float(0.0)  # No throttle
            self.gamepad.left_trigger_float(1.0)   # Full brake
            self.gamepad.left_joystick_float(0.0, 0.0)  # Center steering
            self.gamepad.update()
            
            self.current_action = "BRAKE"
            print("BRAKE")
            
        elif stable_gesture == "both_fists":
            # Both fists - gear up
            self.last_hands_detected = current_time
            self.execute_gear_command("up")
            
            # Maintain current controls but no new input
            self.gamepad.update()
            self.current_action = "GEAR UP"
            
        elif stable_gesture == "mixed":
            # One fist, one open - gear down
            self.last_hands_detected = current_time
            self.execute_gear_command("down")
            
            # Maintain current controls but no new input
            self.gamepad.update()
            self.current_action = "GEAR DOWN"
            
        elif stable_gesture == "no_hands":
            # Check timeout
            if current_time - self.last_hands_detected > LOSS_TIMEOUT:
                self.release_all_controls()
                self.current_action = "EMERGENCY BRAKE"
            else:
                # Just update gamepad to maintain last state
                self.gamepad.update()
                self.current_action = "NO HANDS DETECTED"
        
        else:
            # Unknown gesture - maintain last state
            self.gamepad.update()
            self.current_action = "UNKNOWN GESTURE"
        
        # Draw information overlay
        self.draw_info_overlay(frame, stable_gesture, steering_value)
        
        # Show the frame
        cv2.imshow("Hand Gesture Car Controller - Press 'q' to quit", frame)
        
        # Handle key presses
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:  # 'q' or ESC
            return False
        
        return True
    
    def run(self):
        """Main control loop"""
        print("Hand Gesture Car Controller for Live for Speed")
        print("Gestures:")
        print("  Both hands open -> Accelerate + Steer")
        print("  One hand -> Brake")
        print("  Both fists -> Gear Up (S)")
        print("  One fist + one open -> Gear Down (X)")
        print("  No hands (>1s) -> Emergency brake")
        print("\nPress Ctrl+C to exit")
        
        try:
            while True:
                if not self.process_frame():
                    print("Camera error, retrying...")
                    time.sleep(0.1)
                    continue
                
                # Small delay to prevent excessive CPU usage
                time.sleep(1/60)  # ~60 FPS
                
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        # Release all controls
        self.gamepad.right_trigger_float(0.0)
        self.gamepad.left_trigger_float(0.0)
        self.gamepad.left_joystick_float(0.0, 0.0)
        self.gamepad.update()
        
        # Release resources
        self.hands.close()
        self.cap.release()
        cv2.destroyAllWindows()
        print("Cleanup complete")

def main():
    """Main entry point"""
    try:
        controller = HandGestureController()
        controller.run()
    except Exception as e:
        print(f"Error: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
