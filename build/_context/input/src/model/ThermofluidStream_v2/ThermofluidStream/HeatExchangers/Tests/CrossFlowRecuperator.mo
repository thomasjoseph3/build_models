within ThermofluidStream_v2.HeatExchangers.Tests;
model CrossFlowRecuperator "Gas-Gas Cross Flow Recuperator Example"

  // Standard recuperators use Gas (Air) on both sides.
  replaceable package MediumA = Media.myMedia.Air.MoistAir
    constrainedby Media.myMedia.Interfaces.PartialMedium annotation(choicesAllMatching = true);

  replaceable package MediumB = Media.myMedia.Air.DryAirNasa
    constrainedby Media.myMedia.Interfaces.PartialMedium annotation(choicesAllMatching = true);

  extends Modelica.Icons.Example;

  // --- Hot Gas Side (Side A - e.g. Exhaust) ---
  ThermofluidStream_v2.Boundaries.Source sourceA(
    redeclare package Medium = MediumA,
    T0_par=573.15, // 300 degC (Hot Exhaust)
    p0_par=105000)
    annotation (Placement(transformation(
        extent={{10,-10},{-10,10}},
        rotation=180,
        origin={-126,0})));

  ThermofluidStream_v2.Boundaries.Sink sinkA(
    redeclare package Medium = MediumA, 
    p0_par=100000)
    annotation (Placement(transformation(extent={{116,-10},{136,10}})));

  ThermofluidStream_v2.Sensors.MultiSensor_Tpm multiSensor_Tpm_A_In(
    redeclare package Medium = MediumA,
    temperatureUnit="degC",
    pressureUnit="bar") annotation (
      Placement(transformation(
        extent={{-11,-10},{11,10}},
        rotation=0,
        origin={-41,10})));
        
  ThermofluidStream_v2.Sensors.MultiSensor_Tpm multiSensor_Tpm_A_Out(
    redeclare package Medium = MediumA,
    digits=3,
    temperatureUnit="degC") annotation (Placement(transformation(
        extent={{10,10},{-10,-10}},
        rotation=180,
        origin={40,10})));

  // --- Cold Gas Side (Side B - e.g. Intake Air) ---
  ThermofluidStream_v2.Boundaries.Source sourceB(
    redeclare package Medium = MediumB,
    temperatureFromInput=false,
    T0_par=293.15, // 20 degC (Ambient)
    p0_par=105000)
    annotation (Placement(transformation(extent={{10,-10},{-10,10}},
        rotation=90,
        origin={0,94})));

  ThermofluidStream_v2.Boundaries.Sink sinkB(
    redeclare package Medium = MediumB, 
    p0_par=100000)
    annotation (Placement(transformation(extent={{10,-10},{-10,10}},
        rotation=90,
        origin={0,-84})));
        
  ThermofluidStream_v2.Sensors.MultiSensor_Tpm multiSensor_Tpm_B_Out(
    redeclare package Medium = MediumB,
    temperatureUnit="degC")
    annotation (Placement(transformation(extent={{10,-10},{-10,10}},
        rotation=90,
        origin={-10,-24})));
        
  ThermofluidStream_v2.Sensors.MultiSensor_Tpm multiSensor_Tpm_B_In(
    redeclare package Medium = MediumB, 
    outputMassFlowRate=false,
    temperatureUnit="degC")
    annotation (Placement(transformation(extent={{10,-10},{-10,10}},
        rotation=90,
        origin={-10,32})));

  // --- System ---
  inner DropOfCommons dropOfCommons(displayInstanceNames=false)
    annotation (Placement(transformation(extent={{-156,-98},{-136,-78}})));

  // The Heat Exchanger
  // Gas-Gas heat transfer is poor. 
  // Typical U-value ~ 20-100 W/m2K.
  // We use CrossFlowNTU (unmixed-unmixed is standard for plate-fin recuperators).
  ThermofluidStream_v2.HeatExchangers.CrossFlowNTU crossFlowNTU(
    redeclare package MediumA = MediumA,
    redeclare package MediumB = MediumB,
    A=5,
    k_NTU=50) 
    annotation (Placement(transformation(extent={{-10,-10},{10,10}})));

  // Resistances
  Processes.FlowResistance flowResistanceA(
    redeclare package Medium = MediumA,
    initM_flow=ThermofluidStream_v2.Utilities.Types.InitializationMethods.state,
    r=0.05,
    l=1,
    redeclare function pLoss = Processes.Internal.FlowResistance.laminarTurbulentPressureLoss (
      material=ThermofluidStream_v2.Processes.Internal.Material.steel))
    annotation (Placement(transformation(extent={{-92,-10},{-72,10}})));
    
  Processes.FlowResistance flowResistanceB(
    redeclare package Medium = MediumB,
    initM_flow=ThermofluidStream_v2.Utilities.Types.InitializationMethods.state,
    r=0.05,
    l=1,
    redeclare function pLoss = Processes.Internal.FlowResistance.laminarTurbulentPressureLoss (
      material=ThermofluidStream_v2.Processes.Internal.Material.steel))
    annotation (Placement(transformation(
        extent={{10,-10},{-10,10}},
        rotation=90,
        origin={0,64})));

  // Mass Flow Controllers
  FlowControl.MCV mCV_B(
    redeclare package Medium = MediumB,
    m_flow_0=0,
    massFlow_set_par=0.5) 
    annotation (Placement(transformation(
        extent={{10,-10},{-10,10}},
        rotation=90,
        origin={0,-54})));
        
  FlowControl.MCV mCV_A(
    redeclare package Medium = MediumA,
    m_flow_0=1,
    massFlow_set_par=0.5) 
    annotation (Placement(transformation(
        extent={{10,-10},{-10,10}},
        rotation=180,
        origin={82,0})));

