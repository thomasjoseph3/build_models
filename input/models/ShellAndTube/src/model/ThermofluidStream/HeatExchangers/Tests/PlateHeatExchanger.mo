within ThermofluidStream.HeatExchangers.Tests;
model PlateHeatExchanger "Example of a Plate Heat Exchanger (PHE) using CounterFlowNTU"

  // PHEs are typically used for liquid-liquid heat transfer. 
  // We use StandardWater for both sides to simulate a realistic scenario.
  replaceable package MediumA = Modelica.Media.Water.StandardWater
    constrainedby Modelica.Media.Interfaces.PartialMedium annotation(choicesAllMatching = true);

  replaceable package MediumB = Modelica.Media.Water.StandardWater
    constrainedby Modelica.Media.Interfaces.PartialMedium annotation(choicesAllMatching = true);

  extends Modelica.Icons.Example;

  // --- Hot Side (Side A) ---
  ThermofluidStream.Boundaries.Source sourceA(
    redeclare package Medium = MediumA,
    T0_par=353.15, // 80 degC
    p0_par=300000)
    annotation (Placement(transformation(
        extent={{10,-10},{-10,10}},
        rotation=180,
        origin={-126,-20})));

  ThermofluidStream.Boundaries.Sink sinkA(
    redeclare package Medium = MediumA, 
    p0_par=280000)
    annotation (Placement(transformation(extent={{116,-30},{136,-10}})));

  ThermofluidStream.Sensors.MultiSensor_Tpm multiSensor_Tpm_A_In(
    redeclare package Medium = MediumA,
    temperatureUnit="degC",
    pressureUnit="bar") 
    annotation (Placement(transformation(
        extent={{-11,-10},{11,10}},
        rotation=0,
        origin={-51,-10})));
        
  ThermofluidStream.Sensors.MultiSensor_Tpm multiSensor_Tpm_A_Out(
    redeclare package Medium = MediumA,
    digits=3,
    temperatureUnit="degC") 
    annotation (Placement(transformation(
        extent={{10,10},{-10,-10}},
        rotation=180,
        origin={50,-10})));

  // --- Cold Side (Side B) ---
  ThermofluidStream.Boundaries.Source sourceB(
    redeclare package Medium = MediumB,
    temperatureFromInput=false,
    T0_par=293.15, // 20 degC
    p0_par=400000)
    annotation (Placement(transformation(extent={{136,10},{116,30}})));
    
  ThermofluidStream.Boundaries.Sink sinkB(
    redeclare package Medium = MediumB, 
    p0_par=380000)
    annotation (Placement(transformation(extent={{-116,10},{-136,30}})));
    
  ThermofluidStream.Sensors.MultiSensor_Tpm multiSensor_Tpm_B_Out(
    redeclare package Medium = MediumB,
    temperatureUnit="degC")
    annotation (Placement(transformation(extent={{-80,20},{-100,40}})));
    
  ThermofluidStream.Sensors.MultiSensor_Tpm multiSensor_Tpm_B_In(
    redeclare package Medium = MediumB, 
    outputMassFlowRate=false,
    temperatureUnit="degC")
    annotation (Placement(transformation(extent={{60,20},{40,40}})));

  // --- System Components ---
  inner DropOfCommons dropOfCommons(displayInstanceNames=false, displayParameters=false)
    annotation (Placement(transformation(extent={{-158,-98},{-138,-78}})));

  // The Plate Heat Exchanger Model
  // A standard PHE is a Counter-Flow Heat Exchanger.
  // We simulate a compact unit: Area = 2 m2, U-value (k_NTU) = 3000 W/(m2K)
  ThermofluidStream.HeatExchangers.CounterFlowNTU plateHeatExchanger(
    redeclare package MediumA = MediumA,
    redeclare package MediumB = MediumB,
    A=2,
    k_NTU=3000) 
    annotation (Placement(transformation(extent={{-10,-8},{10,12}})));

  // Flow Resistances (Pressure drops typical for plates)
  Processes.FlowResistance flowResistanceB(
    redeclare package Medium = MediumB,
    initM_flow=ThermofluidStream.Utilities.Types.InitializationMethods.state,
    r=0.05,
    l=1,
    redeclare function pLoss = Processes.Internal.FlowResistance.laminarTurbulentPressureLoss (
      material=ThermofluidStream.Processes.Internal.Material.steel))
    annotation (Placement(transformation(extent={{102,10},{82,30}})));
    
  Processes.FlowResistance flowResistanceA(
    redeclare package Medium = MediumA,
    initM_flow=ThermofluidStream.Utilities.Types.InitializationMethods.state,
    r=0.05,
    l=1,
    redeclare function pLoss = Processes.Internal.FlowResistance.laminarTurbulentPressureLoss (
      material=ThermofluidStream.Processes.Internal.Material.steel))
    annotation (Placement(transformation(extent={{-100,-30},{-80,-10}})));

  // Mass Flow Controllers
  FlowControl.MCV mCV_B(
    redeclare package Medium = MediumB,
    m_flow_0=0,
    massFlow_set_par=1.5) // 1.5 kg/s Cold Water
    annotation (Placement(transformation(extent={{-40,10},{-60,30}})));
    
  FlowControl.MCV mCV_A(
    redeclare package Medium = MediumA,
    m_flow_0=1,
    massFlow_set_par=1.0) // 1.0 kg/s Hot Water
    annotation (Placement(transformation(
        extent={{10,-10},{-10,10}},
        rotation=180,
        origin={90,-20})));

equation
  // Connections Side B (Cold)
  connect(sinkB.inlet, multiSensor_Tpm_B_Out.outlet) annotation (Line(
      points={{-116,20},{-100,20}},
      color={28,108,200},
      thickness=0.5));
  connect(multiSensor_Tpm_B_In.outlet, plateHeatExchanger.inletB) annotation (Line(
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
  connect(plateHeatExchanger.outletB, mCV_B.inlet) annotation (Line(
      points={{-10,8},{-20,8},{-20,20},{-40,20}},
      color={28,108,200},
      thickness=0.5));
  connect(mCV_B.outlet, multiSensor_Tpm_B_Out.inlet) annotation (Line(
      points={{-60,20},{-80,20}},
      color={28,108,200},
      thickness=0.5));

  // Connections Side A (Hot)
  connect(multiSensor_Tpm_A_In.outlet, plateHeatExchanger.inletA) annotation (Line(
      points={{-40,-20},{-20,-20},{-20,-4},{-10,-4}},
      color={28,108,200},
      thickness=0.5));
  connect(plateHeatExchanger.outletA, multiSensor_Tpm_A_Out.inlet) annotation (Line(
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
    Diagram(coordinateSystem(preserveAspectRatio=false, extent={{-160,-100},{160,100}})),
    experiment(
      StopTime=100,
      Tolerance=1e-6,
      Interval=0.1,
      __Dymola_Algorithm="Dassl"),
    Documentation(info="<html>
        <p>This example demonstrates how to model a <b>Plate Heat Exchanger (PHE)</b>.</p>
        <p>A Plate Heat Exchanger is physically a counter-flow device. Therefore, the 
        standard <code>CounterFlowNTU</code> model is used.</p>
        <p><b>Configuration:</b></p>
        <ul>
        <li><b>Media:</b> Water (Hot) vs Water (Cold)</li>
        <li><b>Flow:</b> Counter-current</li>
        <li><b>Parameters:</b> High k_NTU (U-value) typical of plate packs (~3000 W/m2K).</li>
        </ul>
</html>"));
end PlateHeatExchanger;
