# Icon-Based UI Guide for Low-Literacy Users

## Universal Icons Used Throughout ReGenWorks

### Primary Actions (Always with Icons)
- **Scan Waste**: 📷 Camera icon (fas fa-camera)
- **Drop Points**: 📍 Map marker icon (fas fa-map-marker-alt)
- **Dashboard**: 📊 Chart icon (fas fa-chart-line)
- **Projects**: 🏗️ Project icon (fas fa-project-diagram)
- **Rewards**: 🏆 Trophy icon (fas fa-trophy)
- **Profile**: 👤 User icon (fas fa-user-circle)

### Secondary Actions
- **Upload**: ☁️ Cloud upload (fas fa-cloud-upload-alt)
- **Webcam**: 📹 Video camera (fas fa-video)
- **Voice Input**: 🎤 Microphone (fas fa-microphone)
- **Submit**: ✅ Check mark (fas fa-check)
- **Cancel**: ❌ X mark (fas fa-times)
- **Settings**: ⚙️ Gear (fas fa-cog)

### Status Indicators
- **Success**: ✅ Green check (text-success)
- **Warning**: ⚠️ Yellow exclamation (text-warning)
- **Error**: ❌ Red X (text-danger)
- **Info**: ℹ️ Blue info (text-info)

### Material Types (Icons)
- **Plastic**: 🫧 Bottle icon (fas fa-wine-bottle)
- **Paper**: 📄 Document icon (fas fa-file-alt)
- **Metal**: 🔩 Wrench icon (fas fa-wrench)
- **Glass**: 🪟 Window icon (fas fa-window-maximize)
- **Electronic**: 💻 Laptop icon (fas fa-laptop)
- **Organic**: 🍃 Leaf icon (fas fa-leaf)

## Implementation Strategy

1. **Icon-First Design**: All buttons show icon first, text second
2. **Large Touch Targets**: Minimum 44x44px for mobile
3. **Color Coding**: Consistent colors for actions (blue=primary, green=success, red=danger)
4. **Tooltips**: Hover/tap shows text in selected language
5. **Voice Labels**: Icons have aria-labels for screen readers

## Example Button Structure

```html
<button class="btn btn-primary btn-lg">
    <i class="fas fa-camera me-2"></i>
    <span>{{ get_localized_string('nav.scan', lang) }}</span>
</button>
```

## Voice Command Icons

All voice-enabled fields have a microphone button:
- Green mic = Ready to listen
- Red mic = Currently listening
- Disabled = Not supported

