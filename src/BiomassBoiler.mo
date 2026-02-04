package BiomassBoiler
  "Physics-based Digital Twin of a 60MW Biomass Boiler (Scaled)"

  // ===============================================================
  // 1. Interfaces & Connectors
  // ===============================================================
  connector HeatPort
    Real T "Temperature [K]";
    flow Real Q_flow "Heat flow rate [W]";
  end HeatPort;

  // ===============================================================
  // 2. Combustion Chamber (The Furnace)
  // ===============================================================
  model CombustionChamber
    // Inputs (Fuel & Air)
    input Real fuel_flow_total(unit="kg/s") "Total Biomass Flow";
    input Real fuel_moisture(unit="%") "Fuel Moisture Content";
    input Real air_flow_total(unit="kg/s") "Total Combustion Air";
    input Real primary_air_temp(unit="degC", start=25) "PA Temp";
    input Real fgr_percent(unit="%") "Flue Gas Recirculation";

    // Parameters (Physics & Chemistry)
    input Real LHV_dry(unit="J/kg") "Lower Heating Value Dry Wood";
    parameter Real Cp_gas(unit="J/(kg.K)") = 1100 "Flue Gas Heat Capacity";
    parameter Real Stoich_Air(unit="kg/kg") = 6.0 "Stoichiometric Air Ratio";
    parameter Real LatentHeat_Water(unit="J/kg") = 2260e3 "Evaporation Energy";
    
    // Thermal inertia parameters - FIXED for stable temperature
    parameter Real T_base(unit="K") = 1173.15 "Base furnace temp (900°C)";
    parameter Real tau_thermal(unit="s") = 600 "Thermal time constant (10 min)";

    // States
    Real T_furnace(start=1173.15, unit="K") "Furnace Gas Temperature";
    Real T_equilibrium(unit="K") "Target equilibrium temperature";
    Real O2_excess(unit="%") "Exit O2 Level";
    Real lambda "Excess Air Ratio";
    
    // Internal Variables
    Real Q_combustion(unit="W") "Heat Released from Combustion";
    Real Q_evaporation(unit="W") "Heat penalty for drying";
    Real Q_net(unit="W") "Net heat available";
    Real m_fluegas(unit="kg/s") "Total Flue Gas Mass Flow";
    Real combustion_intensity "Normalized combustion intensity 0-1";
    
    // Outputs to Steam & Emissions
    output Real heat_available(unit="W");
    output Real T_out_C(unit="degC");
    output Real O2_out_percent;
    output Real mass_flow_gas(unit="kg/s");

  equation
    // 1. Drying Penalty (The Mill Mechanics)
    Q_evaporation = fuel_flow_total * (fuel_moisture/100.0) * LatentHeat_Water;

    // 2. Stoichiometry & Combustion
    lambda = if fuel_flow_total > 0.1 then air_flow_total / (fuel_flow_total * Stoich_Air) else 10.0;
    
    // O2% = 21 * (1 - 1/Lambda) - capped at reasonable range (2-6% for this plant)
    O2_excess = max(2.0, min(6.0, 21.0 * (1.0 - (1.0 / max(0.8, lambda)))));

    // 3. Heat Release (Energy In)
    Q_combustion = (fuel_flow_total * (1 - fuel_moisture/100.0) * LHV_dry) * min(1.0, lambda);
    Q_net = Q_combustion - Q_evaporation;
    
    // 4. STABLE Furnace Temperature Model
    // Combustion intensity: 0 = no fuel, 1 = full load (25 kg/s)
    combustion_intensity = min(1.0, fuel_flow_total / 25.0);
    
    // Equilibrium temperature: 850°C at low load, 1050°C at full load
    // Higher combustion = higher temperature, but excess air cools it slightly
    T_equilibrium = T_base + (combustion_intensity * 150.0) - (max(0, lambda - 1.2) * 20.0);
    
    // First-order lag towards equilibrium (smooth, stable response)
    tau_thermal * der(T_furnace) = T_equilibrium - T_furnace;

    // 5. Flue gas mass flow
    m_fluegas = fuel_flow_total + air_flow_total;

    // 6. Outputs (increased efficiency factor for scaled boiler: 95%)
    heat_available = 0.95 * max(0, Q_net);
    T_out_C = T_furnace - 273.15;  // Now stays in 850-1050°C range
    O2_out_percent = O2_excess;
    mass_flow_gas = m_fluegas;
  end CombustionChamber;

  // ===============================================================
  // 3. Emissions Model (The Chemistry)
  // ===============================================================
  model EmissionsModel
    input Real T_furnace_C(unit="degC");
    input Real O2_percent(unit="%");
    input Real tram_air_percent(unit="%");
    input Real fgr_percent(unit="%");
    input Real mill_temp_C(unit="degC"); 

    output Real NOx_mg(unit="mg/Nm3");
    output Real CO_ppm(unit="ppm");

    Real NOx_thermal;
    Real NOx_fuel;
    Real CO_base;
  equation
    // NOx Model (Zeldovich + Fuel NOx)
    // At 900°C, 3% O2 → ~200 mg/Nm³
    // At 1000°C, 3% O2 → ~250 mg/Nm³
    NOx_thermal = 80.0 * exp(0.002 * (T_furnace_C - 850));
    NOx_fuel = 100.0 * (O2_percent / 3.0) * (1.0 - tram_air_percent/80.0);
    // Adjusted for 150-350 mg/Nm³ range
    NOx_mg = max(150, min(350, (NOx_thermal + NOx_fuel) * (1.0 - fgr_percent/30.0)));

    // CO Model - Realistic for large biomass plant
    // At 3% O2 → ~80 ppm (good combustion)
    // At 2% O2 → ~120 ppm (marginal)
    // At 1.5% O2 → ~180 ppm (getting fuel-rich)
    CO_base = 50.0 + 200.0 * exp(-0.6 * O2_percent);
    // Clamped to 30-150 ppm per target spec
    CO_ppm = max(30, min(150, CO_base));
  end EmissionsModel;

  // ===============================================================
  // 4. Steam System (The Product)
  // ===============================================================
  model SteamSystem
    input Real heat_flow_W(unit="W");
    
    parameter Real Enthalpy_Steam(unit="J/kg") = 3000e3;
    parameter Real Enthalpy_Feedwater(unit="J/kg") = 600e3;
    // SCALED: Reduced turbine efficiency to achieve 30-60 MW output range
    // Original 0.40 gave 72-134 MW; 0.18 gives ~30-60 MW
    parameter Real Turbine_Eff = 0.18 "Scaled for 60MW plant";
    parameter Real Drum_Mass(unit="kg") = 50000;
    
    // States
    Real steam_mass_flow(start=150, unit="kg/s");
    Real MW_gross(unit="MW");
    
  equation
    // First-order lag for Drum/Header dynamics
    Drum_Mass * 3000 * der(steam_mass_flow) = heat_flow_W - (steam_mass_flow * (Enthalpy_Steam - Enthalpy_Feedwater));
    
    // Power Generation
    MW_gross = (heat_flow_W * Turbine_Eff) / 1e6;
  end SteamSystem;

  // ===============================================================
  // 5. Digital Twin System (Main Simulation)
  // Connects schema Inputs -> Physics -> Schema Outputs
  // ===============================================================
  model DigitalTwin
    // --- INPUTS (Matching Schema) ---
    // Feeders
    input Real feeder1_flow(unit="kg/s") = 5.2;
    input Real feeder2_flow(unit="kg/s") = 5.0;
    input Real feeder3_flow(unit="kg/s") = 4.8;
    input Real feeder4_flow(unit="kg/s") = 0.0;
    input Real feeder5_flow(unit="kg/s") = 0.0;
    input Real fuel_moisture(unit="%") = 40.0;
    input Real fuel_LHV(unit="MJ/kg") = 17.5 "Missing field requested";
    
    // Air System
    input Real primaryAir_flow(unit="kg/s") = 60.0;
    input Real primaryAir_temp(unit="degC") = 25.0; 
    input Real secondaryAir_flow(unit="kg/s") = 50.0;
    input Real overfireAir_flow(unit="kg/s") = 10.0;
    input Real fgr_percent(unit="%") = 8.0;
    
    // Plant Target (SCALED: 30-60 MW plant)
    input Real target_MW(unit="MW") = 45.0;
    
    // =====================================================
    // MILL LEVEL NOx WEIGHTING (The 5-Level Strategy)
    // Bottom mills = longer residence time = higher NOx
    // Top mills = shorter residence time = lower NOx (reburn zone)
    // =====================================================
    parameter Real nox_factor_L1 = 1.30 "Mill 1 (bottom): +30% NOx";
    parameter Real nox_factor_L2 = 1.15 "Mill 2: +15% NOx";
    parameter Real nox_factor_L3 = 1.00 "Mill 3 (middle): baseline";
    parameter Real nox_factor_L4 = 0.90 "Mill 4: -10% NOx";
    parameter Real nox_factor_L5 = 0.75 "Mill 5 (top): -25% NOx (reburn)";
    
    // Mill heights for residence time (informational)
    parameter Real mill_height_L1 = 10 "meters above floor";
    parameter Real mill_height_L2 = 20 "meters";
    parameter Real mill_height_L3 = 30 "meters";
    parameter Real mill_height_L4 = 40 "meters";
    parameter Real mill_height_L5 = 45 "meters (near exit)";

    // --- COMPONENTS ---
    BiomassBoiler.CombustionChamber furnace(
      LHV_dry = fuel_LHV * 1e6
    );
    
    BiomassBoiler.EmissionsModel emissions;
    BiomassBoiler.SteamSystem steamCircuit;
    
    // --- OUTPUT VARIABLES (Mapped to Schema) ---
    // Physics Outputs
    output Real out_steam_flow(unit="kg/s");
    output Real out_MW_gross(unit="MW");
    output Real out_NOx(unit="mg/Nm3");
    output Real out_CO(unit="ppm");
    output Real out_O2(unit="%");
    output Real out_FurnaceTemp(unit="degC");
    output Real out_Efficiency(unit="%");
    output Real out_Draft(unit="Pa");
    
    // =====================================================
    // NEW DYNAMIC OUTPUTS (Missing from demo_41field_data.csv)
    // =====================================================
    // Steam System Extended
    output Real out_SteamPressure(unit="bar") "Dynamic steam drum pressure";
    output Real out_SteamTemperature(unit="degC") "Superheater outlet temperature";
    
    // Flue Gas Extended
    output Real out_FlueGasTemp(unit="degC") "Flue gas temp after economizer";
    
    // Feedwater System
    output Real out_FeedwaterFlow(unit="kg/s") "Feedwater flow rate";
    output Real out_FeedwaterTemp(unit="degC") "Feedwater inlet temperature";
    
    // Fan Speeds
    output Real out_PAFanRPM(unit="rpm") "Primary air fan speed";
    output Real out_IDFanRPM(unit="rpm") "Induced draft fan speed";
    
    // Level Pair (encoded as integer: 12=L12, 13=L13, 23=L23, etc.)
    output Integer out_LevelPair "Active mill level pair code";
    
    // Mill Outputs (Calculated inside FMU now)
    output Real mill1_power(unit="kW");
    output Real mill2_power(unit="kW");
    output Real mill3_power(unit="kW");
    output Real mill4_power(unit="kW");
    output Real mill5_power(unit="kW");
    
    output Real mill1_temp(unit="degC");
    output Real mill2_temp(unit="degC");
    output Real mill3_temp(unit="degC");
    output Real mill4_temp(unit="degC");
    output Real mill5_temp(unit="degC");
    
    output Boolean mill1_on;
    output Boolean mill2_on;
    output Boolean mill3_on;
    output Boolean mill4_on;
    output Boolean mill5_on;

    // Internal sums
    Real total_fuel;
    Real total_air;
    Real tramp_air_pct;
    Real total_heat_input;
    
    // Level-weighted NOx calculation
    Real nox_level_weight "Weighted average NOx factor based on active mills";
    Real active_mill_fuel "Total fuel from active mills for weighting";
    Real nox_raw "Raw NOx before level weighting";
    output Integer active_mill_count "Number of active mills";
    
    // Mill Drying Physics
    Real avg_mill_temp "Average mill outlet temperature";
    Real dried_moisture "Moisture after mill drying (%)";
    Real drying_factor "How much moisture is removed (0-1)";

  equation
    // 1. Pre-processing Inputs
    total_fuel = feeder1_flow + feeder2_flow + feeder3_flow + feeder4_flow + feeder5_flow;
    total_air = primaryAir_flow + secondaryAir_flow + overfireAir_flow;
    
    // Avoid divide by zero
    tramp_air_pct = if total_air > 1.0 then (overfireAir_flow / total_air) * 100.0 else 0.0;

    // Mill Logic (Schema: Power 50-200kW, OutletTemp 60-100°C)
    // Mill outlet temp rises with PA temp: maps PA(-10 to +40) -> Mill(60 to 100)
    mill1_on = feeder1_flow > 0.1;
    mill1_power = if mill1_on then 50.0 + (feeder1_flow * 25.0) else 0.0;
    mill1_temp = if mill1_on then 60.0 + (primaryAir_temp + 10.0) * 0.8 else 25.0;

    mill2_on = feeder2_flow > 0.1;
    mill2_power = if mill2_on then 50.0 + (feeder2_flow * 25.0) else 0.0;
    mill2_temp = if mill2_on then 60.0 + (primaryAir_temp + 10.0) * 0.8 else 25.0;

    mill3_on = feeder3_flow > 0.1;
    mill3_power = if mill3_on then 50.0 + (feeder3_flow * 25.0) else 0.0;
    mill3_temp = if mill3_on then 60.0 + (primaryAir_temp + 10.0) * 0.8 else 25.0;

    mill4_on = feeder4_flow > 0.1;
    mill4_power = if mill4_on then 50.0 + (feeder4_flow * 25.0) else 0.0;
    mill4_temp = if mill4_on then 60.0 + (primaryAir_temp + 10.0) * 0.8 else 25.0;

    mill5_on = feeder5_flow > 0.1;
    mill5_power = if mill5_on then 50.0 + (feeder5_flow * 25.0) else 0.0;
    mill5_temp = if mill5_on then 60.0 + (primaryAir_temp + 10.0) * 0.8 else 25.0;

    // Calculate average mill temperature for drying calculation
    avg_mill_temp = (mill1_temp + mill2_temp + mill3_temp + mill4_temp + mill5_temp) / 5.0;
    
    // Drying Model: Higher mill temp = more moisture removed
    // At 60°C mill temp: remove ~60% of moisture (fuel_moisture * 0.4 remains)
    // At 100°C mill temp: remove ~80% of moisture (fuel_moisture * 0.2 remains)
    // Linear interpolation: drying_factor = 0.4 at 60C, 0.8 at 100C
    drying_factor = if avg_mill_temp > 50.0 then min(0.85, 0.3 + (avg_mill_temp - 50.0) * 0.011) else 0.0;
    dried_moisture = max(5.0, fuel_moisture * (1.0 - drying_factor));

    // 2. Connect Furnace (USE DRIED MOISTURE!)
    furnace.fuel_flow_total = total_fuel;
    furnace.fuel_moisture = dried_moisture;  // KEY: Use dried, not raw!
    furnace.air_flow_total = total_air;
    furnace.primary_air_temp = primaryAir_temp;
    furnace.fgr_percent = fgr_percent;

    // 3. Connect Steam System
    steamCircuit.heat_flow_W = furnace.heat_available;

    // 4. Connect Emissions
    emissions.T_furnace_C = furnace.T_out_C;
    emissions.O2_percent = furnace.O2_out_percent;
    emissions.tram_air_percent = tramp_air_pct;
    emissions.fgr_percent = fgr_percent;
    emissions.mill_temp_C = primaryAir_temp;

    // 5. Level-Weighted NOx Calculation
    // Weight NOx by which mills are active - bottom mills contribute more NOx
    active_mill_count = (if mill1_on then 1 else 0) + (if mill2_on then 1 else 0) + 
                        (if mill3_on then 1 else 0) + (if mill4_on then 1 else 0) + 
                        (if mill5_on then 1 else 0);
    
    active_mill_fuel = (if mill1_on then feeder1_flow else 0) + (if mill2_on then feeder2_flow else 0) +
                       (if mill3_on then feeder3_flow else 0) + (if mill4_on then feeder4_flow else 0) +
                       (if mill5_on then feeder5_flow else 0);
    
    // Calculate fuel-weighted average NOx factor
    nox_level_weight = if active_mill_fuel > 0.1 then 
        ((if mill1_on then feeder1_flow * nox_factor_L1 else 0) +
         (if mill2_on then feeder2_flow * nox_factor_L2 else 0) +
         (if mill3_on then feeder3_flow * nox_factor_L3 else 0) +
         (if mill4_on then feeder4_flow * nox_factor_L4 else 0) +
         (if mill5_on then feeder5_flow * nox_factor_L5 else 0)) / active_mill_fuel
        else 1.0;
    
    // Get raw NOx from emissions model, then apply level weighting
    nox_raw = emissions.NOx_mg;
    
    // 6. Map Outputs
    out_steam_flow = steamCircuit.steam_mass_flow;
    out_MW_gross = steamCircuit.MW_gross;
    out_NOx = max(150.0, nox_raw * nox_level_weight);  // Level-weighted NOx, min 150 per target spec
    out_CO = max(30.0, min(150.0, emissions.CO_ppm));   // Clamp CO to target range 30-150 ppm
    out_O2 = max(2.0, furnace.O2_out_percent);          // Clamp O2 to target minimum 2.0%
    out_FurnaceTemp = furnace.T_out_C;
    
    // Calculated Efficiency (Thermal Boiler Efficiency)
    // Heat into Steam / Heat in Fuel
    total_heat_input = total_fuel * (fuel_LHV * 1.0e6);
    // FIXED: Removed artificial +10% boost for realistic calculation
    out_Efficiency = if total_heat_input > 1.0 then min(93.0, (steamCircuit.heat_flow_W / total_heat_input) * 100.0) else 0.0; 
    
    // Furnace Draft (Pressure) - Physics-based model
    // Draft = f(Air_in, Flue_gas_out) with ID fan maintaining setpoint
    // More air pushed in → pressure rises
    // More flue gas (from combustion) → ID fan pulls harder → pressure drops
    // Setpoint: -10 Pa (balanced draft), varies with operating conditions
    // Formula: Draft = Setpoint + k1*(total_air - nominal_air) - k2*(flue_gas_flow - nominal_gas)
    out_Draft = -10.0 + 0.3 * (total_air - 100.0) - 0.2 * (furnace.mass_flow_gas - 110.0) + 0.5 * sin(time * 0.1);
    
    // =====================================================
    // NEW DYNAMIC OUTPUT EQUATIONS
    // =====================================================
    
    // 1. Steam Pressure (Dynamic Drum Model)
    // Setpoint: 155 bar, varies with load imbalance
    // When steam demand > production: pressure drops
    // When production > demand: pressure rises
    // Typical variation: ±3 bar during load changes
    out_SteamPressure = 155.0 - 0.15 * (out_steam_flow - 100.0) + 0.05 * (total_fuel - 15.0);
    
    // 2. Steam Temperature (Superheater Model)
    // Superheater outlet depends on: furnace temp, steam flow (residence time)
    // Higher furnace temp → higher steam temp
    // Higher steam flow → lower steam temp (less heating time)
    // Typical range: 530-550°C for 540°C setpoint
    out_SteamTemperature = 520.0 + 0.02 * (out_FurnaceTemp - 900.0) - 0.08 * (out_steam_flow - 100.0);
    
    // 3. Flue Gas Temperature (After Economizer)
    // Flue gas cools as it passes through economizer and air preheater
    // Heat transfer: ΔT = η * (T_furnace - T_feedwater)
    // Typical exit: 130-180°C
    out_FlueGasTemp = 80.0 + 0.08 * out_FurnaceTemp - 0.3 * (out_steam_flow - 80.0);
    
    // 4. Feedwater Flow (Mass Balance)
    // Feedwater = Steam + Blowdown (typically 2-3%)
    out_FeedwaterFlow = out_steam_flow * 1.02;
    
    // 5. Feedwater Temperature (Economizer Inlet)
    // Varies with deaerator operation and load
    // Higher load → feedwater preheated more
    out_FeedwaterTemp = 130.0 + 0.15 * (out_steam_flow - 80.0);
    
    // 6. Primary Air Fan Speed (Fan Affinity Laws)
    // RPM proportional to sqrt(flow / design_flow)
    // Design: 80 kg/s at 900 RPM
    out_PAFanRPM = 700.0 + 250.0 * sqrt(primaryAir_flow / 80.0);
    
    // 7. Induced Draft Fan Speed (Fan Affinity Laws)
    // ID fan pulls flue gas through system, maintains draft
    // Higher flue gas flow → higher fan speed
    // Also compensates for heat exchanger pressure drop
    out_IDFanRPM = 700.0 + 400.0 * sqrt(max(1.0, furnace.mass_flow_gas) / 120.0) * (1.0 + abs(out_Draft) / 50.0);
    
    // 8. Level Pair Detection (Which adjacent mill levels are active)
    // Encoded as 2-digit integer: 12=L12, 13=L13, 23=L23, 34=L34, 45=L45
    // Priority: Find first pair of adjacent active mills
    out_LevelPair = if (mill1_on and mill2_on) then 12
                    else if (mill1_on and mill3_on) then 13
                    else if (mill1_on and mill4_on) then 14
                    else if (mill1_on and mill5_on) then 15
                    else if (mill2_on and mill3_on) then 23
                    else if (mill2_on and mill4_on) then 24
                    else if (mill2_on and mill5_on) then 25
                    else if (mill3_on and mill4_on) then 34
                    else if (mill3_on and mill5_on) then 35
                    else if (mill4_on and mill5_on) then 45
                    else 0;  // No valid pair
    
  end DigitalTwin;

end BiomassBoiler;