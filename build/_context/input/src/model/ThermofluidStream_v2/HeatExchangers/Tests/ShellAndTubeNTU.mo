within ThermofluidStream_v2.HeatExchangers.Tests;
model ShellAndTubeNTU "Shell and Tube Heat Exchanger - Glycol Cooler (FMU-Ready)"

  // Glycol cooler: Hot glycol (tube side) cooled by water (shell side)
  // This is a typical configuration for process cooling, HVAC, and industrial systems.
  
  replaceable package MediumA = Media.myMedia.Incompressible.Examples.Glycol47
    constrainedby Media.myMedia.Interfaces.PartialMedium 
    annotation(choicesAllMatching = true);

  replaceable package MediumB = Modelica.Media.Water.StandardWater
    constrainedby Modelica.Media.Interfaces.PartialMedium 
    annotation(choicesAllMatching = true);

  extends Modelica.Icons.Example;

  // =====================================================================
  // FMU INPUTS - Controllable at runtime via fmpy
  // =====================================================================
  parameter Real k_factor(min=0, max=1) = 1.0 "Fouling Factor (1.0 = Clean, 0.5 = 50% Fouled) [1]";


  Modelica.Blocks.Interfaces.RealInput T_glycol_in(start=80, unit="degC") "Glycol inlet temperature [degC]"
    annotation (Placement(transformation(extent={{-200,-40},{-160,0}})));
  Modelica.Blocks.Interfaces.RealInput T_water_in(start=20, unit="degC") "Water inlet temperature [degC]"
    annotation (Placement(transformation(extent={{180,40},{140,80}})));
  Modelica.Blocks.Interfaces.RealInput m_flow_glycol(start=1.0, unit="kg/s") "Glycol mass flow rate [kg/s]"
    annotation (Placement(transformation(extent={{140,-80},{100,-40}})));
  Modelica.Blocks.Interfaces.RealInput m_flow_water(start=2.0, unit="kg/s") "Water mass flow rate [kg/s]"
    annotation (Placement(transformation(extent={{-200,40},{-160,80}})));

  // =====================================================================
  // FMU OUTPUTS - Readable at runtime via fmpy
  // =====================================================================
  Modelica.Blocks.Interfaces.RealOutput T_glycol_out(unit="degC") "Glycol outlet temperature [degC]"
    annotation (Placement(transformation(extent={{150,-30},{170,-10}})));
  Modelica.Blocks.Interfaces.RealOutput T_water_out(unit="degC") "Water outlet temperature [degC]"
    annotation (Placement(transformation(extent={{-150,10},{-170,30}})));
  Modelica.Blocks.Interfaces.RealOutput Q_flow(unit="W") "Heat transfer rate [W]"
    annotation (Placement(transformation(extent={{-10,90},{10,110}})));
  Modelica.Blocks.Interfaces.RealOutput effectiveness(unit="1") "HEX effectiveness [-]"
    annotation (Placement(transformation(extent={{30,90},{50,110}})));
  Modelica.Blocks.Interfaces.RealOutput NTU_value(unit="1") "Number of transfer units [-]"
    annotation (Placement(transformation(extent={{-50,90},{-30,110}})));

  // --- Tube Side (Side A - Hot Glycol) ---
  ThermofluidStream_v2.Boundaries.Source sourceA(
    redeclare package Medium = MediumA,
    temperatureFromInput=true,
    T0_par=353.15,  // 80°C hot glycol (default/fallback)
    p0_par=300000)
    annotation (Placement(transformation(
        extent={{10,-10},{-10,10}},
        rotation=180,
        origin={-126,-20})));

  ThermofluidStream_v2.Boundaries.Sink sinkA(
    redeclare package Medium = MediumA, 
    p0_par=280000)
    annotation (Placement(transformation(extent={{116,-30},{136,-10}})));

  ThermofluidStream_v2.Sensors.MultiSensor_Tpm multiSensor_Tpm_A_In(
    redeclare package Medium = MediumA,
    temperatureUnit="degC",
    pressureUnit="bar") 
    annotation (Placement(transformation(
        extent={{-11,-10},{11,10}},
        rotation=0,
        origin={-51,-10})));
        
  ThermofluidStream_v2.Sensors.MultiSensor_Tpm multiSensor_Tpm_A_Out(
    redeclare package Medium = MediumA,
    digits=3,
    temperatureUnit="degC") 
    annotation (Placement(transformation(
        extent={{10,10},{-10,-10}},
        rotation=180,
        origin={50,-10})));

  // --- Shell Side (Side B - Cooling Water) ---
  ThermofluidStream_v2.Boundaries.Source sourceB(
    redeclare package Medium = MediumB,
    temperatureFromInput=true,
    T0_par=293.15,  // 20°C cooling water (default/fallback)
    p0_par=400000)
    annotation (Placement(transformation(extent={{136,10},{116,30}})));
    
  ThermofluidStream_v2.Boundaries.Sink sinkB(
    redeclare package Medium = MediumB, 
    p0_par=350000)
    annotation (Placement(transformation(extent={{-116,10},{-136,30}})));
    
  ThermofluidStream_v2.Sensors.MultiSensor_Tpm multiSensor_Tpm_B_Out(
    redeclare package Medium = MediumB,
    temperatureUnit="degC")
    annotation (Placement(transformation(extent={{-80,20},{-100,40}})));
    
  ThermofluidStream_v2.Sensors.MultiSensor_Tpm multiSensor_Tpm_B_In(
    redeclare package Medium = MediumB, 
    outputMassFlowRate=false,
    temperatureUnit="degC")
    annotation (Placement(transformation(extent={{60,20},{40,40}})));

  // --- System Components ---
  inner DropOfCommons dropOfCommons(displayInstanceNames=false, displayParameters=false)
    annotation (Placement(transformation(extent={{-158,-98},{-138,-78}})));

  // Shell and Tube Heat Exchanger (1 shell pass, 2n tube passes)
  // Glycol cooler parameters:
  //   Area = 5 m² (compact industrial unit)
  //   k_NTU = 500 * k_factor (Simulates fouling by reducing U-value)
  ThermofluidStream_v2.HeatExchangers.ShellAndTubeNTU shellAndTubeHEX(
    redeclare package MediumA = MediumA,
    redeclare package MediumB = MediumB,
    A=5,
    k_NTU=500 * k_factor) 
    annotation (Placement(transformation(extent={{-10,-8},{10,12}})));

  // Flow Resistances
  Processes.FlowResistance flowResistanceB(
    redeclare package Medium = MediumB,
    initM_flow=ThermofluidStream_v2.Utilities.Types.InitializationMethods.state,
    m_flow_0=2.0,  // match default water flow rate for proper initialization
    r=0.025,
    l=2,
    redeclare function pLoss = Processes.Internal.FlowResistance.laminarTurbulentPressureLoss (
      material=ThermofluidStream_v2.Processes.Internal.Material.steel))
    annotation (Placement(transformation(extent={{102,10},{82,30}})));
    
  Processes.FlowResistance flowResistanceA(
    redeclare package Medium = MediumA,
    initM_flow=ThermofluidStream_v2.Utilities.Types.InitializationMethods.state,
    m_flow_0=1.0,  // match default glycol flow rate for proper initialization
    r=0.015,
    l=3,
    redeclare function pLoss = Processes.Internal.FlowResistance.laminarTurbulentPressureLoss (
      material=ThermofluidStream_v2.Processes.Internal.Material.steel))
    annotation (Placement(transformation(extent={{-100,-30},{-80,-10}})));

  // Mass Flow Controllers (setpoint from FMU input)
  FlowControl.MCV mCV_B(
    redeclare package Medium = MediumB,
    setpointFromInput=true,
    m_flow_0=0,
    massFlow_set_par=2.0)  // 2.0 kg/s cooling water (default/fallback)
    annotation (Placement(transformation(extent={{-40,10},{-60,30}})));
    
  FlowControl.MCV mCV_A(
    redeclare package Medium = MediumA,
    setpointFromInput=true,
    m_flow_0=1,
    massFlow_set_par=1.0)  // 1.0 kg/s hot glycol (default/fallback)
    annotation (Placement(transformation(
        extent={{10,-10},{-10,10}},
        rotation=180,
        origin={90,-20})));

