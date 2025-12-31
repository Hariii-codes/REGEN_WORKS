"""
ECO ROUTES INTEGRATION GUIDE
============================

This file provides guidance on how to integrate the new eco-themed pages with the existing Flask application.

1. Eco-themed Pages Created:
   - base-eco.html: New eco-themed base template
   - index-eco.html: Eco-themed dashboard/material scanner
   - drop_points-eco.html: Eco-themed drop points map
   - footprint_dashboard-eco.html: Eco-themed impact dashboard
   - leaderboards-eco.html: Eco-themed leaderboards (NEW)
   - rewards-eco.html: Eco-themed rewards store (NEW)
   - profile-eco.html: Eco-themed user profile

2. Required New Routes (add to routes.py or app.py):

```python
# Leaderboards Route
@app.route('/leaderboards')
@login_required
def leaderboards():
    # Mock data - replace with actual database queries
    leaderboard_data = [
        {'username': 'Alex Johnson', 'points': 9875, 'items_recycled': 342, 'badge': 'Champion'},
        {'username': 'Jane Smith', 'points': 8450, 'items_recycled': 298, 'badge': 'Gold'},
        {'username': 'Mike Chen', 'points': 7230, 'items_recycled': 276, 'badge': 'Silver'},
        # Add more users...
    ]
    return render_template('leaderboards-eco.html', leaderboard_data=leaderboard_data)

# Rewards Route
@app.route('/rewards')
@login_required
def rewards():
    # Mock rewards data - replace with actual database queries
    rewards = [
        {'name': 'Amazon Gift Card', 'points': 2000, 'category': 'vouchers', 'description': '$20 gift card for eco-friendly purchases'},
        {'name': 'Tree Sapling Kit', 'points': 500, 'category': 'plants', 'description': 'Grow your own tree'},
        # Add more rewards...
    ]
    return render_template('rewards-eco.html', rewards=rewards)

# Optional: Toggle between old and eco themes
@app.route('/toggle-theme')
def toggle_theme():
    session['use_eco_theme'] = not session.get('use_eco_theme', False)
    return redirect(request.referrer or url_for('index'))
```

3. Template Switching Logic:

Modify existing route handlers to optionally use eco-themed templates:

```python
def get_template(base_name):
    """Return either eco-themed or regular template based on user preference"""
    if session.get('use_eco_theme', True):
        return f"{base_name}-eco.html"
    return f"{base_name}.html"

# Example usage in routes:
@app.route('/')
def index():
    # ... existing logic ...
    return render_template(get_template('index'), result=result, image_path=image_path, ...)
```

4. Navigation Updates:

Update base templates to include new navigation items:
- Leaderboards
- Rewards
- Impact Dashboard (Footprint Dashboard)

5. CSS and JavaScript Dependencies:

Ensure the following are included in your project structure:
/static/css/
├── eco-design-system.css    # Main eco design system
└── custom.css               # Existing custom styles

/static/js/
├── eco-animations.js       # Eco animations library
├── script.js              # Existing scripts
└── webcam.js              # Existing webcam functionality

6. Font Imports:

The eco theme uses Google Fonts (Inter and Poppins). These are automatically imported in the base-eco.html template.

7. CDN Dependencies:

The eco theme requires the following CDN links:
- Google Fonts (Inter & Poppins)
- Font Awesome 6.4.0
- OpenLayers (for maps)
- Chart.js (for dashboard charts)

8. Integration Steps:

Step 1: Add the new route handlers to your Flask application
Step 2: Update existing route handlers to use get_template() function
Step 3: Add navigation links in base-eco.html
Step 4: Copy the eco-themed templates to your templates folder
Step 5: Copy the static assets (CSS/JS) to your static folder
Step 6: Test all pages to ensure proper functionality

9. Optional Features:

- Theme toggle functionality
- User preference for theme selection
- Smooth transition between old and new themes
- Database integration for leaderboards and rewards

10. Browser Compatibility:

The eco theme supports:
- Chrome 60+
- Firefox 60+
- Safari 12+
- Edge 79+

For older browsers, some CSS features like backdrop-filter and custom properties may not work.

11. Performance Optimizations:

The eco theme includes:
- Lazy loading for images
- Optimized animations using transform/opacity
- Minimal HTTP requests for fonts
- Efficient CSS animations

12. Accessibility Features:

- Semantic HTML structure
- ARIA labels where appropriate
- Keyboard navigation support
- Screen reader friendly
- High contrast color ratios
"""