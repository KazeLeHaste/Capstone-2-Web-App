# Averaged Traffic Data for Networks Without BTMD Data

## Overview

For intersections without specific BTMD traffic data, the system now automatically calculates and applies averaged traffic patterns from the 5 intersections with real BTMD data.

---

## Calculated Average Traffic Data

### Source Intersections (with BTMD Data)
1. **SM Bacoor Area** - 2,634 veh/hr avg, 2,823 veh/hr peak
2. **SM Molino Area** - 1,916 veh/hr avg, 2,085 veh/hr peak
3. **Jollibee Molino Area** - 1,380 veh/hr avg, 1,485 veh/hr peak
4. **St Dominic Area** - 874 veh/hr avg, 974 veh/hr peak
5. **Bayanan Area** - 619 veh/hr avg, 763 veh/hr peak

### Average Values Applied to Networks Without Data
- **Average vehicles/hour:** 1,484 veh/hr
- **Peak vehicles/hour:** 1,626 veh/hr
- **Total vehicles/day:** 23,750 vehicles (16-hour observation)

### Averaged Vehicle Mix

| Vehicle Type | Proportion | Source |
|-------------|-----------|---------|
| **Passenger** | 46.9% | Average across all 5 intersections |
| **Motorcycle** | 29.9% | Average across all 5 intersections |
| **Truck** | 7.9% | Average across all 5 intersections |
| **Jeepney** | 10.3% | Average across all 5 intersections |
| **Bus** | 0.8% | Average across all 5 intersections |
| **Taxi** | 3.1% | Merged into Passenger in SUMO |

**Note:** Taxi vehicles are mapped to the passenger vehicle class in SUMO, so the effective passenger proportion is 50.0% (46.9% + 3.1%).

### Averaged Hourly Patterns

The system also calculates averaged hourly traffic multipliers:

| Time Period | Multiplier | Notes |
|------------|-----------|--------|
| 6-7 AM | 1.10x | Morning peak |
| 7-8 AM | 1.06x | Morning rush continues |
| 8-9 AM | 1.05x | Late morning |
| 9-10 AM | 1.06x | Mid-morning |
| 10-11 AM | 1.02x | Pre-noon |
| 11-12 PM | 1.03x | Lunch approach |
| 12-1 PM | 1.03x | Lunch hour |
| 1-2 PM | 1.03x | Post-lunch |
| 2-3 PM | 1.02x | Afternoon |
| 3-4 PM | 1.01x | Mid-afternoon |
| 4-5 PM | 0.97x | Late afternoon |
| 5-6 PM | 0.96x | Evening transition |
| 6-7 PM | 0.96x | Evening |
| 7-8 PM | 0.91x | Late evening |
| 8-9 PM | 0.88x | Night approach |
| 9-10 PM | 0.85x | Night traffic |

---

## Networks Using Averaged Data

### 1. Perpetual Molino Area
- **Status:** ✅ Calibrated with averaged BTMD data
- **Generated:** 3,264 vehicles over 2 hours
- **Traffic rate:** 1,632 veh/hr at 1.0x intensity
- **Vehicle breakdown:**
  - Passenger: 1,633 (50.0%)
  - Motorcycle: 976 (29.9%)
  - Truck: 257 (7.9%)
  - Jeepney: 336 (10.3%)
  - Bus: 25 (0.8%)

### 2. Statesfield Area
- **Status:** ✅ Calibrated with averaged BTMD data
- **Generated:** 3,264 vehicles over 2 hours
- **Traffic rate:** 1,632 veh/hr at 1.0x intensity
- **Vehicle breakdown:**
  - Passenger: 1,633 (50.0%)
  - Motorcycle: 976 (29.9%)
  - Truck: 257 (7.9%)
  - Jeepney: 336 (10.3%)
  - Bus: 25 (0.8%)

---

## Comparison: Averaged vs Specific BTMD Data

### Traffic Volume Comparison

| Network | Data Source | Avg (veh/hr) | Peak (veh/hr) | Ratio to Average |
|---------|------------|--------------|---------------|------------------|
| SM Bacoor | BTMD Specific | 2,634 | 2,823 | 177% of avg |
| SM Molino | BTMD Specific | 1,916 | 2,085 | 129% of avg |
| Jollibee Molino | BTMD Specific | 1,380 | 1,485 | 100% of avg |
| St Dominic | BTMD Specific | 874 | 974 | 59% of avg |
| Bayanan | BTMD Specific | 619 | 763 | 42% of avg |
| **Perpetual Molino** | **Averaged** | **1,484** | **1,626** | **100% (baseline)** |
| **Statesfield** | **Averaged** | **1,484** | **1,626** | **100% (baseline)** |

### Vehicle Mix Comparison