equation
  // =====================================================================
  // FMU Input Connections (with Unit Conversion for Temps)
  // =====================================================================
  // Glycol Temp: Input(degC) -> Equation -> Source(K)
  sourceA.T0_var = T_glycol_in + 273.15;
  
  // Water Temp: Input(degC) -> Equation -> Source(K)
  sourceB.T0_var = T_water_in + 273.15;
  
  // Mass Flows: Direct connection
  connect(m_flow_glycol, mCV_A.setpoint_var);
  connect(m_flow_water, mCV_B.setpoint_var);

  // =====================================================================
  // FMU Output Assignments
  // =====================================================================
  T_glycol_out = multiSensor_Tpm_A_Out.T;
  T_water_out = multiSensor_Tpm_B_Out.T;
  Q_flow = shellAndTubeHEX.q_flow;
  effectiveness = shellAndTubeHEX.effectiveness;
  NTU_value = shellAndTubeHEX.NTU;

  // Connections Side B (Cooling Water - Shell)
  connect(sinkB.inlet, multiSensor_Tpm_B_Out.outlet) annotation (Line(
      points={{-116,20},{-100,20}},
      color={28,108,200},
      thickness=0.5));
  connect(multiSensor_Tpm_B_In.outlet, shellAndTubeHEX.inletB) annotation (Line(
      points={{40,20},{20,20},{20,8},{10,8}},
      color={28,108,200},
      thickness=0.5));
  connect(sourceB.outlet, flowResistanceB.inlet) annotation (Line(
      points={{116,20},{102,20}},
      color={28,108,200},
      thickness=0.5));
  connect(multiSensor_Tpm_B_In.inlet, flowResistanceB.outlet) annotation (Line(
      points={{60,20},{82,20}},
      color={28,108,200},
      thickness=0.5));
  connect(shellAndTubeHEX.outletB, mCV_B.inlet) annotation (Line(
      points={{-10,8},{-20,8},{-20,20},{-40,20}},
      color={28,108,200},
      thickness=0.5));
  connect(mCV_B.outlet, multiSensor_Tpm_B_Out.inlet) annotation (Line(
      points={{-60,20},{-80,20}},
      color={28,108,200},
      thickness=0.5));

  // Connections Side A (Hot Glycol - Tubes)
  connect(multiSensor_Tpm_A_In.outlet, shellAndTubeHEX.inletA) annotation (Line(
      points={{-40,-20},{-20,-20},{-20,-4},{-10,-4}},
      color={28,108,200},
      thickness=0.5));
  connect(shellAndTubeHEX.outletA, multiSensor_Tpm_A_Out.inlet) annotation (Line(
      points={{10,-4},{20,-4},{20,-20},{40,-20}},
      color={28,108,200},
      thickness=0.5));
  connect(sourceA.outlet, flowResistanceA.inlet) annotation (Line(
      points={{-116,-20},{-100,-20}},
      color={28,108,200},
      thickness=0.5));
  connect(multiSensor_Tpm_A_In.inlet, flowResistanceA.outlet) annotation (Line(
      points={{-62,-20},{-80,-20}},
      color={28,108,200},
      thickness=0.5));
  connect(sinkA.inlet, mCV_A.outlet) annotation (Line(
      points={{116,-20},{100,-20}},
      color={28,108,200},
      thickness=0.5));
  connect(mCV_A.inlet, multiSensor_Tpm_A_Out.outlet) annotation (Line(
      points={{80,-20},{60,-20}},
      color={28,108,200},
      thickness=0.5));

  annotation (
    Icon(coordinateSystem(preserveAspectRatio=false)), 
    Diagram(coordinateSystem(preserveAspectRatio=false, extent={{-200,-100},{200,120}})),
    experiment(
      StopTime=100,
      Tolerance=1e-6,
      Interval=0.1,
      __Dymola_Algorithm="Dassl"),
    Documentation(info="<html>
        <p>This example demonstrates a <b>Shell and Tube Heat Exchanger</b> 
        configured as a <b>Glycol Cooler</b>, with FMU-ready inputs and outputs.</p>
        
        <h4>FMU Inputs (controllable at runtime)</h4>
        <ul>
        <li><b>T_glycol_in:</b> Glycol inlet temperature [K] (default: 353.15 K / 80°C)</li>
        <li><b>T_water_in:</b> Water inlet temperature [K] (default: 293.15 K / 20°C)</li>
        <li><b>m_flow_glycol:</b> Glycol mass flow rate [kg/s] (default: 1.0 kg/s)</li>
        <li><b>m_flow_water:</b> Water mass flow rate [kg/s] (default: 2.0 kg/s)</li>
        </ul>

        <h4>FMU Outputs (readable at runtime)</h4>
        <ul>
        <li><b>T_glycol_out:</b> Glycol outlet temperature [degC]</li>
        <li><b>T_water_out:</b> Water outlet temperature [degC]</li>
        <li><b>Q_flow:</b> Heat transfer rate [W]</li>
        <li><b>effectiveness:</b> HEX effectiveness [-]</li>
        <li><b>NTU_value:</b> Number of transfer units [-]</li>
        </ul>
        
        <h4>Configuration</h4>
        <ul>
        <li><b>Tube Side (A):</b> Hot glycol (Glycol47) at 80°C, 1.0 kg/s</li>
        <li><b>Shell Side (B):</b> Cooling water at 20°C, 2.0 kg/s</li>
        <li><b>Heat Transfer Area:</b> 5 m²</li>
        <li><b>U-Value:</b> 500 W/(m²K) - typical for liquid-liquid</li>
        </ul>
        
        <h4>Physics</h4>
        <p>Uses the 1-shell-pass, 2n-tube-pass effectiveness-NTU correlation
        from VDI Wärmeatlas. The effectiveness accounts for the mixed flow 
        pattern inherent in shell-and-tube designs.</p>
        
        <h4>Expected Results (at default inputs)</h4>
        <ul>
        <li>Effectiveness: ~60-70%</li>
        <li>Glycol outlet: ~45-55°C (cooled from 80°C)</li>
        <li>Water outlet: ~30-35°C (heated from 20°C)</li>
        </ul>
</html>"));
end ShellAndTubeNTU;