equation
  // Side B (Cold Air)
  connect(multiSensor_Tpm_B_In.outlet, crossFlowNTU.inletB) annotation (Line(
      points={{0,22},{0,10},{0,10}},
      color={28,108,200},
      thickness=0.5));
  connect(crossFlowNTU.outletB, multiSensor_Tpm_B_Out.inlet) annotation (Line(
      points={{0,-10},{0,-12},{0,-12},{0,-14}},
      color={28,108,200},
      thickness=0.5));
  connect(sourceB.outlet, flowResistanceB.inlet) annotation (Line(
      points={{0,84},{0,84},{0,74},{0,74}},
      color={28,108,200},
      thickness=0.5));
  connect(multiSensor_Tpm_B_In.inlet, flowResistanceB.outlet) annotation (Line(
      points={{0,42},{0,54},{0,54}},
      color={28,108,200},
      thickness=0.5));
  connect(sinkB.inlet, mCV_B.outlet)
    annotation (Line(
      points={{0,-74},{0,-69},{0,-69},{0,-64}},
      color={28,108,200},
      thickness=0.5));
  connect(mCV_B.inlet, multiSensor_Tpm_B_Out.outlet)
    annotation (Line(
      points={{0,-44},{0,-39},{0,-39},{0,-34}},
      color={28,108,200},
      thickness=0.5));

  // Side A (Hot Exhaust)
  connect(multiSensor_Tpm_A_In.outlet, crossFlowNTU.inletA) annotation (Line(
      points={{-30,0},{-10,0}},
      color={28,108,200},
      thickness=0.5));
  connect(crossFlowNTU.outletA, multiSensor_Tpm_A_Out.inlet) annotation (Line(
      points={{10,0},{15,0},{15,0},{30,0}},
      color={28,108,200},
      thickness=0.5));
  connect(sourceA.outlet, flowResistanceA.inlet) annotation (Line(
      points={{-116,0},{-104,0},{-104,0},{-92,0}},
      color={28,108,200},
      thickness=0.5));
  connect(multiSensor_Tpm_A_In.inlet, flowResistanceA.outlet) annotation (Line(
      points={{-52,0},{-72,0}},
      color={28,108,200},
      thickness=0.5));
  connect(multiSensor_Tpm_A_Out.outlet, mCV_A.inlet)
    annotation (Line(
      points={{50,0},{61,0},{61,0},{72,0}},
      color={28,108,200},
      thickness=0.5));
  connect(mCV_A.outlet, sinkA.inlet) annotation (Line(
      points={{92,0},{116,0}},
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
        <p><b>Cross Flow Recuperator Example</b></p>
        <p>This model simulates a Gas-to-Gas recuperator, typical of microturbines or exhaust heat recovery systems.</p>
        <p><b>Physics:</b></p>
        <ul>
        <li><b>Hot Side:</b> Moist Air at 300&deg;C (Simulating exhaust)</li>
        <li><b>Cold Side:</b> Dry Air at 20&deg;C (Simulating intake)</li>
        <li><b>Model:</b> CrossFlowNTU (Unmixed-Unmixed).</li>
        <li><b>Heat Transfer:</b> Low k_NTU (50 W/m&sup2;K) reflects gas-gas conditions.</li>
        </ul>
</html>"));
end CrossFlowRecuperator;
