"""
Color Calibration Tool

A simple tkinter-based UI for calibrating color detection thresholds.
Run this script directly to launch the calibration interface.

Usage:
    python -m app.services.color_calibration_ui [image_path]
"""

import json
import sys
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    from PIL import Image, ImageTk
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False
    print("Warning: tkinter not available. Calibration UI cannot run.")

from app.config import settings

CALIBRATION_FILE = settings.MODEL_PATH / "color_calibration.json"


class ColorCalibrationUI:
    """
    GUI for calibrating HSV color thresholds for koi fish color analysis.
    """
    
    def __init__(self, image_path: Optional[str] = None):
        """
        Initialize the calibration UI.
        
        Args:
            image_path: Optional path to initial image.
        """
        if not HAS_TKINTER:
            raise ImportError("tkinter is required for calibration UI")
        
        self.root = tk.Tk()
        self.root.title("Koi Color Calibration Tool")
        self.root.geometry("1400x900")
        
        # Current image
        self.image: Optional[np.ndarray] = None
        self.display_image: Optional[np.ndarray] = None
        self.current_color = "white"
        
        # Threshold values (will be loaded/initialized)
        self.thresholds = self._load_or_create_thresholds()
        
        # Create UI components
        self._create_ui()
        
        # Load initial image if provided
        if image_path:
            self._load_image(image_path)
    
    def _load_or_create_thresholds(self) -> dict:
        """Load existing thresholds or create defaults."""
        if CALIBRATION_FILE.exists():
            try:
                with open(CALIBRATION_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Default thresholds
        return {
            "white": {
                "lower": [0, 0, 180],
                "upper": [179, 50, 255],
                "description": "White (shiroji) areas"
            },
            "red": {
                "lower1": [0, 100, 100],
                "upper1": [10, 255, 255],
                "lower2": [160, 100, 100],
                "upper2": [179, 255, 255],
                "description": "Red/Orange (hi) areas"
            },
            "black": {
                "lower": [0, 0, 0],
                "upper": [179, 255, 50],
                "description": "Black (sumi) areas"
            },
        }
    
    def _create_ui(self):
        """Create all UI components."""
        # Main frames
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        image_frame = ttk.Frame(self.root, padding=10)
        image_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # --- Control Panel ---
        
        # Load image button
        ttk.Button(
            control_frame, text="Load Image", command=self._browse_image
        ).pack(fill=tk.X, pady=5)
        
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Color selection
        ttk.Label(control_frame, text="Select Color:", font=('Arial', 10, 'bold')).pack()
        
        self.color_var = tk.StringVar(value="white")
        for color in ["white", "red", "black"]:
            ttk.Radiobutton(
                control_frame, text=color.capitalize(), value=color,
                variable=self.color_var, command=self._on_color_change
            ).pack(anchor=tk.W)
        
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # HSV Sliders
        ttk.Label(control_frame, text="HSV Thresholds:", font=('Arial', 10, 'bold')).pack()
        
        # Slider frame
        slider_frame = ttk.Frame(control_frame)
        slider_frame.pack(fill=tk.X, pady=5)
        
        # Create slider variables and widgets
        self.slider_vars = {}
        self.sliders = {}
        
        slider_config = [
            ("H Lower", "h_lower", 0, 179),
            ("H Upper", "h_upper", 0, 179),
            ("S Lower", "s_lower", 0, 255),
            ("S Upper", "s_upper", 0, 255),
            ("V Lower", "v_lower", 0, 255),
            ("V Upper", "v_upper", 0, 255),
        ]
        
        for label, key, min_val, max_val in slider_config:
            frame = ttk.Frame(slider_frame)
            frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(frame, text=label, width=10).pack(side=tk.LEFT)
            
            var = tk.IntVar(value=0)
            self.slider_vars[key] = var
            
            slider = ttk.Scale(
                frame, from_=min_val, to=max_val, variable=var,
                orient=tk.HORIZONTAL, command=lambda _: self._update_preview()
            )
            slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.sliders[key] = slider
            
            value_label = ttk.Label(frame, textvariable=var, width=4)
            value_label.pack(side=tk.RIGHT)
        
        # Red color has two ranges (wrap-around)
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        ttk.Label(
            control_frame, text="Red Range 2 (wrap-around):",
            font=('Arial', 9, 'italic')
        ).pack()
        
        self.red_range2_frame = ttk.Frame(control_frame)
        self.red_range2_frame.pack(fill=tk.X, pady=5)
        
        self.red2_vars = {}
        red2_config = [
            ("H2 Lower", "h2_lower", 0, 179),
            ("H2 Upper", "h2_upper", 0, 179),
        ]
        
        for label, key, min_val, max_val in red2_config:
            frame = ttk.Frame(self.red_range2_frame)
            frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(frame, text=label, width=10).pack(side=tk.LEFT)
            
            var = tk.IntVar(value=0)
            self.red2_vars[key] = var
            
            slider = ttk.Scale(
                frame, from_=min_val, to=max_val, variable=var,
                orient=tk.HORIZONTAL, command=lambda _: self._update_preview()
            )
            slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            value_label = ttk.Label(frame, textvariable=var, width=4)
            value_label.pack(side=tk.RIGHT)
        
        # Initially hide red range 2
        self.red_range2_frame.pack_forget()
        
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Preview options
        self.show_mask_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            control_frame, text="Show Color Mask", variable=self.show_mask_var,
            command=self._update_preview
        ).pack(anchor=tk.W)
        
        self.overlay_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            control_frame, text="Overlay on Original", variable=self.overlay_var,
            command=self._update_preview
        ).pack(anchor=tk.W)
        
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Save/Reset buttons
        ttk.Button(
            control_frame, text="Save Calibration", command=self._save_calibration
        ).pack(fill=tk.X, pady=5)
        
        ttk.Button(
            control_frame, text="Reset to Defaults", command=self._reset_defaults
        ).pack(fill=tk.X, pady=5)
        
        # --- Image Display ---
        
        # Original image
        ttk.Label(image_frame, text="Original Image").pack()
        self.original_canvas = tk.Canvas(image_frame, width=600, height=400, bg='gray')
        self.original_canvas.pack(pady=5)
        
        # Preview image
        ttk.Label(image_frame, text="Color Mask Preview").pack()
        self.preview_canvas = tk.Canvas(image_frame, width=600, height=400, bg='gray')
        self.preview_canvas.pack(pady=5)
        
        # Initialize sliders with current color
        self._on_color_change()
    
    def _browse_image(self):
        """Open file dialog to select image."""
        file_path = filedialog.askopenfilename(
            title="Select Koi Fish Image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self._load_image(file_path)
    
    def _load_image(self, path: str):
        """Load and display an image."""
        self.image = cv2.imread(path)
        if self.image is None:
            messagebox.showerror("Error", f"Could not load image: {path}")
            return
        
        # Resize for display if too large
        max_dim = 600
        h, w = self.image.shape[:2]
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            new_size = (int(w * scale), int(h * scale))
            self.display_image = cv2.resize(self.image, new_size)
        else:
            self.display_image = self.image.copy()
        
        self._show_original()
        self._update_preview()
    
    def _show_original(self):
        """Display original image on canvas."""
        if self.display_image is None:
            return
        
        # Convert BGR to RGB for tkinter
        rgb = cv2.cvtColor(self.display_image, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        self.original_photo = ImageTk.PhotoImage(img)
        
        self.original_canvas.delete("all")
        self.original_canvas.config(width=img.width, height=img.height)
        self.original_canvas.create_image(0, 0, anchor=tk.NW, image=self.original_photo)
    
    def _on_color_change(self):
        """Handle color selection change."""
        self.current_color = self.color_var.get()
        
        # Show/hide red range 2 frame
        if self.current_color == "red":
            self.red_range2_frame.pack(fill=tk.X, pady=5)
            self._load_red_sliders()
        else:
            self.red_range2_frame.pack_forget()
            self._load_standard_sliders()
        
        self._update_preview()
    
    def _load_standard_sliders(self):
        """Load slider values for white/black colors."""
        thresh = self.thresholds[self.current_color]
        lower = thresh["lower"]
        upper = thresh["upper"]
        
        self.slider_vars["h_lower"].set(lower[0])
        self.slider_vars["s_lower"].set(lower[1])
        self.slider_vars["v_lower"].set(lower[2])
        self.slider_vars["h_upper"].set(upper[0])
        self.slider_vars["s_upper"].set(upper[1])
        self.slider_vars["v_upper"].set(upper[2])
    
    def _load_red_sliders(self):
        """Load slider values for red color (two ranges)."""
        thresh = self.thresholds["red"]
        
        # Range 1
        self.slider_vars["h_lower"].set(thresh["lower1"][0])
        self.slider_vars["s_lower"].set(thresh["lower1"][1])
        self.slider_vars["v_lower"].set(thresh["lower1"][2])
        self.slider_vars["h_upper"].set(thresh["upper1"][0])
        self.slider_vars["s_upper"].set(thresh["upper1"][1])
        self.slider_vars["v_upper"].set(thresh["upper1"][2])
        
        # Range 2
        self.red2_vars["h2_lower"].set(thresh["lower2"][0])
        self.red2_vars["h2_upper"].set(thresh["upper2"][0])
    
    def _update_preview(self):
        """Update the preview image with current thresholds."""
        if self.display_image is None:
            return
        
        # Update thresholds from sliders
        self._update_thresholds_from_sliders()
        
        # Convert to HSV
        hsv = cv2.cvtColor(self.display_image, cv2.COLOR_BGR2HSV)
        
        # Create mask based on current color
        if self.current_color == "red":
            thresh = self.thresholds["red"]
            lower1 = np.array(thresh["lower1"])
            upper1 = np.array(thresh["upper1"])
            lower2 = np.array(thresh["lower2"])
            upper2 = np.array(thresh["upper2"])
            
            mask1 = cv2.inRange(hsv, lower1, upper1)
            mask2 = cv2.inRange(hsv, lower2, upper2)
            mask = cv2.bitwise_or(mask1, mask2)
        else:
            thresh = self.thresholds[self.current_color]
            lower = np.array(thresh["lower"])
            upper = np.array(thresh["upper"])
            mask = cv2.inRange(hsv, lower, upper)
        
        # Create preview
        if self.show_mask_var.get():
            if self.overlay_var.get():
                # Overlay mask on original
                preview = self.display_image.copy()
                color_overlay = np.zeros_like(preview)
                
                if self.current_color == "white":
                    color_overlay[mask > 0] = [255, 255, 255]
                elif self.current_color == "red":
                    color_overlay[mask > 0] = [0, 0, 255]
                else:  # black
                    color_overlay[mask > 0] = [100, 100, 100]
                
                preview = cv2.addWeighted(preview, 0.7, color_overlay, 0.3, 0)
            else:
                # Show mask only
                preview = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        else:
            preview = self.display_image.copy()
        
        # Display preview
        rgb = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        self.preview_photo = ImageTk.PhotoImage(img)
        
        self.preview_canvas.delete("all")
        self.preview_canvas.config(width=img.width, height=img.height)
        self.preview_canvas.create_image(0, 0, anchor=tk.NW, image=self.preview_photo)
    
    def _update_thresholds_from_sliders(self):
        """Update threshold values from current slider positions."""
        if self.current_color == "red":
            self.thresholds["red"]["lower1"] = [
                self.slider_vars["h_lower"].get(),
                self.slider_vars["s_lower"].get(),
                self.slider_vars["v_lower"].get()
            ]
            self.thresholds["red"]["upper1"] = [
                self.slider_vars["h_upper"].get(),
                self.slider_vars["s_upper"].get(),
                self.slider_vars["v_upper"].get()
            ]
            self.thresholds["red"]["lower2"] = [
                self.red2_vars["h2_lower"].get(),
                self.slider_vars["s_lower"].get(),
                self.slider_vars["v_lower"].get()
            ]
            self.thresholds["red"]["upper2"] = [
                self.red2_vars["h2_upper"].get(),
                self.slider_vars["s_upper"].get(),
                self.slider_vars["v_upper"].get()
            ]
        else:
            self.thresholds[self.current_color]["lower"] = [
                self.slider_vars["h_lower"].get(),
                self.slider_vars["s_lower"].get(),
                self.slider_vars["v_lower"].get()
            ]
            self.thresholds[self.current_color]["upper"] = [
                self.slider_vars["h_upper"].get(),
                self.slider_vars["s_upper"].get(),
                self.slider_vars["v_upper"].get()
            ]
    
    def _save_calibration(self):
        """Save current calibration to file."""
        CALIBRATION_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(CALIBRATION_FILE, 'w') as f:
            json.dump(self.thresholds, f, indent=2)
        
        messagebox.showinfo(
            "Success",
            f"Calibration saved to:\n{CALIBRATION_FILE}"
        )
    
    def _reset_defaults(self):
        """Reset thresholds to default values."""
        self.thresholds = {
            "white": {
                "lower": [0, 0, 180],
                "upper": [179, 50, 255],
                "description": "White (shiroji) areas"
            },
            "red": {
                "lower1": [0, 100, 100],
                "upper1": [10, 255, 255],
                "lower2": [160, 100, 100],
                "upper2": [179, 255, 255],
                "description": "Red/Orange (hi) areas"
            },
            "black": {
                "lower": [0, 0, 0],
                "upper": [179, 255, 50],
                "description": "Black (sumi) areas"
            },
        }
        
        self._on_color_change()
        messagebox.showinfo("Reset", "Thresholds reset to defaults.")
    
    def run(self):
        """Run the calibration UI."""
        self.root.mainloop()


def main():
    """Entry point for calibration UI."""
    if not HAS_TKINTER:
        print("Error: tkinter is required but not available.")
        print("Install it with: pip install tk")
        sys.exit(1)
    
    image_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    app = ColorCalibrationUI(image_path)
    app.run()


if __name__ == "__main__":
    main()
