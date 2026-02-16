within ThermofluidStream_v2.HeatExchangers.Tests;
model RegenerativeHEX "HVAC Heat Recovery Wheel Example"

  replaceable package MediumA = Media.myMedia.Air.DryAirNasa
    constrainedby Media.myMedia.Interfaces.PartialMedium annotation(choicesAllMatching = true);

  replaceable package MediumB = Media.myMedia.Air.DryAirNasa
    constrainedby Media.myMedia.Interfaces.PartialMedium annotation(choicesAllMatching = true);

  extends Modelica.Icons.Example;

  // --- Exhaust Side (Side A - Hot Indoor Air) ---
  ThermofluidStream_v2.Boundaries.Source sourceA(
    redeclare package Medium = MediumA,
    T0_par=308.15,  // 35°C exhaust air
    p0_par=101325)
    annotation (Placement(transformation(
        extent={{10,-10},{-10,10}},
        rotation=180,
        origin={-126,-20})));

  ThermofluidStream_v2.Boundaries.Sink sinkA(
    redeclare package Medium = MediumA, 
    p0_par=100000)
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

  // --- Supply Side (Side B - Cold Outdoor Air) ---
  ThermofluidStream_v2.Boundaries.Source sourceB(
    redeclare package Medium = MediumB,
    temperatureFromInput=false,
    T0_par=278.15,  // 5°C outdoor air
    p0_par=101325)
    annotation (Placement(transformation(extent={{136,10},{116,30}})));
    
  ThermofluidStream_v2.Boundaries.Sink sinkB(
    redeclare package Medium = MediumB, 
    p0_par=100000)
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

  // The Regenerative Heat Exchanger (Heat Wheel)
  // Typical HVAC energy recovery wheel: 
  //   Area = 20 m2 (packed honeycomb matrix)
  //   k_NTU = 30 W/(m2K) (effective heat transfer coefficient)
  ThermofluidStream_v2.HeatExchangers.RegenerativeHEX regenerativeHEX(
    redeclare package MediumA = MediumA,
    redeclare package MediumB = MediumB,
    A=20,
    k_NTU=30,
    useFiniteMatrixCapacity=false) 
    annotation (Placement(transformation(extent={{-10,-8},{10,12}})));

  // Flow Resistances (Pressure drops through the wheel)
  Processes.FlowResistance flowResistanceB(
    redeclare package Medium = MediumB,
    initM_flow=ThermofluidStream_v2.Utilities.Types.InitializationMethods.state,
    r=0.15,
    l=0.3,
    redeclare function pLoss = Processes.Internal.FlowResistance.laminarTurbulentPressureLoss (
      material=ThermofluidStream_v2.Processes.Internal.Material.steel))
    annotation (Placement(transformation(extent={{102,10},{82,30}})));
    
  Processes.FlowResistance flowResistanceA(
    redeclare package Medium = MediumA,
    initM_flow=ThermofluidStream_v2.Utilities.Types.InitializationMethods.state,
    r=0.15,
    l=0.3,
    redeclare function pLoss = Processes.Internal.FlowResistance.laminarTurbulentPressureLoss (
      material=ThermofluidStream_v2.Processes.Internal.Material.steel))
    annotation (Placement(transformation(extent={{-100,-30},{-80,-10}})));

  // Mass Flow Controllers (Balanced flow typical for heat wheels)
  FlowControl.MCV mCV_B(
    redeclare package Medium = MediumB,
    m_flow_0=0,
    massFlow_set_par=0.5)  // 0.5 kg/s supply air
    annotation (Placement(transformation(extent={{-40,10},{-60,30}})));
    
  FlowControl.MCV mCV_A(
    redeclare package Medium = MediumA,
    m_flow_0=0.5,
    massFlow_set_par=0.5)  // 0.5 kg/s exhaust air (balanced)
    annotation (Placement(transformation(
        extent={{10,-10},{-10,10}},
        rotation=180,
        origin={90,-20})));

equation
  // Connections Side B (Cold Supply Air)
  connect(sinkB.inlet, multiSensor_Tpm_B_Out.outlet) annotation (Line(
      points={{-116,20},{-100,20}},
      color={28,108,200},
      thickness=0.5));
  connect(multiSensor_Tpm_B_In.outlet, regenerativeHEX.inletB) annotation (Line(
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
  connect(regenerativeHEX.outletB, mCV_B.inlet) annotation (Line(
      points={{-10,8},{-20,8},{-20,20},{-40,20}},
      color={28,108,200},
      thickness=0.5));
  connect(mCV_B.outlet, multiSensor_Tpm_B_Out.inlet) annotation (Line(
      points={{-60,20},{-80,20}},
      color={28,108,200},
      thickness=0.5));

  // Connections Side A (Hot Exhaust Air)
  connect(multiSensor_Tpm_A_In.outlet, regenerativeHEX.inletA) annotation (Line(
      points={{-40,-20},{-20,-20},{-20,-4},{-10,-4}},
      color={28,108,200},
      thickness=0.5));
  connect(regenerativeHEX.outletA, multiSensor_Tpm_A_Out.inlet) annotation (Line(
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
        <p>This example demonstrates a <b>Regenerative Heat Exchanger (Heat Wheel)</b> 
        for HVAC heat recovery applications.</p>
        <p><b>Configuration:</b></p>
        <ul>
        <li><b>Side A (Exhaust):</b> Hot indoor air at 35°C</li>
        <li><b>Side B (Supply):</b> Cold outdoor air at 5°C</li>
        <li><b>Flow:</b> Balanced at 0.5 kg/s each side</li>
        <li><b>Expected Effectiveness:</b> ~75-85%</li>
        <li><b>Expected Supply Outlet:</b> ~26-28°C (heated by wheel)</li>
        </ul>
        <p><b>Verification:</b></p>
        <p>Plot <code>regenerativeHEX.effectiveness</code> and outlet temperatures to verify
        the heat recovery performance.</p>
</html>"));
end RegenerativeHEX;
