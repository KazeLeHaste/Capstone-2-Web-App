# Traffic Control Demo Guide

## Quick Demo: How Adaptive Traffic Control Works

### Step 1: Configuration
1. Open Configuration Page
2. Go to "Traffic Light Control" section
3. Select "Adaptive Control (Recommended)"
4. Notice the settings:
   - **Max Gap**: 3.0 seconds (how long to wait for next vehicle)
   - **Min Green**: 5 seconds (minimum green time guaranteed)
   - **Max Green**: 50 seconds (maximum green time allowed)

### Step 2: How It Prioritizes Heavy Traffic

#### Scenario A: Light Traffic Road
```
🚗    [gap > 3s]     [gap > 3s]     🚦
Light traffic → Phase switches after min duration (5s)
Result: Short green time ✅
```

#### Scenario B: Heavy Traffic Road  
```
🚗🚗🚗🚗 [gap < 3s] 🚗🚗🚗🚗 [gap < 3s] 🚗🚗 🚦
Heavy traffic → Phase extends up to max duration (50s)
Result: Long green time ✅
```

### Step 3: Visual Results in Simulation
- **Heavy traffic directions**: Get 30-50 seconds green time
- **Light traffic directions**: Get 5-15 seconds green time
- **Overall result**: Reduced congestion and waiting time

### Step 4: Compare Methods

| Method | Heavy Traffic | Light Traffic | Best For |
|--------|---------------|---------------|----------|
| **Existing** | Network default | Network default | Testing current state |
| **Fixed** | Same as light | Same as heavy | Predictable timing |
| **Adaptive** ⭐ | Long green (up to 50s) | Short green (5-15s) | **Real traffic response** |

## Quick Test Instructions

1. **Run with Fixed Control**:
   - Set method to "Fixed"
   - Set cycle time to 90s
   - Notice: All directions get equal time

2. **Run with Adaptive Control**:
   - Set method to "Adaptive Control" 
   - Keep default parameters
   - Notice: Busy roads get more green time automatically

3. **Add Traffic Lights**:
   - Set method to "Add Adaptive Lights to Priority Intersections"
   - Set speed threshold to 50 km/h
   - Notice: New traffic lights appear at busy priority junctions

## Expected Results

### With Heavy Traffic (scale > 2.0x):
- **Adaptive**: Main roads get 40-50s green, side roads get 5-10s
- **Fixed**: All roads get same time regardless of demand
- **Efficiency**: Adaptive reduces overall waiting time by 30-50%

### With Light Traffic (scale < 1.0x):
- **Adaptive**: All roads get near-minimum green time
- **Fixed**: Wastes time with long unnecessary green phases
- **Efficiency**: Adaptive reduces cycle time and delays

## Pro Tips

1. **For Realistic Simulations**: Use Adaptive Control with default settings
2. **For Research**: Compare Fixed vs Adaptive with same traffic scenario  
3. **For Heavy Congestion**: Lower max-gap to 2.0s for faster switching
4. **For Light Traffic**: Increase max-gap to 4.0s for smoother flow

---

**Bottom Line**: Adaptive control automatically gives more green time to the roads that need it most! 🎯