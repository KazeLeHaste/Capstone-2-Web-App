# Custom Traffic Light Timing - Quick Testing Guide

## Prerequisites
- Backend server running on port 5000
- Frontend server running on port 3000
- SUMO installed and accessible

## Test Procedure

### Test 1: Basic Custom Timing Configuration

1. **Navigate to Configuration Page**
   - Open browser to http://localhost:3000
   - Click "Configuration" tab

2. **Set Custom Timing**
   - Scroll to "Traffic Light Control" section
   - In "Control Method" dropdown, select "Custom Timing"
   - You should see 4 new input fields appear

3. **Configure Timings**
   - Main Direction Green Time: `40` seconds
   - Cross Direction Green Time: `35` seconds
   - Yellow Phase Duration: `4` seconds
   - All-Red Clearance Time: `3` seconds

4. **Verify UI Feedback**
   - Check that "Total Cycle Time" shows `98 seconds`
   - Verify phase sequence is displayed correctly
   - Ensure all values are reflected in the summary

5. **Save Configuration**
   - Click "Save Configuration & Continue"
   - Verify success message appears

### Test 2: Network Selection and Launch

1. **Select Network**
   - Click "Select Network" button
   - Choose "SM Bacoor Area" or any other network

2. **Launch Simulation**
   - Enable SUMO GUI option
   - Click "Launch Simulation"
   - Wait for SUMO GUI to open

3. **Verify Traffic Lights**
   - In SUMO GUI, right-click on a traffic light
   - Select "Show Phases"
   - Verify phases show:
     - Phase 0: 40s duration
     - Phase 1: 4s duration
     - Phase 2: 3s duration
     - Phase 3: 35s duration
     - Phase 4: 4s duration
     - Phase 5: 3s duration

### Test 3: Edge Case - Minimum Values

1. **Return to Configuration**
   - Stop current simulation
   - Go back to Configuration page
   - Select "Custom Timing" method

2. **Set Minimum Values**
   - Main Direction Green Time: `5` seconds
   - Cross Direction Green Time: `5` seconds
   - Yellow Phase Duration: `2` seconds
   - All-Red Clearance Time: `0` seconds

3. **Verify Total Cycle**
   - Should show `14 seconds`

4. **Launch and Test**
   - Select network and launch
   - Verify very fast traffic light cycling

### Test 4: Edge Case - Maximum Values

1. **Configure Maximum Values**
   - Main Direction Green Time: `180` seconds
   - Cross Direction Green Time: `180` seconds
   - Yellow Phase Duration: `6` seconds
   - All-Red Clearance Time: `10` seconds

2. **Verify Total Cycle**
   - Should show `392 seconds` (6.5 minutes)

3. **Launch and Test**
   - Launch simulation
   - Verify very long green phases

### Test 5: Compare with Other Methods

1. **Test Existing Method**
   - Configure with "Keep Existing Traffic Lights"
   - Launch simulation
   - Note traffic light behavior

2. **Test Fixed Method**
   - Configure with "Fixed-Time Control"
   - Set cycle time to 90 seconds
   - Launch and compare

3. **Test Adaptive Method**
   - Configure with "Adaptive Control"
   - Launch and observe dynamic behavior

4. **Test Custom Method Again**
   - Return to custom timing with known values
   - Verify custom timing provides exact control

## Expected Results

### ✅ Success Criteria

- [ ] Custom timing option appears in dropdown
- [ ] Four input fields appear when custom is selected
- [ ] Total cycle time calculated correctly
- [ ] Phase sequence displayed correctly
- [ ] Configuration saves without errors
- [ ] SUMO launches successfully
- [ ] Traffic lights show custom phase durations
- [ ] Traffic lights cycle through all 6 phases
- [ ] Phase states (green/yellow/red) are correct
- [ ] Minimum value constraints work (no values < minimum)
- [ ] Maximum value constraints work (no values > maximum)

### ⚠️ Common Issues

**Issue**: Custom timing option not appearing
- **Solution**: Clear browser cache and reload page

**Issue**: Phase durations not matching in SUMO
- **Solution**: Check backend console for debug messages about traffic light generation

**Issue**: Traffic lights not using custom timing
- **Solution**: Verify network has traffic lights, check that "existing_logic" is False

**Issue**: Simulation crashes with custom timing
- **Solution**: Check that all phase durations are within valid ranges

## Backend Verification

### Check Backend Logs

Look for these debug messages in backend console:

```
DEBUG: Custom timing - Main green: Xs, Cross green: Ys, Yellow: Zs, All-red: Ws
DEBUG: Generated N custom timer traffic light configurations
```

### Verify Additional Files

After launching simulation, check session directory:
- Navigate to `backend/sessions/session_XXXXXXXX/`
- Look for `traffic_lights.add.xml` or modified `.add.xml` file
- Open in text editor
- Verify `<tlLogic>` elements have correct phase durations

Example expected XML:
```xml
<tlLogic id="..." type="static" programID="0" offset="0">
    <!-- Custom timing configuration - Total cycle: 98s -->
    <phase duration="40" state="..."/>
    <phase duration="4" state="..."/>
    <phase duration="3" state="..."/>
    <phase duration="35" state="..."/>
    <phase duration="4" state="..."/>
    <phase duration="3" state="..."/>
</tlLogic>
```

## Troubleshooting

### Network Has No Traffic Lights
Some networks may not have traffic lights defined. Use these networks for testing:
- ✅ SM Bacoor Area
- ✅ Jollibee Molino Area
- ✅ SM Molino Area
- ✅ St. Dominic Area

### Traffic Lights Not Changing
1. Ensure simulation is running (not paused)
2. Check simulation time is advancing
3. Verify phase durations are reasonable (not too long)

### Custom Settings Not Persisting
1. Check browser console for JavaScript errors
2. Verify backend API is responding
3. Check session configuration file in backend

## Performance Testing

### Test with Different Traffic Scales

1. **Light Traffic (0.5x)**
   - Custom timing: 20s/20s green
   - Observe if phases complete with minimal waiting

2. **Normal Traffic (1.0x)**
   - Custom timing: 30s/30s green
   - Check for balanced flow

3. **Heavy Traffic (2.0x)**
   - Custom timing: 45s/45s green
   - Verify queues clear during green phases

## Advanced Testing

### Test Multiple Networks
- Run same custom timing on different networks
- Verify timing applies correctly to different intersection types
- Note any networks where custom timing doesn't work

### Test Long Simulations
- Set simulation time to 1 hour (3600s)
- Use moderate custom timings (30s/30s)
- Let simulation run completely
- Verify traffic lights remain consistent throughout

### Test with Analytics
- Enable live data collection
- Run simulation with custom timing
- Check that KPI data is collected correctly
- Verify charts show expected patterns

## Reporting Issues

If you encounter issues, please report with:
1. Custom timing values used
2. Network selected
3. Other configuration settings (traffic scale, vehicle types, etc.)
4. Screenshot of error or unexpected behavior
5. Backend console logs
6. Browser console errors

## Success!

If all tests pass, the custom traffic light timing feature is working correctly! 🎉
