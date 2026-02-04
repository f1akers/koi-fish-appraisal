# Feature 3: Frontend Camera Capture

**Status:** � Completed  
**Last Updated:** 2026-02-05

---

## Overview

A React component that accesses the user's camera, displays a live preview, and captures images for koi fish appraisal.

---

## User Flow

1. User opens the application
2. Camera permission is requested
3. Live camera feed is displayed
4. User positions koi fish and reference coin in frame
5. User clicks "Capture" button
6. Image is captured and sent to backend
7. Loading state while processing
8. Results are displayed (see Feature 4)

---

## UI Components

### CameraCapture Component

```typescript
interface CameraProps {
  onCapture: (imageData: Blob) => void;
  onError: (error: Error) => void;
}
```

**Features:**
- Live video preview
- Capture button
- Camera switch (front/back) for mobile
- Guide overlay showing optimal positioning
- Flash/torch control (if available)

### Guide Overlay

Visual guide to help users:
- Outline showing recommended fish position
- Circle showing recommended coin position
- Tips text: "Ensure coin and fish are clearly visible"

---

## Technical Implementation

### Camera Access

```typescript
const initCamera = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: 'environment', // Prefer back camera
        width: { ideal: 1920 },
        height: { ideal: 1080 }
      }
    });
    videoRef.current.srcObject = stream;
  } catch (error) {
    // Handle permission denied or no camera
  }
};
```

### Image Capture

```typescript
const captureImage = (): Blob => {
  const canvas = document.createElement('canvas');
  canvas.width = videoRef.current.videoWidth;
  canvas.height = videoRef.current.videoHeight;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(videoRef.current, 0, 0);
  
  return new Promise((resolve) => {
    canvas.toBlob(resolve, 'image/jpeg', 0.9);
  });
};
```

### API Call

```typescript
const sendForAppraisal = async (imageBlob: Blob) => {
  const formData = new FormData();
  formData.append('image', imageBlob, 'capture.jpg');
  
  const response = await fetch('/api/appraise', {
    method: 'POST',
    body: formData
  });
  
  return response.json();
};
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `frontend/src/components/CameraCapture.tsx` | Main camera component |
| `frontend/src/components/GuideOverlay.tsx` | Positioning guide overlay |
| `frontend/src/hooks/useCamera.ts` | Camera access hook |
| `frontend/src/services/api.ts` | API service functions |

---

## Error Handling

| Error | User Message |
|-------|--------------|
| Camera permission denied | "Please allow camera access to use this feature" |
| No camera available | "No camera detected on this device" |
| API error | "Failed to process image. Please try again" |
| Network error | "Network error. Please check your connection" |

---

## Responsive Design

- **Desktop:** Larger preview, side panel for controls
- **Tablet:** Full-width preview, bottom controls
- **Mobile:** Full-screen preview, floating capture button

---

## Accessibility

- Keyboard navigation for capture button
- Screen reader announcements for state changes
- High contrast mode support
- Focus indicators

---

## Testing Checklist

- [ ] Camera permission handling (granted/denied)
- [ ] Image capture produces valid Blob
- [ ] API integration works correctly
- [ ] Loading states display properly
- [ ] Error states display properly
- [ ] Works on mobile browsers
- [ ] Works on desktop browsers
- [ ] Camera switch works on mobile

---

## Completion Checklist

When this feature is complete:
- [ ] Camera capture component implemented
- [ ] Guide overlay implemented
- [ ] API integration working
- [ ] Error handling implemented
- [ ] Responsive design tested
- [ ] Accessibility reviewed
- [ ] Update status in FEATURES_INDEX.md to 🟢