**Passenger Vehicles:**
- SM Bacoor: 45.2%
- SM Molino: 58.1%
- Jollibee Molino: 52.7%
- St Dominic: 34.4%
- Bayanan: 44.4%
- **Average: 46.9%** → Applied to Perpetual & Statesfield

**Motorcycles:**
- SM Bacoor: 31.9%
- SM Molino: 32.2%
- Jollibee Molino: 32.0%
- St Dominic: 33.5%
- Bayanan: 20.0%
- **Average: 29.9%** → Applied to Perpetual & Statesfield

**Trucks:**
- SM Bacoor: 10.1%
- SM Molino: 5.6%
- Jollibee Molino: 2.4%
- St Dominic: 18.1%
- Bayanan: 3.3%
- **Average: 7.9%** → Applied to Perpetual & Statesfield

---

## Methodology

### Averaging Calculation

The system calculates averages using arithmetic mean across all 5 intersections with BTMD data:

1. **Traffic Volume:**
   ```
   Average veh/hr = (2634 + 1916 + 1380 + 874 + 619) / 5 = 1,484 veh/hr
   Peak veh/hr = (2823 + 2085 + 1485 + 974 + 763) / 5 = 1,626 veh/hr
   ```

2. **Vehicle Mix:**
   ```
   For each vehicle type:
   Average proportion = Σ(proportion from each intersection) / 5
   ```

3. **Hourly Patterns:**
   ```
   For each time slot:
   Average multiplier = Σ(multiplier from each intersection) / 5
   ```

### Application to Networks

When calibrating a network without specific BTMD data:

1. **System detects** no matching BTMD data for the network name
2. **Notifies user** with warning and list of source intersections
3. **Applies averaged values** for:
   - Target vehicle count
   - Vehicle type proportions
   - Hourly traffic patterns
4. **Generates routes** using OSM-validated edges (same as BTMD networks)
5. **Marks calibration report** with `"using_averaged_data": true`

---

## Traffic Intensity Scaling

The averaged data supports the same 1.0x to 10.0x traffic intensity scaling:

- **1.0x:** 1,484 veh/hr (normal traffic, averaged baseline)
- **5.5x:** 1,555 veh/hr (moderate increase)
- **10.0x:** 1,626 veh/hr (peak rush hour, averaged peak)

Linear interpolation between baseline and peak based on intensity factor.

---

## Benefits of This Approach

### ✅ **Realistic Baseline**
- Uses actual traffic data from 5 real intersections
- Reflects typical Bacoor City traffic patterns
- Better than arbitrary values or empty networks

### ✅ **Consistent Methodology**
- All networks use the same calibration system
- Networks with specific data: use actual BTMD measurements
- Networks without data: use averaged patterns from real data
- Same vehicle routing, same pre-computed routes

### ✅ **Transparency**
- System clearly indicates when averaged data is used
- Calibration reports track data source
- Users can see which intersections contributed to average

### ✅ **Reasonable Estimates**
- Average of 1,484 veh/hr represents medium traffic
- Not as busy as SM Bacoor (2,634 veh/hr)
- Busier than Bayanan (619 veh/hr)
- Suitable default for unknown intersections

---

## Calibration Report Indicators

For networks using averaged data, the calibration report includes:

```json
{
  "success": true,
  "network": "Perpetual Molino Area",
  "btmd_data": "Average BTMD Intersection (Calculated)",
  "using_averaged_data": true,
  "source_intersections": [
    "SM Bacoor Area",
    "SM Molino Area",
    "Jollibee Molino Area",
    "St Dominic Area",
    "Bayanan Area"
  ],
  "avg_vehicles_per_hour": 1484,
  "peak_hour_volume": 1626,
  ...
}
```

This makes it easy to identify which networks use specific vs averaged data.

---

## Future Enhancements

### Potential Improvements

1. **Weighted Averages:**
   - Weight intersections by similarity to target network
   - Consider road classification, size, location

2. **Category-Based Averaging:**
   - Separate averages for highway vs local intersections
   - Different patterns for commercial vs residential areas

3. **Time-of-Day Profiles:**
   - More granular hourly patterns
   - Weekend vs weekday differences

4. **Dynamic Updates:**
   - As new BTMD data becomes available, automatically recalculate averages
   - Option to recalibrate networks with updated averages

---

## Conclusion

**The averaged traffic data system enables realistic traffic simulation for ALL networks in the system, not just those with specific BTMD data.**

Networks with specific BTMD data continue to use their accurate, measured values, while networks without data now receive realistic traffic patterns averaged from 5 real Bacoor City intersections. This ensures consistency across the entire simulation system while maintaining accuracy where real data exists.

All 7 networks in the system are now production-ready with realistic traffic patterns! 🎉
